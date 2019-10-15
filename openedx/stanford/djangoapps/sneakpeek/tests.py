"""
Tests for deeplink middleware for sneakpeek
"""
from datetime import datetime, timedelta
from ddt import ddt, data
from importlib import import_module
import unittest

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.test import Client
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse

from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory
from .middleware import SneakPeekLoginMiddleware

NO_SNEAKPEEK_PATHS = [
    '/courses/open/course/run/lti_rest_endpoints/',  # lti_rest_endpoint
    '/courses/open/course/run/xblock/usage_id/handler_noauth/handler',  # xblock_handler_noauth
    '/courses/open/course/run/xqueue/user_id/mod_id/dispatch',
    '/courses/open/course/run/about',
    '/courses/open/course/run/info',
    '/courses/open/course/run/',
]


class NonRegisteredUserFactory(UserFactory):
    # only difference from UserFactory is the profile has nonregistered bit set
    @classmethod
    def _after_postgeneration(cls, obj, create, results=None):
        if create:
            obj.profile.nonregistered = True
            obj.profile.save()


@ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class SneakPeekDeeplinkMiddlewareTests(ModuleStoreTestCase):
    """
    Tests of Sneakpek deeplink middleware
    """
    def setUp(self):
        from courseware.models import CoursePreference
        super(SneakPeekDeeplinkMiddlewareTests, self).setUp()
        self.client = Client()
        self.factory = RequestFactory()
        self.middleware = SneakPeekLoginMiddleware()
        month = timedelta(days=30)
        month2 = timedelta(days=60)
        now = datetime.now()
        self.nonsneakpeek_course = CourseFactory.create(
            org='nonsneakpeek',
            number='course',
            run='run',
            enrollment_start=now - month,
            enrollment_end=now + month)
        self.nonsneakpeek_course.save()
        self.open_course = CourseFactory.create(
            org='open',
            number='course',
            run='run',
            enrollment_start=now - month,
            enrollment_end=now + month)
        self.open_course.save()
        self.closed_course = CourseFactory.create(
            org='closed',
            number='course',
            run='run',
            enrollment_start=now - month2,
            enrollment_end=now - month)
        self.closed_course.save()
        self.course_to_delete = CourseFactory.create(
            org='deleted',
            number='course',
            run='run',
            enrollment_start=now - month,
            enrollment_end=now + month,
        )
        self.course_to_delete.save()
        CoursePreference(
            course_id=self.open_course.id,
            pref_key="allow_nonregistered_access",
            pref_value="true",
        ).save()
        CoursePreference(
            course_id=self.closed_course.id,
            pref_key="allow_nonregistered_access",
            pref_value="true",
        ).save()
        CoursePreference(
            course_id=self.course_to_delete.id,
            pref_key='allow_nonregistered_access',
            pref_value='true',
        ).save()

    def make_successful_sneakpeek_login_request(self):
        """
        This returns a request which will cause a sneakpeek to happen
        """
        sneakpeek_path = '/courses/open/course/run/courseware'
        req = self.factory.get(sneakpeek_path)
        req.session = import_module(settings.SESSION_ENGINE).SessionStore()  # empty session
        req.user = AnonymousUser()
        return req

    def assertSuccessfulSneakPeek(self, request, course):
        self.assertTrue(request.user.is_authenticated)
        self.assertFalse(request.user.is_registered())
        self.assertTrue(CourseEnrollment.is_enrolled(request.user, course.id))

    def assertNoSneakPeek(self, request, course, check_auth=True):
        if check_auth:
            self.assertFalse(request.user.is_authenticated)
        self.assertEquals(0, CourseEnrollment.objects.filter(course_id=course.id).count())

    def test_sneakpeek_success(self):
        req = self.make_successful_sneakpeek_login_request()
        self.assertIsNone(self.middleware.process_request(req))
        self.assertSuccessfulSneakPeek(req, self.open_course)

    def test_non_get(self):
        req = self.make_successful_sneakpeek_login_request()
        req.method = "POST"
        self.assertIsNone(self.middleware.process_request(req))
        self.assertNoSneakPeek(req, self.open_course)

    def test_get_404(self):
        req = self.make_successful_sneakpeek_login_request()
        req.path = '/foobarmew'
        self.assertIsNone(self.middleware.process_request(req))
        self.assertNoSneakPeek(req, self.open_course)

    @data(*NO_SNEAKPEEK_PATHS)
    def test_url_blacklists(self, path):
        req = self.make_successful_sneakpeek_login_request()
        req.path = path
        self.assertIsNone(self.middleware.process_request(req))
        self.assertNoSneakPeek(req, self.open_course)

    def test_authenticated_user(self):
        req = self.make_successful_sneakpeek_login_request()
        user = UserFactory()
        user.save()
        req.user = user
        self.assertIsNone(self.middleware.process_request(req))
        self.assertNoSneakPeek(req, self.open_course, check_auth=False)

    def test_noncourse_path(self):
        req = self.make_successful_sneakpeek_login_request()
        req.path = "/dashboard"
        self.assertIsNone(self.middleware.process_request(req))
        self.assertNoSneakPeek(req, self.open_course)

    def test_nonsneakpeek_course(self):
        req = self.make_successful_sneakpeek_login_request()
        req.path = '/courses/nonsneakpeek/course/run/info'
        self.assertIsNone(self.middleware.process_request(req))
        self.assertNoSneakPeek(req, self.nonsneakpeek_course)

    def test_sneakpeek_course_enrollment_closed(self):
        req = self.make_successful_sneakpeek_login_request()
        req.path = '/courses/closed/course/run/info'
        self.assertIsNone(self.middleware.process_request(req))
        self.assertNoSneakPeek(req, self.closed_course)

    def test_deleted_course_with_preferences(self):
        """
        Verify that Sneakpeek requests fail after deleting a course
        """
        request = self.make_successful_sneakpeek_login_request()
        request.path = '/courses/deleted/course/run/courseware'
        self.assertIsNone(self.middleware.process_request(request))
        self.assertSuccessfulSneakPeek(request, self.course_to_delete)
        self.store.delete_course(self.course_to_delete.id, self.user)
        request = self.make_successful_sneakpeek_login_request()
        request.path = '/courses/deleted/course/run/courseware'
        self.assertIsNone(self.middleware.process_request(request))
        self.assertFalse(request.user.is_authenticated)
        count = CourseEnrollment.objects.filter(course_id=self.course_to_delete.id).count()
        self.assertEquals(1, count)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestNonRegisteredUser(TestCase):
    """
    Tests nonregistered (auto-created) users
    """
    def setUp(self):
        self.request_factory = RequestFactory()
        self.user = NonRegisteredUserFactory()
        self.course_id = "course/id/doesnt_matter"

    def test_nonregistered_user_factory(self):
        self.assertTrue(self.user.profile.nonregistered)

    def test_nonregistered_progress_404(self):
        import courseware.views.views as views
        with self.assertRaises(Http404):
            req = self.request_factory.get(reverse('progress', args=[self.course_id]))
            req.user = self.user
            views.progress(req, self.course_id)
