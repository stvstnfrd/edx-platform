"""
Tests for class dashboard (Metrics tab in instructor dashboard)
"""

import json

from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from django.test.utils import override_settings
from mock import patch
from nose.plugins.attrib import attr

from capa.tests.response_xml_factory import StringResponseXMLFactory
from class_dashboard.dashboard_data import (
    get_array_section_has_problem,
    get_d3_problem_grade_distrib,
    get_d3_section_grade_distrib,
    get_d3_sequential_open_distrib,
    get_problem_grade_distribution,
    get_problem_set_grade_distrib,
    get_section_display_name,
    get_sequential_open_distrib,
    get_students_opened_subsection,
    get_students_problem_grades
)
from class_dashboard.dashboard_data import get_non_student_list
from class_dashboard.views import has_instructor_access_for_class
from courseware.models import StudentModule
from courseware.tests.factories import StaffFactory, InstructorFactory
from courseware.tests.factories import StudentModuleFactory
from student.models import CourseEnrollment
from student.tests.factories import AdminFactory, CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

USER_COUNT = 11


@attr(shard=1)
class TestGetProblemGradeDistribution(SharedModuleStoreTestCase):
    """
    Tests related to class_dashboard/dashboard_data.py
    """
    @classmethod
    def setUpClass(cls):
        super(TestGetProblemGradeDistribution, cls).setUpClass()
        cls.course = CourseFactory.create(
            display_name=u"test course omega \u03a9",
        )
        with cls.store.bulk_operations(cls.course.id, emit_signals=False):
            section = ItemFactory.create(
                parent_location=cls.course.location,
                category="chapter",
                display_name=u"test factory section omega \u03a9",
            )
            cls.sub_section = ItemFactory.create(
                parent_location=section.location,
                category="sequential",
                display_name=u"test subsection omega \u03a9",
            )
            cls.unit = ItemFactory.create(
                parent_location=cls.sub_section.location,
                category="vertical",
                metadata={'graded': True, 'format': 'Homework'},
                display_name=u"test unit omega \u03a9",
            )
            cls.items = []
            for i in xrange(USER_COUNT - 1):
                item = ItemFactory.create(
                    parent_location=cls.unit.location,
                    category="problem",
                    data=StringResponseXMLFactory().build_xml(answer='foo'),
                    metadata={'rerandomize': 'always'},
                    display_name=u"test problem omega \u03a9 " + str(i)
                )
                cls.items.append(item)
                cls.item = item

            # Create embedded content library and problem
            cls.content_library = ItemFactory.create(
                parent_location=cls.unit.location,
                category="library_content",
            )
            library_problem = ItemFactory.create(
                parent_location=cls.content_library.location,
                category="problem",
                data=StringResponseXMLFactory().build_xml(answer='foo'),
                display_name=u'test library problem',
            )
            cls.items.append(library_problem)

    def setUp(self):
        super(TestGetProblemGradeDistribution, self).setUp()

        self.request_factory = RequestFactory()
        self.instructor = AdminFactory.create()
        self.client.login(username=self.instructor.username, password='test')
        self.attempts = 3
        self.users = [
            UserFactory.create(username="metric" + str(__))
            for __ in xrange(USER_COUNT)
        ]

        for user in self.users:
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id)

        #  Adding an instructor and a staff to the site.  These should not be included in any reports.
        instructor_member = InstructorFactory(course_key=self.course.id)
        CourseEnrollment.enroll(instructor_member, self.course.id)

        staff_member = StaffFactory(course_key=self.course.id)
        CourseEnrollment.enroll(staff_member, self.course.id)

        for i, item in enumerate(self.items):
            for j, user in enumerate(self.users):
                StudentModuleFactory.create(
                    grade=1 if i < j else 0,
                    max_grade=1,
                    student=user,
                    course_id=self.course.id,
                    module_state_key=item.location,
                    state=json.dumps({'attempts': self.attempts}),
                )

            StudentModuleFactory.create(
                grade=1,
                max_grade=1,
                student=instructor_member,
                course_id=self.course.id,
                module_state_key=item.location,
                state=json.dumps({'attempts': self.attempts}),
            )

            StudentModuleFactory.create(
                grade=1,
                max_grade=1,
                student=staff_member,
                course_id=self.course.id,
                module_state_key=item.location,
                state=json.dumps({'attempts': self.attempts}),
            )

        for j, user in enumerate(self.users):
            StudentModuleFactory.create(
                course_id=self.course.id,
                student=user,
                module_type='sequential',
                module_state_key=self.sub_section.location,
            )

        StudentModuleFactory.create(
            course_id=self.course.id,
            student=instructor_member,
            module_type='sequential',
            module_state_key=self.sub_section.location,
        )

        StudentModuleFactory.create(
            course_id=self.course.id,
            student=staff_member,
            module_type='sequential',
            module_state_key=self.sub_section.location,
        )

    def test_instructor_staff_studentmodules(self):
        non_students = get_non_student_list(self.course.id)
        total_sm_count_problem = StudentModule.objects.filter(module_type='problem', module_state_key=self.item.location).count()
        total_student_sm_count_problem = StudentModule.objects.filter(module_type='problem', module_state_key=self.item.location).exclude(student__id__in=non_students).count()
        self.assertEqual(total_sm_count_problem, USER_COUNT + 2)
        self.assertEqual(total_student_sm_count_problem, USER_COUNT)
        total_sm_count_seq = StudentModule.objects.filter(module_type='sequential', module_state_key=self.sub_section.location).count()
        total_student_sm_count_seq = StudentModule.objects.filter(module_type='sequential', module_state_key=self.sub_section.location).exclude(student__id__in=non_students).count()
        self.assertEqual(total_sm_count_seq, USER_COUNT + 2)
        self.assertEqual(total_student_sm_count_seq, USER_COUNT)

    @override_settings(MAX_ENROLLEES_FOR_METRICS_USING_DB=(USER_COUNT + 1))
    def test_get_problem_grade_distribution_from_db(self):
        prob_grade_distrib, total_student_count = get_problem_grade_distribution(self.course.id, USER_COUNT)

        for problem in prob_grade_distrib:
            max_grade = prob_grade_distrib[problem]['max_grade']
            self.assertEquals(1, max_grade)

        for val in total_student_count.values():
            self.assertEquals(USER_COUNT, val)

    @patch('class_dashboard.dashboard_data.Client')
    @override_settings(MAX_ENROLLEES_FOR_METRICS_USING_DB=(USER_COUNT - 1))
    def test_get_problem_grade_distribution_from_client(self, mock_client):
        mock_client.return_value.modules.return_value.grade_distribution.return_value = [
            {
                'grade': 1,
                'max_grade': 1,
                'count': USER_COUNT,
            },
        ]

        prob_grade_distrib, total_student_count = get_problem_grade_distribution(self.course.id, USER_COUNT)

        for problem in prob_grade_distrib:
            max_grade = prob_grade_distrib[problem]['max_grade']
            self.assertEquals(1, max_grade)

        for val in total_student_count.values():
            self.assertEquals(USER_COUNT, val)

    @override_settings(ANALYTICS_DATA_URL='', MAX_ENROLLEES_FOR_METRICS_USING_DB=(USER_COUNT - 1))
    def test_get_problem_grade_distribution_api_not_set(self):
        prob_grade_distrib, total_student_count = get_problem_grade_distribution(self.course.id, USER_COUNT)

        for problem in prob_grade_distrib:
            max_grade = prob_grade_distrib[problem]['max_grade']
            self.assertEquals(1, max_grade)

        for value in total_student_count.values():
            self.assertEquals(USER_COUNT, value)

    @override_settings(MAX_ENROLLEES_FOR_METRICS_USING_DB=(USER_COUNT + 1))
    def test_get_sequential_open_distibution_from_db(self):
        sequential_open_distrib = get_sequential_open_distrib(self.course.id, USER_COUNT)

        for problem in sequential_open_distrib:
            num_students = sequential_open_distrib[problem]
            self.assertEquals(USER_COUNT, num_students)

    @patch('class_dashboard.dashboard_data.Client')
    @override_settings(MAX_ENROLLEES_FOR_METRICS_USING_DB=(USER_COUNT - 1))
    def test_get_sequential_open_distibution_from_client(self, mock_client):
        mock_client.return_value.modules.return_value.sequential_open_distribution.return_value = [{'count': USER_COUNT}]
        sequential_open_distrib = get_sequential_open_distrib(self.course.id, USER_COUNT)

        for problem in sequential_open_distrib:
            num_students = sequential_open_distrib[problem]
            self.assertEquals(USER_COUNT, num_students)

    @override_settings(ANALYTICS_DATA_URL='', MAX_ENROLLEES_FOR_METRICS_USING_DB=(USER_COUNT - 1))
    def test_get_sequential_open_distibution_api_not_set(self):
        sequential_open_distrib = get_sequential_open_distrib(self.course.id, USER_COUNT)

        for problem in sequential_open_distrib:
            num_students = sequential_open_distrib[problem]
            self.assertEquals(USER_COUNT, num_students)

    @override_settings(MAX_ENROLLEES_FOR_METRICS_USING_DB=(USER_COUNT + 1))
    def test_get_problem_set_grade_distrib_from_db(self):
        prob_grade_distrib, __ = get_problem_grade_distribution(self.course.id, USER_COUNT)
        probset_grade_distrib = get_problem_set_grade_distrib(self.course.id, prob_grade_distrib, USER_COUNT)

        for problem in probset_grade_distrib:
            max_grade = probset_grade_distrib[problem]['max_grade']
            self.assertEquals(1, max_grade)

            grade_distrib = probset_grade_distrib[problem]['grade_distrib']
            sum_attempts = 0
            for item in grade_distrib:
                sum_attempts += item[1]
            self.assertEquals(USER_COUNT, sum_attempts)

    @patch('class_dashboard.dashboard_data.Client')
    @override_settings(MAX_ENROLLEES_FOR_METRICS_USING_DB=(USER_COUNT - 1))
    def test_get_problem_set_grade_distrib_from_client(self, mock_client):
        mock_client.return_value.modules.return_value.grade_distribution.return_value = [
            {
                'grade': 1,
                'max_grade': 1,
                'count': USER_COUNT,
            },
        ]

        prob_grade_distrib, __ = get_problem_grade_distribution(self.course.id, USER_COUNT)
        probset_grade_distrib = get_problem_set_grade_distrib(self.course.id, prob_grade_distrib, USER_COUNT)

        for problem in probset_grade_distrib:
            max_grade = probset_grade_distrib[problem]['max_grade']
            self.assertEquals(1, max_grade)

            grade_distrib = probset_grade_distrib[problem]['grade_distrib']
            sum_attempts = 0
            for item in grade_distrib:
                sum_attempts += item[1]
            self.assertEquals(USER_COUNT, sum_attempts)

    @override_settings(ANALYTICS_DATA_URL='', MAX_ENROLLEES_FOR_METRICS_USING_DB=(USER_COUNT - 1))
    def test_get_problem_set_grade_distrib_api_not_set(self):
        prob_grade_distrib, __ = get_problem_grade_distribution(self.course.id, USER_COUNT)
        probset_grade_distrib = get_problem_set_grade_distrib(self.course.id, prob_grade_distrib, USER_COUNT)

        for problem in probset_grade_distrib:
            max_grade = probset_grade_distrib[problem]['max_grade']
            self.assertEquals(1, max_grade)

            grade_distrib = probset_grade_distrib[problem]['grade_distrib']
            sum_attempts = 0
            for item in grade_distrib:
                sum_attempts += item[1]
            self.assertEquals(USER_COUNT, sum_attempts)

    @patch('class_dashboard.dashboard_data.Client')
    def test_get_d3_problem_grade_distrib(self, mock_client):
        mock_client.return_value.modules.return_value.grade_distribution.return_value = [
            {
                'grade': 1,
                'max_grade': 1,
                'count': USER_COUNT,
            },
        ]

        d3_data = get_d3_problem_grade_distrib(self.course.id, USER_COUNT)
        for data in d3_data:
            for stack_data in data['data']:
                sum_values = 0
                for problem in stack_data['stackData']:
                    sum_values += problem['value']
                self.assertEquals(USER_COUNT, sum_values)

    @patch('class_dashboard.dashboard_data.Client')
    def test_get_d3_sequential_open_distrib(self, mock_client):
        mock_client.return_value.modules.return_value.sequential_open_distribution.return_value = [{'count': 0}]

        d3_data = get_d3_sequential_open_distrib(self.course.id, USER_COUNT)

        for data in d3_data:
            for stack_data in data['data']:
                for problem in stack_data['stackData']:
                    value = problem['value']
                self.assertEquals(USER_COUNT, value)

    @patch('class_dashboard.dashboard_data.Client')
    def test_get_d3_section_grade_distrib(self, mock_client):
        mock_client.return_value.modules.return_value.grade_distribution.return_value = [
            {
                'grade': 1,
                'max_grade': 1,
                'count': USER_COUNT,
            },
        ]

        d3_data = get_d3_section_grade_distrib(self.course.id, 0, USER_COUNT)

        for stack_data in d3_data:
            sum_values = 0
            for problem in stack_data['stackData']:
                sum_values += problem['value']
            self.assertEquals(USER_COUNT, sum_values)

    def test_get_students_problem_grades(self):

        attributes = '?module_id=' + self.item.location.to_deprecated_string() + '&course_id=' + self.course.id.to_deprecated_string()
        request = self.request_factory.get(reverse('get_students_problem_grades') + attributes)

        response = get_students_problem_grades(request)
        response_content = json.loads(response.content)['results']
        response_max_exceeded = json.loads(response.content)['max_exceeded']

        self.assertEquals(USER_COUNT, len(response_content))
        self.assertEquals(False, response_max_exceeded)
        for item in response_content:
            if item['grade'] == 0:
                self.assertEquals(0, item['percent'])
            else:
                self.assertEquals(100, item['percent'])

    def test_get_students_problem_grades_max(self):

        with patch('class_dashboard.dashboard_data.MAX_SCREEN_LIST_LENGTH', 2):
            attributes = '?module_id=' + self.item.location.to_deprecated_string() + '&course_id=' + self.course.id.to_deprecated_string()
            request = self.request_factory.get(reverse('get_students_problem_grades') + attributes)

            response = get_students_problem_grades(request)
            response_results = json.loads(response.content)['results']
            response_max_exceeded = json.loads(response.content)['max_exceeded']

            # Only 2 students in the list and response_max_exceeded is True
            self.assertEquals(2, len(response_results))
            self.assertEquals(True, response_max_exceeded)

    def test_get_students_problem_grades_csv(self):

        tooltip = 'P1.2.1 Q1 - 3382 Students (100%: 1/1 questions)'
        attributes = '?module_id=' + self.item.location.to_deprecated_string() + '&course_id=' + self.course.id.to_deprecated_string() + '&tooltip=' + tooltip + '&csv=true'
        request = self.request_factory.get(reverse('get_students_problem_grades') + attributes)

        response = get_students_problem_grades(request)
        # Check header and a row for each student in csv response
        self.assertContains(response, '"Name","Username","Grade","Percent"')
        self.assertContains(response, '"metric0","0.0","0.0"')
        self.assertContains(response, '"metric1","0.0","0.0"')
        self.assertContains(response, '"metric2","0.0","0.0"')
        self.assertContains(response, '"metric3","0.0","0.0"')
        self.assertContains(response, '"metric4","0.0","0.0"')
        self.assertContains(response, '"metric5","0.0","0.0"')
        self.assertContains(response, '"metric6","0.0","0.0"')
        self.assertContains(response, '"metric7","0.0","0.0"')
        self.assertContains(response, '"metric8","0.0","0.0"')
        self.assertContains(response, '"metric9","0.0","0.0"')
        self.assertContains(response, '"metric10","1.0","100.0"')

    def test_get_students_opened_subsection(self):

        attributes = '?module_id=' + self.sub_section.location.to_deprecated_string() + '&course_id=' + self.course.id.to_deprecated_string()
        request = self.request_factory.get(reverse('get_students_opened_subsection') + attributes)

        response = get_students_opened_subsection(request)
        response_results = json.loads(response.content)['results']
        response_max_exceeded = json.loads(response.content)['max_exceeded']
        self.assertEquals(USER_COUNT, len(response_results))
        self.assertEquals(False, response_max_exceeded)

    def test_get_students_opened_subsection_max(self):

        with patch('class_dashboard.dashboard_data.MAX_SCREEN_LIST_LENGTH', 2):

            attributes = '?module_id=' + self.sub_section.location.to_deprecated_string() + '&course_id=' + self.course.id.to_deprecated_string()
            request = self.request_factory.get(reverse('get_students_opened_subsection') + attributes)

            response = get_students_opened_subsection(request)
            response_results = json.loads(response.content)['results']
            response_max_exceeded = json.loads(response.content)['max_exceeded']

            # Only 2 students in the list and response_max_exceeded is True
            self.assertEquals(2, len(response_results))
            self.assertEquals(True, response_max_exceeded)

    def test_get_students_opened_subsection_csv(self):

        tooltip = '4162 students opened Subsection 5: Relational Algebra Exercises'
        attributes = '?module_id=' + self.sub_section.location.to_deprecated_string() + '&course_id=' + self.course.id.to_deprecated_string() + '&tooltip=' + tooltip + '&csv=true'
        request = self.request_factory.get(reverse('get_students_opened_subsection') + attributes)

        response = get_students_opened_subsection(request)
        self.assertContains(response, '"Name","Username"')
        # Check response contains 1 line for each user +1 for the header
        self.assertEquals(USER_COUNT + 1, len(response.content.splitlines()))

    def test_post_metrics_data_subsections_csv(self):

        url = reverse('post_metrics_data_csv')

        sections = json.dumps(["Introduction"])
        tooltips = json.dumps([[{"subsection_name": "Pre-Course Survey", "subsection_num": 1, "type": "subsection", "num_students": 18963}]])
        course_id = self.course.id
        data_type = 'subsection'

        data = json.dumps({'sections': sections,
                           'tooltips': tooltips,
                           'course_id': course_id.to_deprecated_string(),
                           'data_type': data_type,
                           })

        response = self.client.post(url, {'data': data})
        # Check response contains 1 line for header, 1 line for Section and 1 line for Subsection
        self.assertEquals(3, len(response.content.splitlines()))

    def test_post_metrics_data_problems_csv(self):

        url = reverse('post_metrics_data_csv')

        sections = json.dumps(["Introduction"])
        tooltips = json.dumps([[[
            {'student_count_percent': 0,
             'problem_name': 'Q1',
             'grade': 0,
             'percent': 0,
             'label': 'P1.2.1',
             'max_grade': 1,
             'count_grade': 26,
             'type': u'problem'},
            {'student_count_percent': 99,
             'problem_name': 'Q1',
             'grade': 1,
             'percent': 100,
             'label': 'P1.2.1',
             'max_grade': 1,
             'count_grade': 4763,
             'type': 'problem'},
        ]]])
        course_id = self.course.id
        data_type = 'problem'

        data = json.dumps({'sections': sections,
                           'tooltips': tooltips,
                           'course_id': course_id.to_deprecated_string(),
                           'data_type': data_type,
                           })

        response = self.client.post(url, {'data': data})
        # Check response contains 1 line for header, 1 line for Sections and 2 lines for problems
        self.assertEquals(4, len(response.content.splitlines()))

    def test_get_section_display_name(self):

        section_display_name = get_section_display_name(self.course.id)
        self.assertMultiLineEqual(section_display_name[0], u"test factory section omega \u03a9")

    def test_get_array_section_has_problem(self):

        b_section_has_problem = get_array_section_has_problem(self.course.id)
        self.assertEquals(b_section_has_problem[0], True)

    def test_has_instructor_access_for_class(self):
        """
        Test for instructor access
        """
        ret_val = bool(has_instructor_access_for_class(self.instructor, self.course.id))
        self.assertEquals(ret_val, True)
