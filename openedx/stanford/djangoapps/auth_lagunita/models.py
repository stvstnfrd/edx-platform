# -*- coding: utf-8 -*-
"""
Record extra lagunita-centric user data
"""
from __future__ import unicode_literals
import logging

from django.conf import settings
from django.db import models
from django.db.models import Q
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import CourseEnrollment

log = logging.getLogger('auth_lagunita')
USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class Info(models.Model):
    """
    Record extra fields that will be saved when a user registers

    requested_marketing_optin: Track whether user has requested to
        receive additional marketing messages
    submitted_marketing_optin: Track whether system has submitted an
        opt-in for user to receive additional marketing messages
    """
    user = models.OneToOneField(
        USER_MODEL,
    )
    requested_marketing_optin = models.BooleanField(
        default=False,
    )
    submitted_marketing_optin = models.BooleanField(
        default=False,
    )
    created_date = models.DateTimeField(
        auto_now_add=True,
    )
    modified_date = models.DateTimeField(
        auto_now=True,
    )

    class Meta(object):
        app_label = 'openedx.stanford.djangoapps.auth_lagunita'
        db_table = 'auth_lagunita_info'

    def __unicode__(self):
        message = (
            "Info.objects.get("
            "user__email='{email}', "
            "requested_marketing_optin={requested_marketing_optin}, "
            "submitted_marketing_optin={submitted_marketing_optin}"
            ")"
        ).format(
            email=self.user.email,
            requested_marketing_optin=self.requested_marketing_optin,
            submitted_marketing_optin=self.submitted_marketing_optin,
        )
        return message

    @classmethod
    def need_subscribed(cls, blacklist_organizations=None, blacklist_courses=None):
        """
        Return a filtered list of users pending subscription to marketing list
        """
        blacklist = _get_blacklisted_courses(blacklist_organizations, blacklist_courses)
        infos = cls.objects.filter(
            requested_marketing_optin=True,
            submitted_marketing_optin=False,
            user__is_active=True,
        )
        infos = infos.exclude(
            Q(user__email='') |
            Q(user__email=None) |
            Q(user__email__endswith='@example.com') |
            Q(user__email__endswith='.example.com')
        )
        for info in infos:
            if info.is_enrolled_in_any(blacklist):
                log.info("Subscription blacklisted for user=%s", info.user.email)
            else:
                yield info

    def is_enrolled_in_any(self, courses):
        """
        Check if user is enrolled in any of the specified courses
        """
        is_enrolled = CourseEnrollment.objects.filter(
            user_id=self.user_id,
            course_id__in=courses,
        ).exists()
        return is_enrolled


def _get_blacklisted_courses(organizations=None, course_ids=None):
    """
    Fetch a list of all blacklisted courses
    """
    organizations = organizations or []
    course_ids = course_ids or []
    blacklist_by_organization = CourseOverview.objects.filter(
        org__in=organizations,
    )
    blacklist_by_organization = [
        course.id
        for course in blacklist_by_organization
    ]
    blacklist_by_course_id = [
        CourseKey.from_string(course_id)
        for course_id in course_ids
    ]
    blacklist = blacklist_by_organization + blacklist_by_course_id
    return blacklist
