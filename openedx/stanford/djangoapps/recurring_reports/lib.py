"""
TODO: Add docstring
"""
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


def get_all_course_overviews(blacklist_organizations=None, blacklist_courses=None):
    """
    TODO: Add docstring
    """
    blacklist = _get_blacklisted_courses(blacklist_organizations, blacklist_courses)
    overviews = CourseOverview.objects.exclude(
        id__in=blacklist,
    )
    return overviews


def _get_blacklisted_courses(organizations=None, course_ids=None):
    """
    Fetch a list of all blacklisted courses

    TODO: cribbed from:
        openedx/stanford/djangoapps/auth_lagunita/models.py
    """
    organizations = organizations or []
    course_ids = course_ids or []
    blacklist_by_organization = CourseOverview.objects.filter(
        org__in=organizations,
    )
    blacklist_by_organization = [
        course.id
        for course in blacklist_by_organization
    ]
    blacklist_by_course_id = [
        CourseKey.from_string(course_id)
        for course_id in course_ids
    ]
    blacklist = blacklist_by_organization + blacklist_by_course_id
    return blacklist
