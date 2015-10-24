# -*- coding: utf-8 -*-
"""
Generate a certificate for a user
"""

from __future__ import unicode_literals

import logging
from optparse import make_option

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.modulestore.django import modulestore

from certificates.models import BadgeAssertion
from certificates.models import CertificateWhitelist
from certificates.tasks import request_certificate

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Request certificates for users in a course
    """
    help = __doc__
    option_list = BaseCommand.option_list + (
        make_option(
            '-c',
            '--course-id',
            default=None,
            dest='course_id',
            help=(
                'The course for which the certifcate should be requested'
            ),
        ),
        make_option(
            '-u',
            '--user',
            default=None,
            dest='username_or_email',
            help=(
                'The username or email address for whom certification should be requested'
            ),
        ),
        make_option(
            '-g',
            '--grade',
            default=True,
            dest='grade',
            help=(
                'The grade string, such as "Distinction", '
                'which should be passed to the certificate agent'
            ),
        ),
        make_option(
            '-w',
            '--whitelist-add',
            action='store_true',
            default=True,
            dest='whitelist',
            help=(
                "Add to whitelist before requesting certificate"
            ),
        ),
        make_option(
            '-W',
            '--whitelist-remove',
            action='store_false',
            default=None,
            dest='whitelist',
            help=(
                "Remove from whitelist before requesting certificate"
            ),
        ),
        make_option(
            '-n',
            '--noop',
            action='store_true',
            dest='noop',
            help=(
                "Don't actually request certificate creation"
            ),
        ),
        make_option(
            '-s',
            '--status',
            default=None,
            dest='status',
            help=(
                "Don't actually request certificate creation"
            ),
        ),
    )

    def handle(self, *args, **options):
        """
        Attempt to request certificates for users in a course
        """
        course = _get_course(options['course_id'])
        users = _get_users(options['username_or_email'], course)
        noop = options['noop']
        grade = options['grade']
        should_whitelist = options['whitelist']
        status = options['status']
        for user in users:
            _whitelist(user, course, noop, should_whitelist)
            _request_certificate(user, course, noop, grade)
            _delete_badge(user, course, noop)


def _delete_badge(user, course, noop):
    """
    Delete badges for a user in a given course
    """
    LOGGER.debug(
        "Deleting badge: "
        "user_id=%s, course_id='%s'",
        user.id,
        course.id,
    )
    try:
        badge = BadgeAssertion.objects.get(
            user=user,
            course_id=course.id,
        )
        if not noop:
            badge.delete()
        LOGGER.info(
            "Cleared badge: "
            "user_id=%s, course_id='%s', "
            "badge_id=%s",
            user.id,
            course.id,
            badge.id,  # TODO: is this correct?
        )
    except BadgeAssertion.DoesNotExist:
        LOGGER.debug(
            "No badge to delete: "
            "user_id=%s, course_id='%s'",
            user.id,
            course.id,
        )


def _get_course(course_id):
    """
    Get the course for which to generate certificates
    """
    if not course_id:
        raise CommandError('You must specify a course identifier.')
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    course = modulestore().get_course(course_key, depth=2)
    if not course:
        raise CommandError('No course found')
    return course


def _get_users(username_or_email, course):
    """
    Get a list of users for whom to request certificates

    If no user is specified, all users enrolled in the course will be yielded.
    """
    if username_or_email is None:
        users = User.objects.filter(
            courseenrollment__course_id=course.id,
        )
        for user in users:
            yield user
    elif '@' in username_or_email:
        yield User.objects.get(email=username_or_email)
    else:
        yield User.objects.get(username=username_or_email)


def _request_certificate(user, course, noop, grade):
    """
    Request a certificate for a user in a given course
    """
    LOGGER.debug(
        "Requesting certificate: "
        "user_id=%s, course_id='%s'",
        user.id,
        unicode(course.id),
    )
    status = "'noop'"
    if not noop:
        status = request_certificate(
            course,
            user,
            grade=grade,
        )
    LOGGER.info(
        (
            "Requested certificate: "
            "user_id=%s, course_id='%s', "
            "status=%s"
        ),
        user.id,
        unicode(course.id),
        status,
    )


def _whitelist(user, course, noop, should_whitelist):
    """
    Add/remove user to/from whitelist for a given course
    """
    LOGGER.debug(
        "Adding to whitelist: "
        "user_id=%s, course_id='%s'"
        "noop=%s, whitelist=%s",
        user.id,
        course.id,
        noop,
        should_whitelist,
    )
    if should_whitelist is not None:
        whitelist, _created = CertificateWhitelist.objects.get_or_create(
            user=user,
            course_id=course.id,
        )
        whitelist.whitelist = should_whitelist
        whitelist.save()
        LOGGER.info(
            "Added to whitelist: "
            "user_id=%s, course_id='%s'"
            "noop=%s, whitelist=%s",
            user.id,
            course.id,
            noop,
            should_whitelist,
        )
