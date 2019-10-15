"""
Provide utility/helper methods for nonregistered/sneakpeek logic
"""
from datetime import datetime
import logging

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext as _
from pytz import UTC

from courseware.access import has_access
from courseware.models import CoursePreference
from student.models import CourseEnrollment
from student.models import UserProfile
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError


log = logging.getLogger("stanford.sneakpeek")
NONREGISTERED_CATEGORY_WHITELIST = [
    "about",
    "chapter",
    "course",
    "course_info",
    "problem",
    "sequential",
    "vertical",
    "videoalpha",
    #"combinedopenended",
    #"discussion",
    "html",
    #"peergrading",
    "static_tab",
    "video",
    #"annotatable",
    "book",
    "conditional",
    #"crowdsource_hinter",
    "custom_tag_template",
    #"discuss",
    #"error",
    "hidden",
    "image",
    "imagemodal",
    "invideoquiz",
    "problemset",
    "randomize",
    "raw",
    "section",
    "slides",
    "timelimit",
    "videodev",
    "videosequence",
    "word_cloud",
    "wrapper",
]


def check_can_enroll_in_course(user, course_key):
    """
    Refactored check for user being able to enroll in course
    Returns (bool, error_message), where error message is only applicable if bool == False
    """
    try:
        course = modulestore().get_course(course_key)
    except ItemNotFoundError:
        log.warning(
            "User {0} tried to enroll in non-existent course {1}".format(
                user.username,
                course_key,
            )
        )
        return False, _("Course id is invalid")
    if not within_enrollment_period(course):
        return False, _("Enrollment is closed")
    return True, ""


def _get_random_anon_username():
    # django 1.8 has 30 char usernames
    candidate = "anon__{}".format(get_random_string(24))
    while User.objects.filter(username=candidate).exists():
        # get_random_string output is alphanumeric
        candidate = "anon__{}".format(get_random_string(24))
    return candidate


def _create_nonregistered_user():
    anon_username = _get_random_anon_username()
    email_split = settings.ANONYMOUS_USER_EMAIL.split('@')
    anon_email = "{}+{}@{}".format(
        email_split[0],
        anon_username,
        email_split[-1],
    )
    anon_user = User(username=anon_username, email=anon_email, is_active=False)
    anon_user.save()
    profile = UserProfile(user=anon_user, nonregistered=True)
    profile.save()
    return anon_user


def create_and_login_nonregistered_user(request):
    """
    Create a nonregistered user and log them in with a long session life
    """
    new_student = _create_nonregistered_user()
    new_student.backend = settings.AUTHENTICATION_BACKENDS[0]
    login(request, new_student)
    # set session to very long to reduce number of nonreg users created
    request.session.set_expiry(604800)


def _bind_can_load_forum(can_load_function, user):
    """
    Bind variables for the function
    """
    def can_load_forum():
        """
        Can this user access the forums in this course?
        """
        return (
            can_load_function()
            and
            user.is_registered()
        )
    return can_load_forum


def extend_checkers_has_access_course(user, course, can_load):
    """
    Bind and provide helper methods to check access
    """
    checkers = {
        'load_forum': _bind_can_load_forum(can_load, user),
    }
    return checkers


def is_registered(user):
    """
    Handles django anonymous users.  SHOULD use this to test whether request.user has registered,
    i.e. has a profile that says not nonregistered,
    instead of directly accessing user.profile.nonregistered,
    because if the user is AnonymousUser it won't have a profile.
    """
    registration = None
    if hasattr(user, 'profile'):
        registration = not user.profile.nonregistered
    return registration


def is_nonregistered(user):
    """
    Check if user is nonregistered (not Django Anonymous)
    """
    registration = is_registered(user) is False
    return registration


def deny_nonregistered_access(user, descriptor):
    """
    Check if nonregistered access should be denied for this user on this descriptor
    """
    should_deny = False
    if is_nonregistered(user):
        should_deny = descriptor.category not in NONREGISTERED_CATEGORY_WHITELIST
    return should_deny


def within_enrollment_period(course):
    """
    Just a time boundary check, handles if start or stop were set to None
    """
    now = datetime.now(UTC)
    start = course.enrollment_start
    if start is not None:
        start = start.replace(tzinfo=UTC)
    end = course.enrollment_end
    if end is not None:
        end = end.replace(tzinfo=UTC)
    return (start is None or now > start) and (end is None or now < end)


def can_enroll_nonregistered(user, course):
    """
    Check if nonregistered access is allow for a course

    Sneakpeek is only allowed if:
    1) within enrollment period
    2) course specifies it's okay
    3) request.user is not a registered user.
    """
    course_key = course.id
    return (
        within_enrollment_period(course)
        and
        CoursePreference.course_allows_nonregistered_access(course_key)
        and
        not user.is_registered()
    )
