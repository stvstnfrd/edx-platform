import logging

from django.contrib.auth import logout
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.http import require_POST
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from courseware.models import CoursePreference
from openedx.stanford.djangoapps.sneakpeek.lib import check_can_enroll_in_course
from openedx.stanford.djangoapps.sneakpeek.lib import create_and_login_nonregistered_user
from student.models import CourseEnrollment

log = logging.getLogger("stanford.sneakpeek")


@require_POST
def setup_sneakpeek(request, course_id):
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    if not CoursePreference.course_allows_nonregistered_access(course_key):
        return HttpResponseForbidden("Cannot access the course")
    if not request.user.is_authenticated:
        # if there's no user,
        # create a nonregistered user
        create_and_login_nonregistered_user(request)
    elif request.user.is_registered():
        # registered users can't sneakpeek,
        # so log them out and create a new nonregistered user
        logout(request)
        create_and_login_nonregistered_user(request)
        # fall-through case is a sneakpeek user that's already logged in
    can_enroll, error_msg = check_can_enroll_in_course(
        request.user,
        course_key,
    )
    if not can_enroll:
        log.error(error_msg)
        return HttpResponseBadRequest(error_msg)
    CourseEnrollment.enroll(request.user, course_key)
    return HttpResponse("OK. Allowed sneakpeek")
