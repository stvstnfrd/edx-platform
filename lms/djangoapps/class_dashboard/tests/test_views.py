"""
Tests for class dashboard (Metrics tab in instructor dashboard)
"""
import json

from django.test.client import RequestFactory
from mock import patch
from nose.plugins.attrib import attr
from six import text_type

from class_dashboard import views
from student.tests.factories import AdminFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@attr(shard=1)
class TestViews(ModuleStoreTestCase):
    """
    Tests related to class_dashboard/views.py
    """

    def setUp(self):
        super(TestViews, self).setUp()

        self.request_factory = RequestFactory()
        self.request = self.request_factory.get('')
        self.request.user = None
        self.simple_data = {'error': 'error'}
        self.enrollment = 100

    @patch('class_dashboard.views.has_instructor_access_for_class')
    def test_all_problem_grade_distribution_has_access(self, has_access):
        """
        Test returns proper value when have proper access
        """
        has_access.return_value = True
        response = views.all_problem_grade_distribution(self.request, 'test/test/test', self.enrollment)

        self.assertEqual(json.dumps(self.simple_data), response.content)

    @patch('class_dashboard.views.has_instructor_access_for_class')
    def test_all_problem_grade_distribution_no_access(self, has_access):
        """
        Test for no access
        """
        has_access.return_value = False
        response = views.all_problem_grade_distribution(self.request, 'test/test/test', self.enrollment)

        self.assertEqual("{\"error\": \"Access Denied: User does not have access to this course\'s data\"}", response.content)

    @patch('class_dashboard.views.has_instructor_access_for_class')
    def test_all_sequential_open_distribution_has_access(self, has_access):
        """
        Test returns proper value when have proper access
        """
        has_access.return_value = True
        response = views.all_sequential_open_distrib(self.request, 'test/test/test', self.enrollment)

        self.assertEqual(json.dumps(self.simple_data), response.content)

    @patch('class_dashboard.views.has_instructor_access_for_class')
    def test_all_sequential_open_distribution_no_access(self, has_access):
        """
        Test for no access
        """
        has_access.return_value = False
        response = views.all_sequential_open_distrib(self.request, 'test/test/test', self.enrollment)

        self.assertEqual("{\"error\": \"Access Denied: User does not have access to this course\'s data\"}", response.content)

    @patch('class_dashboard.views.has_instructor_access_for_class')
    def test_section_problem_grade_distribution_has_access(self, has_access):
        """
        Test returns proper value when have proper access
        """
        has_access.return_value = True
        response = views.section_problem_grade_distrib(self.request, 'test/test/test', '1', self.enrollment)

        self.assertEqual(json.dumps(self.simple_data), response.content)

    @patch('class_dashboard.views.has_instructor_access_for_class')
    def test_section_problem_grade_distribution_no_access(self, has_access):
        """
        Test for no access
        """
        has_access.return_value = False
        response = views.section_problem_grade_distrib(self.request, 'test/test/test', '1', self.enrollment)

        self.assertEqual("{\"error\": \"Access Denied: User does not have access to this course\'s data\"}", response.content)

    def test_sending_deprecated_id(self):

        course = CourseFactory.create()
        instructor = AdminFactory.create()
        self.request.user = instructor

<<<<<<< HEAD
        response = views.all_sequential_open_distrib(self.request, course.id.to_deprecated_string(), self.enrollment)
        self.assertEqual('[]', response.content)

        response = views.all_problem_grade_distribution(self.request, course.id.to_deprecated_string(), self.enrollment)
        self.assertEqual('[]', response.content)

        response = views.section_problem_grade_distrib(self.request, course.id.to_deprecated_string(), 'no section', self.enrollment)
=======
        response = views.all_sequential_open_distrib(self.request, text_type(course.id))
        self.assertEqual('[]', response.content)

        response = views.all_problem_grade_distribution(self.request, text_type(course.id))
        self.assertEqual('[]', response.content)

        response = views.section_problem_grade_distrib(self.request, text_type(course.id), 'no section')
>>>>>>> 7ad437b52cb5b2d65ab1b65e6147bcced05c42e4
        self.assertEqual('{"error": "error"}', response.content)
