"""
Views related to bulk settings change operations on course problems.
"""

import logging

from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound
from django.views.decorators.http import require_GET

# Imports from common / openedx
from edxmako.shortcuts import render_to_response
from student.auth import has_course_author_access
from util.json_request import JsonResponse
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata

from opaque_keys.edx.keys import CourseKey  # ?
from xblock.fields import Scope  # ?

from contentstore.views.utilities.tasks import BulkUpdateUtil, _do_update

SHOW_ANSWER_OPTIONS = [
    'always',
    'answered',
    'attempted',
    'closed',
    'finished',
    'past_due',
    'correct_or_past_due',
    'never'
]


log = logging.getLogger(__name__)

__all__ = [
    'utility_bulkupdate_handler',
    'utility_bulkupdate_status_handler',
]


def reverse_course_url(handler, course_key_string, kwargs=None):
    """
    Creates the URL for handlers that use course_keys as URL parameters.
    """
    kwargs_for_reverse = {
        'course_key_string': unicode(course_key_string)
    }
    if kwargs:
        kwargs_for_reverse.update(kwargs)
    return reverse('contentstore.views.' + handler, kwargs=kwargs_for_reverse)


def save_request_status(request, key, status):
    """
    Save update status for a course in request session
    """
    session_status = request.session.get('update_status')
    if session_status is None:
        session_status = request.session.setdefault("update_status", {})

    session_status[key] = status
    request.session.save()


def _utility_bulkupdate_get_handler(request, course_key_string, course):
    """
    Internal bulkupdate handler for GET operation
    """
    max_attempts = 0
    show_answer = SHOW_ANSWER_OPTIONS[0]
    update_url = reverse_course_url(
        "utility_bulkupdate_handler",
        course_key_string
    )
    status_url = reverse_course_url(
        "utility_bulkupdate_status_handler",
        course_key_string,
        kwargs={
            'max_attempts': 'fillerMaxAttempts',
            'show_answer': 'fillerShowAnswer'
        }
    )

    return render_to_response(
        'bulkupdate.html',
        {
            'context_course': course,
            'bulkupdate_update_url': update_url,
            'bulkupdate_status_url': status_url,
            'default_max_attempts': max_attempts,
            'default_show_answer': show_answer,
            'show_answer_options': SHOW_ANSWER_OPTIONS
        }
    )


def _utility_bulkupdate_post_handler(request, course_key_string, course):
    """
    Internal bulkupdate handler for POST operation
    """
    try:
        modified_settings = {}
        max_attempts = request.POST.get('maxAttempts')
        show_answer = request.POST.get('showAnswer')
        session_status = request.session.setdefault("update_status", {})
        session_status_string = course_key_string + max_attempts + show_answer
    except:
        return JsonResponse(
            {
                'ErrMsg': 'Missing or invalid arguments',
                'Stage': -1
            },
            status=400
        )

    try:
        save_request_status(request, session_status_string, 1)

        if max_attempts.find('null') == -1:
            try:
                max_attempts = int(max_attempts)
            except:
                save_request_status(request, session_status_string, -1)
                return JsonResponse(
                    {
                        'ErrMsg': 'Invalid settings',
                        'Stage': -1
                    },
                    status=400
                )
            if max_attempts < 0:
                save_request_status(request, session_status_string, -1)
                return JsonResponse(
                    {
                        'ErrMsg': 'Invalid settings',
                        'Stage': -1
                    },
                    status=400
                )
            else:
                modified_settings['max_attempts'] = max_attempts

        if show_answer.find('null') == -1:
            if show_answer not in SHOW_ANSWER_OPTIONS:
                save_request_status(request, session_status_string, -1)
                return JsonResponse(
                    {
                        'ErrMsg': 'Invalid settings',
                        'Stage': -1
                    },
                    status=400
                )
            else:
                modified_settings['showanswer'] = show_answer
        save_request_status(request, session_status_string, 2)
    except Exception as exception:   # pylint: disable=broad-except
        save_request_status(request, session_status_string, -1)
        log.exception('Unable to update problem settings for course')
        return JsonResponse(
            {
                'ErrMsg': str(exception),
                'Stage': -1
            },
            status=500
        )

    _do_update.delay(course_key_string, request.user.id, modified_settings)

    return JsonResponse({'Status': 'OK'})


@login_required
def utility_bulkupdate_handler(request, course_key_string):
    """
    Handler for bulk updates view requests in the utilities tool.
    Updates max_attempts and show_answer settings for all problsms in a given course.
    """

    print(request.user.id)

    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    course = modulestore().get_course(course_key, 3)

    if 'text/html' in request.META.get('HTTP_ACCEPT', 'text/html'):
        if request.method == 'GET':
            return _utility_bulkupdate_get_handler(request, course_key_string, course)
        else:
            return HttpResponseNotFound()

    elif 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        if request.method == 'POST':
            return _utility_bulkupdate_post_handler(request, course_key_string, course)
        else:
            return HttpResponseNotFound()


@require_GET
@login_required
def utility_bulkupdate_status_handler(request, course_key_string, max_attempts=None, show_answer=None):
    """
    Returns an integer corresponding to the status of a file import. These are:

        -X : Update unsuccessful due to some error with X as stage [0-3]
        0 : No status info found (update done or submit still in progress)
        1 : Validating.
        2 : Updating mongo
        3 : Update successful

    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    try:
        session_status = request.session["update_status"]
        status = session_status[course_key_string + max_attempts + show_answer]
    except KeyError:
        status = 0

    return JsonResponse({"UpdateStatus": status})
