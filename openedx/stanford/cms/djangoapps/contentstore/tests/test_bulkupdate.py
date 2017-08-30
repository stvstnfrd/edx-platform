"""
Unit tests for bulk update problem settings utility
"""

import ddt

from xmodule.modulestore.tests.factories import CourseFactory

from opaque_keys.edx.keys import CourseKey

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from contentstore.utils import reverse_course_url

from ..views.utilities.bulkupdate import utility_bulkupdate_handler, SHOW_ANSWER_OPTIONS


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

    def check_modified_advanced_settings(self, settings):
        """
        Helper for test cases to check advanced advanced settings have been modified
        """
        if settings['maxAttempts'] != 'null':
            self.assertEquals(getattr(self.course, 'max_attempts'), settings['maxAttempts'])
        if settings['showAnswer'] != 'null':
            self.assertEquals(getattr(self.course, 'showanswer'), settings['showAnswer'])

    def test_get_bulkupdate_html(self):
        """
        Tests getting the HTML template and URLs for the bulkupdate page
        """
        response = self.client.get(self.bulkupdate_url, HTTP_ACCEPT='text/html')
        self.assertContains(response, '/course/'.format(self.course.id))
        self.assertContains(response, '/utility/bulkupdate/'.format(self.course.id))
        self.assertContains(response, '/utility/bulkupdate_status/'.format(self.course.id))
        # Verify dynamic content populates HTML correctly
        self.assertContains(response, '<input class="input setting-input setting-input-number" type="number" value="0" min="0.0000" step="1">')
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
        {'maxAttempts': 0, 'showAnswer': 'null'},
        {'maxAttempts': 'null', 'showAnswer': SHOW_ANSWER_OPTIONS[0]},
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
        {'maxAttempts': -1, 'showAnswer': 'null'},
        {'maxAttempts': 'not_a_number', 'showAnswer': 'null'},
        {'showAnswer': 'invalid_show_answer_option'},
        {'maxAttempts': 'null', 'showAnswer': 'invalid_show_answer_option'},
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
