"""
Unit tests for bulk update problem settings utility
"""

import ddt
import mock

from xmodule.modulestore.tests.factories import CourseFactory

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from contentstore.utils import reverse_course_url


SHOW_ANSWER_OPTIONS = [
    'always',
    'answered',
    'attempted',
    'closed',
    'finished',
    'past_due',
    'correct_or_past_due',
    'never'
]

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
        self.course = CourseFactory.create(org='edX', number='test1', display_name='BulkUpdate Course')
        self.bulkupdate_url = reverse_course_url('utility_bulkupdate_handler', self.course.id)

    def test_get_bulkupdate(self):
        """
        Tests the get bulkupdate method and URL expansion
        """
        response = self.client.get(self.bulkupdate_url)
        self.assertContains(response, "Update Problem Settings")
        # Verify expansion of action URL happened.
        self.assertContains(response, '/utility/bulkupdate/edX/test1/BulkUpdate_Course')
        self.assertContains(response, '/utility/bulkupdate_status/edX/test1/BulkUpdate_Course')

    def test_get_bulkupdate_html(self):
        """
        Tests getting the HTML template for the bulkupdate page
        """
        response = self.client.get(self.bulkupdate_url, HTTP_ACCEPT='text/html')
        self.assertContains(response, "Update Problem Settings")
        # The HTML generated will define the handler URL (for use by the Backbone model).
        self.assertContains(response, self.bulkupdate_url)
        # Verify dynamic content populates HTML correctly
        self.assertContains(response, '<input class="input setting-input setting-input-number" type="number" value="0" min="0.0000" step="1">')
        self.assertContains(response, '<option value="always" selected>always</option>')
        self.assertContains(response, '<option value="answered">answered</option>')
        self.assertContains(response, '<option value="attempted">attempted</option>')
        self.assertContains(response, '<option value="closed">closed</option>')
        self.assertContains(response, '<option value="finished">finished</option>')
        self.assertContains(response, '<option value="past_due">past_due</option>')
        self.assertContains(response, '<option value="correct_or_past_due">correct_or_past_due</option>')
        self.assertContains(response, '<option value="never">never</option>')

    def test_bulkupdate_put_unsupported(self):
        """
        Put operation is not supported.
        """
        update_url = reverse_course_url('utility_bulkupdate_handler', self.course.id)
        response = self.client.put(update_url)
        self.assertEqual(response.status_code, 404)

    def test_bulkupdate_delete_unsupported(self):
        """
        Delete operation is not supported.
        """
        update_url = reverse_course_url('utility_bulkupdate_handler', self.course.id)
        response = self.client.delete(update_url)
        self.assertEqual(response.status_code, 404)

    @ddt.data(
        {'maxAttempts': 0, 'showAnswer': SHOW_ANSWER_OPTIONS[0]},
        {'maxAttempts': 1, 'showAnswer': SHOW_ANSWER_OPTIONS[1]}
    )
    def test_post_bulkupdate_two_correct_arguments(self, settings):
        """
        Tests POST operation works given two correct arguments
        """
        update_url = reverse_course_url('utility_bulkupdate_handler', self.course.id)
        print settings
        response = self.client.post(update_url, settings, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

    @ddt.data(
        {'maxAttempts': 0},
        {'showAnswer': SHOW_ANSWER_OPTIONS[0]}
    )
    def test_post_bulkupdate_one_correct_argument(self, settings):
        """
        Tests POST operations works given one correct argument
        """
        update_url = reverse_course_url('utility_bulkupdate_handler', self.course.id)
        print settings
        response = self.client.post(update_url, settings, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)

    @ddt.data(
        {'maxAttempts': -1},
        {'showAnswer': 'invalid_show_answer_option'},
        {'maxAttempts': -1, 'showAnswer': SHOW_ANSWER_OPTIONS[0]},
        {'maxAttempts': 0, 'showAnswer': 'invalid_show_answer_option'},
        {'maxAttempts': -1, 'showAnswer': 'invalid_show_answer_option'}
    )
    def test_post_bulkupdate_incorrect_arguments(self, settings):
        """
        Tests POST operation returns 'invalid setting' 400 code on incorrect arguments
        """
        update_url = reverse_course_url('utility_bulkupdate_handler', self.course.id)
        print settings
        response = self.client.post(update_url, settings, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 400)
