from celery.task import task
from django.core.mail import send_mail
from django.core.urlresolvers import reverse

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata

from opaque_keys.edx.keys import CourseKey
from xblock.fields import Scope


def _get_course_problems(course_key):
    """
    Retrieve all problems in the course
    """
    # Note: Some components may have been orphaned due to a bug in split
    # modulestore (PLAT-799). We may be returning orphaned components in this
    # list to be updated as well
    return modulestore().get_items(
        course_key,
        qualifiers={"category": 'problem'},
    )


class BulkUpdateUtil():
    """
    Utility class that hold functions for bulksettings operations
    """

    @classmethod
    def update_metadata(cls, course_key, user_id, metadata):
        """
        Updates metadata settings for all problems.
        """

        problems = _get_course_problems(course_key)

        with modulestore().bulk_operations(course_key):
            for problem in problems:
                for metadata_key, value in metadata.items():
                    field = problem.fields[metadata_key]
                    try:
                        value = field.from_json(value)
                    except Exception as exception:
                        print(exception)
                    field.write_to(problem, value)

                modulestore().update_item(problem, user_id)

                if modulestore().has_published_version(problem):
                    modulestore().publish(problem.location, user_id)


@task()
def bulk_update_problem_settings(course_key_string, user_id, modified_settings):
    course_key = CourseKey.from_string(course_key_string)
    course = modulestore().get_course(course_key, 3)

    try:
        BulkUpdateUtil.update_metadata(course_key, user_id, modified_settings)
        course_key = CourseKey.from_string(course_key_string)
        course = modulestore().get_course(course_key, 3)
    except Exception as exception:
        print(exception)
