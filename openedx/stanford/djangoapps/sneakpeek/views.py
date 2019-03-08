import logging

from django.conf import settings
from django.contrib.auth import login, logout
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_GET, require_POST
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from courseware.access import has_access
from courseware.models import CoursePreference
from student.models import CourseEnrollment
from student.models import UserProfile
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

log = logging.getLogger("stanford.sneakpeek")


@require_POST
def setup_sneakpeek(request, course_id):
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    if not CoursePreference.course_allows_nonregistered_access(course_key):
        return HttpResponseForbidden("Cannot access the course")
    if not request.user.is_authenticated:
        # if there's no user,
        # create a nonregistered user
        _create_and_login_nonregistered_user(request)
    elif UserProfile.has_registered(request.user):
        # registered users can't sneakpeek,
        # so log them out and create a new nonregistered user
        logout(request)
        _create_and_login_nonregistered_user(request)
        # fall-through case is a sneakpeek user that's already logged in
    can_enroll, error_msg = _check_can_enroll_in_course(
        request.user,
        course_key,
        access_type='within_enrollment_period',
    )
    if not can_enroll:
        log.error(error_msg)
        return HttpResponseBadRequest(error_msg)
    CourseEnrollment.enroll(request.user, course_key)
    return HttpResponse("OK. Allowed sneakpeek")


def _create_and_login_nonregistered_user(request):
    new_student = UserProfile.create_nonregistered_user()
    new_student.backend = settings.AUTHENTICATION_BACKENDS[0]
    login(request, new_student)
    request.session.set_expiry(604800)  # set session to very long to reduce number of nonreg users created


def _check_can_enroll_in_course(user, course_key, access_type="enroll"):
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
    if not has_access(user, access_type, course):
        return False, _("Enrollment is closed")
    return True, ""
