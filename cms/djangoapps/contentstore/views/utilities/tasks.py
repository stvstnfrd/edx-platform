from celery.task import task
from celery.utils.log import get_task_logger

from django.core.mail import send_mail
from django.core.urlresolvers import reverse

# Imports from common / openedx
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata

from opaque_keys.edx.keys import CourseKey  # ?
from xblock.fields import Scope  # ?

LOGGER = get_task_logger(__name__)

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
    def _update_with_callback(cls, xblock, user_id, old_metadata=None, old_content=None):
        """
        Updates the xblock in the modulestore.
        But before doing so, it calls the xblock's editor_saved callback function.
        """
        if callable(getattr(xblock, "editor_saved", None)):
            if old_metadata is None:
                old_metadata = own_metadata(xblock)
            if old_content is None:
                old_content = xblock.get_explicitly_set_fields_by_scope(Scope.content)

        # Update after the callback so any changes made in the callback will get persisted.
        return modulestore().update_item(xblock, user_id)

    @classmethod
    def _update_settings_for_problem(cls, user_id, xblock, metadata=None):
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
                        LOGGER.error("Error in _update_settings_for_problem")

                    field.write_to(xblock, value)

            # update the xblock and call any xblock callbacks
            xblock = cls._update_with_callback(xblock, user_id, old_metadata)

    @classmethod
    def update_bulksettings_metadata(cls, course, user_id, modified_settings):
        """
        Updates settings metadata for all sections, subsections, units, and problems.
        """

        print("Inside update_bulksettings_metadata")
        for section in course.get_children():
            for subsection in section.get_children():
                for unit in subsection.get_children():
                    for component in unit.get_children():
                        if component.location.category == 'problem':
                            cls._update_settings_for_problem(user_id, component, modified_settings)



@task()
def _do_update(course_key_string, user_id, modified_settings):
    course_key = CourseKey.from_string(course_key_string)
    course = modulestore().get_course(course_key, 3)

    try:
        BulkUpdateUtil.update_bulksettings_metadata(course, user_id, modified_settings)
        course_key = CourseKey.from_string(course_key_string)
        course = modulestore().get_course(course_key, 3)
    except Exception as exception:   # pylint: disable=broad-except
        LOGGER.error('Unable to update problem settings for course')