# -*- coding: utf-8 -*-
"""
TODO: Update this
"""
from __future__ import unicode_literals
from datetime import datetime
import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from ...lib import get_all_course_overviews


log = logging.getLogger('recurring_reports')


class Command(BaseCommand):
    """
    TODO: Update this
    """
    help = __doc__

    blacklist_organizations = []
    blacklist_courses = []
    verbosity = None

    def add_arguments(self, parser):
        parser.add_argument(
            '-b',
            '--blacklist-organization',
            help='Set one or more Course Organizations to "blacklist" and exclude their courses',
            action='append',
            dest='blacklist_organizations',
        )
        parser.add_argument(
            '-B',
            '--blacklist-course',
            help='Set one or more Course IDs to "blacklist" and exclude the courses',
            action='append',
            dest='blacklist_courses',
        )

    def _initialize_settings(self, **kwargs):
        """
        Parse and assign settings from CLI
        """
        self.blacklist_organizations = kwargs['blacklist_organizations']
        self.blacklist_courses = kwargs['blacklist_courses']
        self.verbosity = kwargs['verbosity']

    def _set_logging_verbosity(self):
        """
        Toggle verbosity via CLI
        """
        if not self.verbosity:
            log.setLevel(logging.ERROR)
        elif self.verbosity == 1:
            log.setLevel(logging.INFO)
        else:
            log.setLevel(logging.DEBUG)

    def handle(self, *args, **kwargs):
        self._initialize_settings(**kwargs)
        self._set_logging_verbosity()
        header = _get_header_row()
        self.output_row(header)
        rows = self.get_rows()
        for row in rows:
            self.output_row(row)

    def output_row(self, row):
        self.stdout.write("CSV: {0}".format(row))

    def get_rows(self):
        courses = get_all_course_overviews(self.blacklist_organizations, self.blacklist_courses)
        for course in courses:
            log.debug("course: %s", course)
            row = self.get_row(course)
            yield row

    def get_row(self, course):
        school = course.org
        course_number = course.id.offering.split('/')[0]
        course_run = course.id.run
        visibility = 'public'
        if course.invitation_only:
            visibility = 'private'
        status = 'ongoing'
        # TODO: can't compare between timezone-aware and timezone-naive
        # if course.end and course.end < datetime.now():
        #     status = 'archived'
        course_title = course.display_name
        start_date = course.start
        # TODO: pull the URL from settings: LMS_BASE?
        course_link = "https://lagunita.stanford.edu/courses/{course_id}".format(
            course_id=course.id,
        )
        course_team = 'TODO'
        count_enrollment_winter = 0  # TODO
        count_enrollment_spring = 0  # TODO
        count_enrollment_summer = 0  # TODO
        count_enrollment_fall = 0  # TODO
        count_enrollment_ytd = 0  # TODO
        count_enrollment_total = 0  # TODO
        count_enrollment_anonymous = 0  # TODO
        count_soa_winter = 0  # TODO
        count_soa_spring = 0  # TODO
        count_soa_summer = 0  # TODO
        count_soa_fall = 0  # TODO
        count_soa_ytd = 0  # TODO
        count_soa_total = 0  # TODO
        row = (
            school,
            course_number,
            course_run,
            visibility,
            status,
            course_title,
            start_date,
            course_link,
            course_team,
            count_enrollment_winter,
            count_enrollment_spring,
            count_enrollment_summer,
            count_enrollment_fall,
            count_enrollment_ytd,
            count_enrollment_total,
            count_enrollment_anonymous,
            count_soa_winter,
            count_soa_spring,
            count_soa_summer,
            count_soa_fall,
            count_soa_ytd,
            count_soa_total,
        )
        return row


def _get_header_row():
    row = (
        'school',
        'course_number',
        'course_run',
        'visibility',
        'status',
        'course_title',
        'start_date',
        'course_link',
        'course_team',
        'count_enrollment_winter',
        'count_enrollment_spring',
        'count_enrollment_summer',
        'count_enrollment_fall',
        'count_enrollment_ytd',
        'count_enrollment_total',
        'count_enrollment_anonymous',
        'count_soa_winter',
        'count_soa_spring',
        'count_soa_summer',
        'count_soa_fall',
        'count_soa_ytd',
        'count_soa_total',
    )
    return row
