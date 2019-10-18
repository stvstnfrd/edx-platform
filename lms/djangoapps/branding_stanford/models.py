"""
Model for branding_stanford

This was implemented initially so that the list of course tiles could be
stored in this model.
"""
from django.conf import settings
from django.db import models

from config_models.models import ConfigurationModel
from opaque_keys.edx.django.models import CourseKeyField
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class TileConfiguration(ConfigurationModel):
    """
        Stores a list of tiles presented on the front page.
    """
    site = models.CharField(max_length=32, default='default', blank=False)
    course_id = CourseKeyField(max_length=255, db_index=True)

    class Meta(ConfigurationModel.Meta):
        app_label = 'branding_stanford'

    def __unicode__(self):
        return u"{0} {1} {2}".format(self.site, self.course_id, self.enabled)


def get_visible_courses(org=None, filter_=None):
    """
    Get list of visible course tiles
    """
    if not settings.DISPLAY_COURSE_TILES:
        return []
    orgs = []
    if org:
        orgs.append(org)
    filtered_by_db = TileConfiguration.objects.filter(
        enabled=True,
    ).values('course_id').order_by('-change_date')
    courses = None
    if filtered_by_db:
        filtered_by_db_keys = frozenset([
            course['course_id']
            for course in filtered_by_db
        ])
        courses = CourseOverview.get_all_courses(orgs=orgs, filter_=None)
        courses = [
            course
            for course in courses
            if course.id in filtered_by_db_keys
        ]
    return courses
