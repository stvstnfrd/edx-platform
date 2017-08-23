import requests

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
    def update_bulksettings_metadata(cls, problems_list, user_id, metadata):
        """
        Updates settings metadata for all sections, subsections, units, and problems.
        """
        store = modulestore()
        for problem in problems_list:
            for metadata_key, value in metadata.items():
                field = problem.fields[metadata_key]

                try:
                    value = field.from_json(value)
                except ValueError as verr:
                    LOGGER.error("Error in _update_settings_for_problem")

                field.write_to(problem, value)

            # update the xblock and call any xblock callbacks
            modulestore().update_item(problem, user_id, is_publish_root=False)


def get_course_problems(course_key):
    """
    Retrieve all XBlocks in the course for a particular category.

    Returns only XBlocks that are published and haven't been deleted.
    """
    # Note: Some components may have been orphaned due to a bug in split 
    # modulestore (PLAT-799). We may be returning orphaned components in this
    # list to be updated as well
    return modulestore().get_items(
        course_key,
        qualifiers={"category": 'problem'},
    )

@task()
def _do_update(course_key_string, user_id, modified_settings):
    course_key = CourseKey.from_string(course_key_string)
    course = modulestore().get_course(course_key, 3)

    try:
        problems_list = get_course_problems(course_key)
        BulkUpdateUtil.update_bulksettings_metadata(problems_list, user_id, modified_settings)
        course_key = CourseKey.from_string(course_key_string)
        course = modulestore().get_course(course_key, 3)
    except Exception as exception:   # pylint: disable=broad-except
        LOGGER.error(exception)