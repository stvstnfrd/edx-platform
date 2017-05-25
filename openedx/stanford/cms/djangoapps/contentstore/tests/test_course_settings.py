import mock
from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from milestones.tests.utils import MilestonesTestCaseMixin


def get_url(course_id, handler_name='settings_handler'):
    return reverse_course_url(handler_name, course_id)


@ddt.ddt
class AboutSidebarHtmlViewTest(CourseTestCase, MilestonesTestCaseMixin):
    def test_update_and_fetch(self):
        SelfPacedConfiguration(enabled=True).save()
        details = CourseDetails.fetch(self.course.id)
        # resp s/b json from here on
        url = get_url(self.course.id)
        resp = self.client.get_json(url)
        self.compare_details_with_encoding(json.loads(resp.content), details.__dict__, "virgin get")
        utc = UTC()
        self.alter_field(url, details, 'about_sidebar_html', "About Sidebar HTML")

    def compare_details_with_encoding(self, encoded, details, context):
        """
        compare all of the fields of the before and after dicts
        """
        self.assertEqual(
            details['about_sidebar_html'], encoded['about_sidebar_html'], context + " about_sidebar_html not =="
        )

    @override_settings(MKTG_URLS={'ROOT': 'dummy-root'})
    def test_marketing_site_fetch(self):
        settings_details_url = get_url(self.course.id)
        with mock.patch.dict('django.conf.settings.FEATURES', {
            'ENABLE_MKTG_SITE': True,
            'ENTRANCE_EXAMS': False,
            'ENABLE_PREREQUISITE_COURSES': False
        }):
            response = self.client.get_html(settings_details_url)
            self.assertNotContains(response, "Course About Sidebar HTML")

    def test_regular_site_fetch(self):
        settings_details_url = get_url(self.course.id)
        with mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': False,
                                                               'ENABLE_EXTENDED_COURSE_DETAILS': True}):
            response = self.client.get_html(settings_details_url)
            self.assertContains(response, "Course About Sidebar HTML")
