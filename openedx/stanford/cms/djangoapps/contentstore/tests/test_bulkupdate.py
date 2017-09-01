"""
Unit tests for bulk update problem settings utility
"""

import ddt
import mock

from xmodule.capa_base import CapaFields
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from contentstore.utils import reverse_course_url

from ..views.utilities.tasks import bulk_update_problem_settings


SHOW_ANSWER_OPTIONS = []
for value in CapaFields.__dict__['showanswer'].values:
    SHOW_ANSWER_OPTIONS.append(value['value'])


@ddt.ddt
class BulkUpdateTest(CourseTestCase):
    """
    Test for bulk update get and post methods
    """
    def setUp(self):
        """
        Creates the test course
        """
        super(BulkUpdateTest, self).setUp()
        self.course = CourseFactory.create()
        self.bulkupdate_url = reverse_course_url('utility_bulkupdate_handler', self.course.id)

    def test_get_bulkupdate_html(self):
        """
        Tests getting the HTML template and URLs for the bulkupdate page
        """
        response = self.client.get(self.bulkupdate_url, HTTP_ACCEPT='text/html')
        self.assertContains(response, '/course/{}'.format(self.course.id))
        self.assertContains(response, '/utility/bulkupdate/{}'.format(self.course.id))
        # Verify dynamic content populates HTML correctly
        self.assertContains(
            response,
            '<input class="input setting-input setting-input-number" type="number" value="0" min="0.0000" step="1">'
        )
        self.assertContains(response, '<option value="always" selected>always</option>')
        for option in SHOW_ANSWER_OPTIONS[1:]:
            self.assertContains(response, '<option value="{}">{}</option>'.format(option, option))

    def test_bulkupdate_put_unsupported(self):
        """
        Put operation is not supported.
        """
        response = self.client.put(self.bulkupdate_url)
        self.assertEqual(response.status_code, 404)

    def test_bulkupdate_delete_unsupported(self):
        """
        Delete operation is not supported.
        """
        response = self.client.delete(self.bulkupdate_url)
        self.assertEqual(response.status_code, 404)

    @ddt.data(
        {'maxAttempts': 0, 'showAnswer': ''},
        {'maxAttempts': '', 'showAnswer': SHOW_ANSWER_OPTIONS[0]},
        {'maxAttempts': 0, 'showAnswer': SHOW_ANSWER_OPTIONS[0]},
        {'maxAttempts': 1, 'showAnswer': SHOW_ANSWER_OPTIONS[1]},
    )
    def test_post_bulkupdate_correct_arguments(self, settings):
        """
        Tests POST operation returns 200
        """
        response = self.client.post(self.bulkupdate_url, settings, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

    @ddt.data(
        {'maxAttempts': -1},
        {'maxAttempts': -1, 'showAnswer': ''},
        {'maxAttempts': 'not_a_number', 'showAnswer': ''},
        {'showAnswer': 'invalid_show_answer_option'},
        {'maxAttempts': '', 'showAnswer': 'invalid_show_answer_option'},
        {'maxAttempts': -1, 'showAnswer': SHOW_ANSWER_OPTIONS[0]},
        {'maxAttempts': 0, 'showAnswer': 'invalid_show_answer_option'},
        {'maxAttempts': -1, 'showAnswer': 'invalid_show_answer_option'},
    )
    def test_post_bulkupdate_incorrect_arguments(self, settings):
        """
        Tests POST operation returns 'invalid setting' 400 code on incorrect arguments
        """
        response = self.client.post(self.bulkupdate_url, settings, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 400)

    @ddt.data(
        {'maxAttempts': 0, 'showAnswer': ''},
        {'maxAttempts': '', 'showAnswer': SHOW_ANSWER_OPTIONS[0]},
        {'maxAttempts': 0, 'showAnswer': SHOW_ANSWER_OPTIONS[0]},
        {'maxAttempts': 1, 'showAnswer': SHOW_ANSWER_OPTIONS[1]},
    )
    @mock.patch(
        'openedx.stanford.cms.djangoapps.contentstore.views.utilities.bulkupdate.bulk_update_problem_settings.delay',
        side_effect=bulk_update_problem_settings
    )
    def test_bulkupdate_advanced_settings_modified(self, settings, bulk_update_non_celery_task):  #pylint: disable=unused-argument
        """
        Tests course is updated
        """
        response = self.client.post(self.bulkupdate_url, settings, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

        store = modulestore()
        course = store.get_course(self.course.id, 3)
        if settings['maxAttempts']:
            self.assertEquals(getattr(course, 'max_attempts'), settings['maxAttempts'])  # TODO fix pylint: literal-used-as-attribute
        if settings['showAnswer']:
            self.assertEquals(getattr(course, 'showanswer'), settings['showAnswer'])  # TODO fix pylint: literal-used-as-attribute

    @ddt.data(
        {'maxAttempts': 0, 'showAnswer': ''},
        {'maxAttempts': '', 'showAnswer': SHOW_ANSWER_OPTIONS[0]},
        {'maxAttempts': 0, 'showAnswer': SHOW_ANSWER_OPTIONS[0]},
        {'maxAttempts': 1, 'showAnswer': SHOW_ANSWER_OPTIONS[1]},
    )
    @mock.patch(
        'openedx.stanford.cms.djangoapps.contentstore.views.utilities.bulkupdate.bulk_update_problem_settings.delay',
        side_effect=bulk_update_problem_settings
    )
    def test_bulkupdate_problem_settings_modified(self, settings, bulk_update_non_celery_task):  #pylint: disable=unused-argument
        """
        Tests course is updated
        """
        response = self.client.post(self.bulkupdate_url, settings, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

        store = modulestore()

        problems = store.get_items(
            self.course.id,
            qualifiers={"category": 'problem'},
        )
        for problem in problems:
            if settings['maxAttempts']:
                self.assertEquals(getattr(problem, 'max_attempts'), settings['maxAttempts'])  # TODO fix pylint: literal-used-as-attribute
            if settings['showAnswer']:
                self.assertEquals(getattr(problem, 'showanswer'), settings['showAnswer'])  # TODO fix pylint: literal-used-as-attribute
