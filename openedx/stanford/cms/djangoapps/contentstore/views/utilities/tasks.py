from celery.task import task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from smtplib import SMTPException

from edxmako.shortcuts import render_to_string
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata

from opaque_keys.edx.keys import CourseKey
from xblock.fields import Scope


LOGGER = get_task_logger(__name__)

def _get_course_problems(course_key):
    """
    Retrieve all problems in the course

    Note: Some components may have been orphaned due to a bug in split
    modulestore (PLAT-799). We may be returning orphaned components in this
    list to be updated as well
    """
    return modulestore().get_items(
        course_key,
        qualifiers={"category": 'problem'},
    )


def _send_email_on_completion(course, user_username, user_email, modified_settings, success):
    """
    Send email to user on completion of celery task completion
    """
    context = {
        'username': user_username,
        'course_name': course.display_name,
        'modified_settings': modified_settings,
        'success': success,
    }

    from_email = settings.DEFAULT_FROM_EMAIL
    subject = render_to_string('emails/utilities_bulk_update_done_subject.txt', context)
    subject = ''.join(subject.splitlines())
    message = render_to_string('emails/utilities_bulk_update_done_message.txt', context)

    try:
        send_mail(
            subject,
            message,
            from_email,
            [user_email],
            fail_silently=False,
        )
    except SMTPException:
        LOGGER.error("Failure sending e-mail for bulk update completion to %s", user_email)


def _update_metadata(course_key, user_id, metadata):
    """
    Updates metadata settings for all problems.
    """
    store = modulestore()
    problems = _get_course_problems(course_key)
    with store.bulk_operations(course_key):
        for problem in problems:
            for metadata_key, value in metadata.items():
                field = problem.fields[metadata_key]
                try:
                    value = field.from_json(value)
                except Exception as exception:
                    LOGGER.error(exception)
                field.write_to(problem, value)
            store.update_item(problem, user_id)
            if store.has_published_version(problem):
                store.publish(problem.location, user_id)


@task()
def bulk_update_problem_settings(course_key_string, user_id, user_username, user_email, modified_settings):
    store = modulestore()
    course_key = CourseKey.from_string(course_key_string)
    course = store.get_course(course_key, 3)
    try:
        _update_metadata(course_key, user_id, modified_settings)
        success = True
    except Exception as exception:
        LOGGER.error(exception)
        success = False
    _send_email_on_completion(course, user_username, user_email, modified_settings, success)
