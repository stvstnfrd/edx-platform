"""
Middleware classes to login/logout sneakpeek users
"""
import logging

from django.contrib.auth import logout
from django.core.urlresolvers import resolve
from django.http import Http404
from django.shortcuts import redirect

from courseware.models import CoursePreference
from openedx.stanford.djangoapps.sneakpeek.lib import check_can_enroll_in_course
from openedx.stanford.djangoapps.sneakpeek.lib import create_and_login_nonregistered_user
from student.models import CourseEnrollment
from student.models import UserProfile
from xmodule.modulestore.django import modulestore
from util.request import course_id_from_url

DISALLOW_SNEAKPEEK_URL_NAMES = (
    'lti_rest_endpoints',
    'xblock_handler_noauth',
    'xqueue_callback',
    'about_course',
    'course_root',
    'info',
)
LOG = logging.getLogger("stanford.sneakpeek")


class SneakPeekLoginMiddleware(object):
    """
    Support deep-links for courses that allow sneakpeek

    The user will be registered anonymously, logged in, and enrolled in the course.
    """
    def process_request(self, request):
        """
        Only if the following are all true:
          1. request is a GET
          2. request is NOT to a URL in DISALLOW_SNEAKPEEK_URL_NAMES
          3. request.user is AnonymousUser (This middleware must be added after the AuthenticationMiddleware)
          4. request has a course context
          5. request's course allows sneakpeek
          6. request's course's enrollment period is open
        Does the following:
          1. Registers an anonymous user
          2. Login this user in
          3. Enrolls this user in the course
        """
        if request.method != 'GET':
            return None
        try:
            match = resolve(request.path)
            if match.url_name in DISALLOW_SNEAKPEEK_URL_NAMES:
                return None
        except Http404:
            pass
        if request.user.is_authenticated:
            return None
        course_id = course_id_from_url(request.path)
        if not course_id:
            return None
        if not CoursePreference.course_allows_nonregistered_access(course_id):
            return None
        if not modulestore().has_course(course_id):
            message = u"Sneakpeek attempt for non-existent course %s"
            LOG.warning(message, course_id)
            return None
        can_enroll, _ = check_can_enroll_in_course(
            request.user,
            course_id,
        )
        if not can_enroll:
            return None
        create_and_login_nonregistered_user(request)
        CourseEnrollment.enroll(request.user, course_id)
        return None


class SneakPeekLogoutMiddleware(object):
    """
    Log out all sneakpeek users and redirect the same URL

    Never allow sneakpeek in CMS
    """
    def process_request(self, request):
        """
        Log out all sneakpeek users and redirect the same URL
        """
        if request.user.is_anonymous:
            return None
        if request.user.is_registered():
            return None
        logout(request)
        return redirect(request.get_full_path())
