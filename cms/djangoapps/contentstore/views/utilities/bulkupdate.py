"""
Views related to bulk settings change operations on course problems.
"""

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound
from django.views.decorators.http import require_GET

from edxmako.shortcuts import render_to_response
from student.auth import has_course_author_access
from util.json_request import JsonResponse
from xmodule.modulestore.django import modulestore

from opaque_keys.edx.keys import CourseKey

from contentstore.views.utilities.tasks import bulk_update_problem_settings

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
DEFAULT_MAX_ATTEMPTS = 0
DEFAULT_SHOW_ANSWER = SHOW_ANSWER_OPTIONS[0]


__all__ = [
    'utility_bulkupdate_handler',
    'utility_bulkupdate_status_handler',
]


def _reverse_course_url(handler, course_key_string, kwargs=None):
    """
    Internal method used to create the URL for handlers that use
    course_keys as URL parameters
    """
    kwargs_for_reverse = {
        'course_key_string': unicode(course_key_string)
    }
    if kwargs:
        kwargs_for_reverse.update(kwargs)
    return reverse('contentstore.views.' + handler, kwargs=kwargs_for_reverse)


def _save_request_status(request, key, status):
    """
    Internal method used to save update status for a course in request
    session
    """
    session_status = request.session.get('update_status')
    if session_status is None:
        session_status = request.session.setdefault("update_status", {})

    session_status[key] = status
    request.session.save()


def _update_advanced_settings(request, course_key_string, session_status_string, modified_settings):
    """
    Internal method used to save to advanced settings
    """
    course_key = CourseKey.from_string(course_key_string)
    course = modulestore().get_course(course_key, 3)
    try:
        with modulestore().bulk_operations(course_key):
            for key, value in modified_settings.iteritems():
                setattr(course, key, value)

            modulestore().update_item(course, request.user.id)

    except:
        _save_request_status(request, session_status_string, 2)
        return JsonResponse(
            {
                'ErrMsg': 'Unable to update advanced settings',
                'Stage': -2
            },
            status=500
        )


def _utility_bulkupdate_get_handler(request, course_key_string):
    """
    Internal bulkupdate handler for GET operation
    """
    update_url = _reverse_course_url(
        "utility_bulkupdate_handler",
        course_key_string
    )
    status_url = _reverse_course_url(
        "utility_bulkupdate_status_handler",
        course_key_string,
        kwargs={
            'max_attempts': 'fillerMaxAttempts',
            'show_answer': 'fillerShowAnswer'
        }
    )

    course_key = CourseKey.from_string(course_key_string)
    course = modulestore().get_course(course_key, 3)

    return render_to_response(
        'bulkupdate.html',
        {
            'context_course': course,
            'bulkupdate_update_url': update_url,
            'bulkupdate_status_url': status_url,
            'default_max_attempts': DEFAULT_MAX_ATTEMPTS,
            'default_show_answer': DEFAULT_SHOW_ANSWER,
            'show_answer_options': SHOW_ANSWER_OPTIONS
        }
    )


def _utility_bulkupdate_post_handler(request, course_key_string):
    """
    Internal bulkupdate handler for POST operation
    """
    modified_settings = {}
    user = request.user

    # Retrieve settings from request
    try:
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

    # Validate settings
    _save_request_status(request, session_status_string, 1)

    if max_attempts.find('null') == -1:
        try:
            max_attempts = int(max_attempts)
        except:
            _save_request_status(request, session_status_string, -1)
            return JsonResponse(
                {
                    'ErrMsg': 'Given value for max attempts is not an integer',
                    'Stage': -1
                },
                status=400
            )
        if max_attempts < 0:
            _save_request_status(request, session_status_string, -1)
            return JsonResponse(
                {
                    'ErrMsg': 'Given value for max attempts is negative',
                    'Stage': -1
                },
                status=400
            )
        else:
            modified_settings['max_attempts'] = max_attempts

    if show_answer.find('null') == -1:
        if show_answer in SHOW_ANSWER_OPTIONS:
            modified_settings['showanswer'] = show_answer
        else:
            _save_request_status(request, session_status_string, -1)
            return JsonResponse(
                {
                    'ErrMsg': 'Given value for show answer is not an available option',
                    'Stage': -1
                },
                status=400
            )
    _save_request_status(request, session_status_string, 2)
    _update_advanced_settings(request, course_key_string, session_status_string, modified_settings)
    _save_request_status(request, session_status_string, 3)
    bulk_update_problem_settings.delay(course_key_string, user.id, user.username, user.email, modified_settings)

    return JsonResponse({'Status': 'OK'})


@login_required
def utility_bulkupdate_handler(request, course_key_string):
    """
    Handler for bulk update requests in the utilities tool. Currently
    updates maxAttempts and showAnswer settings for all problems in a
    given course and sets as settings for future problems in advanced
    settings
    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    if 'text/html' in request.META.get('HTTP_ACCEPT', 'text/html'):
        if request.method == 'GET':
            return _utility_bulkupdate_get_handler(request, course_key_string)
        else:
            return HttpResponseNotFound()

    elif 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        if request.method == 'POST':
            return _utility_bulkupdate_post_handler(request, course_key_string)
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
        2 : Updating advanced settings
        3 : Updating problems

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
