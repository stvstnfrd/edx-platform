"""
Views related to operations on course objects
"""
import copy
import json
import logging
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import ensure_csrf_cookie
from edxmako.shortcuts import render_to_response
import requests

from opaque_keys import InvalidKeyError
from util.json_request import JsonResponse
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError, InsufficientSpecificationError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.keys import UsageKey
from openedx.stanford.cms.djangoapps.contentstore.views.helpers import get_course_and_check_access
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.exceptions import NotFoundError
from xmodule.video_module.transcripts_utils import (
    get_transcripts_from_youtube,
    GetTranscriptsFromYouTubeException,
    TranscriptsRequestValidationException,
    download_youtube_subs,
    youtube_video_transcript_name,
)
from xmodule.video_module import manage_video_subtitles_save


log = logging.getLogger(__name__)


# pylint: disable=unused-argument
@login_required
def utility_captions_handler(request, course_key_string):
    """
    The restful handler for captions requests in the utilities area.
    It provides the list of course videos as well as their status. It also lets
    the user update the captions by pulling the latest version from YouTube.

    GET
        json: get the status of the captions of a given video
        html: return page containing a list of videos in the course
    POST
        json: update the captions of a given video by copying the version of the captions hosted in youtube.
    """
    course_key = CourseKey.from_string(course_key_string)
    response_format = request.POST.get('format') or request.GET.get('format') or 'html'
    if response_format == 'json' or 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        if request.method == 'POST':  # update
            try:
                locations = _validate_captions_data_update(request, course_key)
            except TranscriptsRequestValidationException as e:
                return error_response(e.message)
            return json_update_videos(request, locations)
        elif request.method == 'GET':  # get status
            try:
                data, item = _validate_captions_data_get(request, course_key)
            except TranscriptsRequestValidationException as e:
                return error_response(e.message)
            return json_get_video_status(data, item)
        else:
            return HttpResponseBadRequest()
    elif request.method == 'GET':  # assume html
        return captions_index(request, course_key)
    else:
        return HttpResponseNotFound()


@login_required
@ensure_csrf_cookie
def json_update_videos(request, locations):
    """
    Updates the captions of a given list of videos and returns the status of the
    videos in json format

    request: the incoming request to update the videos
    locations: list of locations of videos to be updated
    """
    results = []
    for key_string in locations:
        key = UsageKey.from_string(key_string)
        try:
            #update transcripts
            item = modulestore().get_item(key)
            download_youtube_subs(item.youtube_id_1_0, item, settings)

            # Once transcripts downloaded, show subs are present from youtube
            item.sub = item.youtube_id_1_0
            manage_video_subtitles_save(item, request.user)

            #get new status
            videos = {'youtube': item.youtube_id_1_0}
            html5 = {}
            for url in item.html5_sources:
                name = os.path.splitext(url.split('/')[-1])[0]
                html5[name] = 'html5'
            videos['html5'] = html5
            captions_dict = get_transcripts_presence(videos, item)
            captions_dict.update({'location': key_string})
            results.append(captions_dict)

        except GetTranscriptsFromYouTubeException as e:
            log.debug(e)
            results.append({'location': key_string, 'command': e})

    return JsonResponse(results)


@login_required
@ensure_csrf_cookie
def captions_index(request, course_key):
    """
    Display a list of course videos as well as their status (up to date, or out of date)

    org, course, name: Attributes of the Location for the item to edit
    """
    course = get_course_and_check_access(
        course_key,
        request.user,
        depth=2,
    )

    return render_to_response(
        'captions.html',
        {
            'videos': get_videos(course),
            'context_course': course,
        }
    )


def error_response(message, response=None, status_code=400):
    """
    Simplify similar actions: log message and return JsonResponse with message included in response.

    By default return 400 (Bad Request) Response.
    """
    if response is None:
        response = {}
    log.debug(message)
    response['message'] = message
    return JsonResponse(response, status_code)


def _validate_captions_data_get(request, course_key):
    """
    Happens on 'GET'. Validates, that request contains all proper data for transcripts processing.

    Returns touple of two elements:
        data: dict, loaded json from request,
        item: video item from storage

    Raises `TranscriptsRequestValidationException` if validation is unsuccessful
    or `PermissionDenied` if user has no access.
    """
    try:
        data = json.loads(request.GET.get('video', '{}'))
    except ValueError:
        raise TranscriptsRequestValidationException(_("Invalid location."))

    if not data:
        raise TranscriptsRequestValidationException(_('Incoming video data is empty.'))

    location = data.get('location')
    item = _validate_location(location, course_key)
    return data, item


def _validate_captions_data_update(request, course_key):
    """
    Happens on 'POST'. Validates, that request contains all proper data for transcripts processing.

    Returns data: dict, loaded json from request

    Raises `TranscriptsRequestValidationException` if validation is unsuccessful
    or `PermissionDenied` if user has no access.
    """
    try:
        data = json.loads(request.POST.get('update_array', '[]'))
    except ValueError:
        raise TranscriptsRequestValidationException(_("Invalid locations."))

    if not data:
        raise TranscriptsRequestValidationException(_('Incoming update_array data is empty.'))

    for location in data:
        _validate_location(location, course_key)
    return data


def _validate_location(location, course_key):
    try:
        location = UsageKey.from_string(location)
        item = modulestore().get_item(location)
    except (ItemNotFoundError, InvalidKeyError, InsufficientSpecificationError):
        raise TranscriptsRequestValidationException(_("Can't find item by locator."))

    if item.category != 'video':
        raise TranscriptsRequestValidationException(_('Transcripts are supported only for "video" modules.'))
    return item


def json_get_video_status(video_meta, item):
    """
    Fetches the status of a given video

    Returns: json response which includes a detailed status of the video captions
    """

    videos = {'youtube': item.youtube_id_1_0}
    html5 = {}
    for url in item.html5_sources:
        name = os.path.splitext(url.split('/')[-1])[0]
        html5[name] = 'html5'
    videos['html5'] = html5
    transcripts_presence = get_transcripts_presence(videos, item)
    video_meta.update(transcripts_presence)
    return JsonResponse(video_meta)


def get_videos(course):
    """
    Fetches the list of course videos

    Returns: A list of tuples representing (name, location) of each video
    """
    video_list = []
    for section in course.get_children():
        for subsection in section.get_children():
            for unit in subsection.get_children():
                for component in unit.get_children():
                    if component.location.category == 'video':
                        video_list.append({'name': component.display_name_with_default, 'location': str(component.location)})
    return video_list


def get_transcripts_presence(videos, item):
    """ fills in the transcripts_presence dictionary after for a given component
    with its list of videos.

    Returns transcripts_presence dict:

        html5_local: list of html5 ids, if subtitles exist locally for them;
        is_youtube_mode: bool, if we have youtube_id, and as youtube mode is of higher priority, reflect this with flag;
        youtube_local: bool, if youtube transcripts exist locally;
        youtube_server: bool, if youtube transcripts exist on server;
        youtube_diff: bool, if youtube transcripts exist on youtube server, and are different from local youtube ones;
        current_item_subs: string, value of item.sub field;
        status: string, 'Error' or 'Success';
        subs: string, new value of item.sub field, that should be set in module;
        command: string, action to front-end what to do and what to show to user.
    """
    transcripts_presence = {
        'html5_local': [],
        'html5_equal': False,
        'is_youtube_mode': False,
        'youtube_local': False,
        'youtube_server': False,
        'youtube_diff': True,
        'current_item_subs': None,
        'status': 'Success',
    }

    filename = 'subs_{0}.srt.sjson'.format(item.sub)
    content_location = StaticContent.compute_location(item.location.course_key, filename)
    try:
        local_transcripts = contentstore().find(content_location).data
        transcripts_presence['current_item_subs'] = item.sub
    except NotFoundError:
        pass

    # Check for youtube transcripts presence
    youtube_id = videos.get('youtube', None)
    if youtube_id:
        transcripts_presence['is_youtube_mode'] = True

        # youtube local
        filename = 'subs_{0}.srt.sjson'.format(youtube_id)
        content_location = StaticContent.compute_location(item.location.course_key, filename)
        try:
            local_transcripts = contentstore().find(content_location).data
            transcripts_presence['youtube_local'] = True
        except NotFoundError:
            log.debug("Can't find transcripts in storage for youtube id: %s", youtube_id)

        # youtube server
        youtube_text_api = copy.deepcopy(settings.YOUTUBE['TEXT_API'])
        youtube_text_api['params']['v'] = youtube_id
        youtube_transcript_name = youtube_video_transcript_name(youtube_text_api)
        if youtube_transcript_name:
            youtube_text_api['params']['name'] = youtube_transcript_name
        youtube_response = requests.get('http://' + youtube_text_api['url'], params=youtube_text_api['params'])

        if youtube_response.status_code == 200 and youtube_response.text:
            transcripts_presence['youtube_server'] = True
        #check youtube local and server transcripts for equality
        if transcripts_presence['youtube_server'] and transcripts_presence['youtube_local']:
            try:
                youtube_server_subs = get_transcripts_from_youtube(
                    youtube_id,
                    settings,
                    item.runtime.service(item, "i18n")
                )
                if json.loads(local_transcripts) == youtube_server_subs:  # check transcripts for equality
                    transcripts_presence['youtube_diff'] = False
            except GetTranscriptsFromYouTubeException:
                pass

    # Check for html5 local transcripts presence
    html5_subs = []
    for html5_id in videos['html5']:
        filename = 'subs_{0}.srt.sjson'.format(html5_id)
        content_location = StaticContent.compute_location(item.location.course_key, filename)
        try:
            html5_subs.append(contentstore().find(content_location).data)
            transcripts_presence['html5_local'].append(html5_id)
        except NotFoundError:
            log.debug("Can't find transcripts in storage for non-youtube video_id: %s", html5_id)
        if len(html5_subs) == 2:  # check html5 transcripts for equality
            transcripts_presence['html5_equal'] = json.loads(html5_subs[0]) == json.loads(html5_subs[1])

    command, subs_to_use = _transcripts_logic(transcripts_presence, videos)
    transcripts_presence.update({
        'command': command,
        'subs': subs_to_use,
    })
    return transcripts_presence


def _transcripts_logic(transcripts_presence, videos):
    """
    By `transcripts_presence` content, figure what show to user:

    returns: `command` and `subs`.

    `command`: string,  action to front-end what to do and what show to user.
    `subs`: string, new value of item.sub field, that should be set in module.

    `command` is one of::

        replace: replace local youtube subtitles with server one's
        found: subtitles are found
        import: import subtitles from youtube server
        choose: choose one from two html5 subtitles
        not found: subtitles are not found
    """
    command = None

    # new value of item.sub field, that should be set in module.
    subs = ''

    # youtube transcripts are of high priority than html5 by design
    if (
            transcripts_presence['youtube_diff'] and
            transcripts_presence['youtube_local'] and
            transcripts_presence['youtube_server']):  # youtube server and local exist
        command = 'replace'
        subs = videos['youtube']
    elif transcripts_presence['youtube_local']:  # only youtube local exist
        command = 'found'
        subs = videos['youtube']
    elif transcripts_presence['youtube_server']:  # only youtube server exist
        command = 'import'
    else:  # html5 part
        if transcripts_presence['html5_local']:  # can be 1 or 2 html5 videos
            if len(transcripts_presence['html5_local']) == 1 or transcripts_presence['html5_equal']:
                command = 'found'
                subs = transcripts_presence['html5_local'][0]
            else:
                command = 'choose'
                subs = transcripts_presence['html5_local'][0]
        else:  # html5 source have no subtitles
            # check if item sub has subtitles
            if transcripts_presence['current_item_subs'] and not transcripts_presence['is_youtube_mode']:
                log.debug("Command is use existing %s subs", transcripts_presence['current_item_subs'])
                command = 'use_existing'
            else:
                command = 'not_found'
    log.debug(
        "Resulted command: %s, current transcripts: %s, youtube mode: %s",
        command,
        transcripts_presence['current_item_subs'],
        transcripts_presence['is_youtube_mode']
    )
    return command, subs
