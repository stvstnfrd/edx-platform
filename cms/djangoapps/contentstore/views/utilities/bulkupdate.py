"""
Views related to bulk settings change operations on course problems.
"""

import logging

from django.core.exceptions import PermissionDenied
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


class BulkUpdateUtil():
    """
    Utility class that hold functions for bulksettings operations
    """

    @classmethod
    def reverse_course_url(cls, handler, course_key_string, kwargs=None):
        """
        Creates the URL for handlers that use course_keys as URL parameters.
        """
        kwargs_for_reverse = {
            'course_key_string': unicode(course_key_string)
        }
        if kwargs:
            kwargs_for_reverse.update(kwargs)
        return reverse('contentstore.views.' + handler, kwargs=kwargs_for_reverse)

    @classmethod
    def save_request_status(cls, request, key, status):
        """
        Save update status for a course in request session
        """
        session_status = request.session.get('update_status')
        if session_status is None:
            session_status = request.session.setdefault("update_status", {})

        session_status[key] = status
        request.session.save()

    @classmethod
    def _update_with_callback(cls, xblock, user, old_metadata=None, old_content=None):
        """
        Updates the xblock in the modulestore.
        But before doing so, it calls the xblock's editor_saved callback function.
        """
        if callable(getattr(xblock, "editor_saved", None)):
            if old_metadata is None:
                old_metadata = own_metadata(xblock)
            if old_content is None:
                old_content = xblock.get_explicitly_set_fields_by_scope(Scope.content)
#            xblock.xmodule_runtime = StudioEditModuleRuntime(user) #TODO Do we need this? Would introduce more dependencies
            xblock.editor_saved(user, old_metadata, old_content)

        # Update after the callback so any changes made in the callback will get persisted.
        return modulestore().update_item(xblock, user.id)

    @classmethod
    def _update_settings_for_problem(cls, user, xblock, metadata=None, nullout=None, publish=None):
        """
        Saves problem with new settings. Has special processing for publish and nullout and Nones in metadata.
        nullout means to truly set the field to None whereas nones in metadata mean to unset them (so they revert
        to default).
        """

        store = modulestore()
        # Perform all xblock changes within a (single-versioned) transaction
        with store.bulk_operations(xblock.location.course_key):

            old_metadata = own_metadata(xblock)

            # update existing metadata with submitted metadata (which can be partial)
            if metadata is not None:
                for metadata_key, value in metadata.items():
                    field = xblock.fields[metadata_key]

                    try:
                        value = field.from_json(value)
                    except ValueError as verr:
                        reason = _("Invalid data")
                        if verr.message:
                            reason = _("Invalid data ({details})").format(details=verr.message)
                        return JsonResponse(
                            {
                                'ErrMsg': reason,
                                'Stage': -2
                            },
                            status=500
                        )

                    field.write_to(xblock, value)

            # update the xblock and call any xblock callbacks
            xblock = cls._update_with_callback(xblock, user, old_metadata)

    @classmethod
    def update_bulksettings_metadata(cls, course, user, modified_settings):
        """
        Updates settings metadata for all sections, subsections, units, and problems.
        """

        for section in course.get_children():
            for subsection in section.get_children():
                for unit in subsection.get_children():
                    for component in unit.get_children():
                        if component.location.category == 'problem':
                            cls._update_settings_for_problem(user, component, modified_settings)


log = logging.getLogger(__name__)

__all__ = [
    'utility_bulkupdate_handler',
    'utility_bulkupdate_status_handler',
]


@login_required
def utility_bulkupdate_handler(request, course_key_string):
    """
    Handler for bulk updates view requests in the utilities tool.
    Updates max_attempts and show_answer settings for all problsms in a given course.
    """

    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    course = modulestore().get_course(course_key, 3)

    if 'text/html' in request.META.get('HTTP_ACCEPT', 'text/html'):
        if request.method == 'GET':
            max_attempts = 0
            show_answer = SHOW_ANSWER_OPTIONS[0]
            update_url = BulkUpdateUtil.reverse_course_url(
                "utility_bulkupdate_handler",
                course_key_string
            )
            status_url = BulkUpdateUtil.reverse_course_url(
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
        else:
            return HttpResponseNotFound()

    elif 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        if request.method == 'POST':
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
                BulkUpdateUtil.save_request_status(request, session_status_string, 1)

                if max_attempts.find('null') == -1:
                    try:
                        max_attempts = int(max_attempts)
                    except:
                        BulkUpdateUtil.save_request_status(request, session_status_string, -1)
                        return JsonResponse(
                            {
                                'ErrMsg': 'Invalid settings',
                                'Stage': -1
                            },
                            status=400
                        )
                    if max_attempts < 0:
                        BulkUpdateUtil.save_request_status(request, session_status_string, -1)
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
                        BulkUpdateUtil.save_request_status(request, session_status_string, -1)
                        return JsonResponse(
                            {
                                'ErrMsg': 'Invalid settings',
                                'Stage': -1
                            },
                            status=400
                        )
                    else:
                        modified_settings['showanswer'] = show_answer
                BulkUpdateUtil.save_request_status(request, session_status_string, 2)
            except Exception as exception:   # pylint: disable=broad-except
                BulkUpdateUtil.save_request_status(request, session_status_string, -1)
                log.exception('Unable to update problem settings for course')
                return JsonResponse(
                    {
                        'ErrMsg': str(exception),
                        'Stage': -1
                    },
                    status=500
                )

            try:
                BulkUpdateUtil.update_bulksettings_metadata(course, request.user, modified_settings)
                BulkUpdateUtil.save_request_status(request, session_status_string, 3)
            except Exception as exception:   # pylint: disable=broad-except
                BulkUpdateUtil.save_request_status(request, session_status_string, -2)
                log.exception('Unable to update problem settings for course')
                return JsonResponse(
                    {
                        'ErrMsg': str(exception),
                        'Stage': -2
                    },
                    status=500
                )
            finally:
                # set failed stage number with negative sign in case of unsuccessful import
                if session_status[session_status_string] != 3:
                    BulkUpdateUtil.save_request_status(request, session_status_string, -abs(session_status[session_status_string]))

                # status == 3 represents that course has been updated successfully.
                if session_status[session_status_string] == 3:
                    # Reload the course so we have the latest state
                    course_key = CourseKey.from_string(course_key_string)
                    course = modulestore().get_course(course_key, 3)

            return JsonResponse({'Status': 'OK'})
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
