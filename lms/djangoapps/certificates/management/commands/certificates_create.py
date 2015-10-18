# -*- coding: utf-8 -*-
"""
Generate a certificate for a user
"""

import logging
from optparse import make_option

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.modulestore.django import modulestore

from certificates.models import BadgeAssertion
from certificates.tasks import request_certificate

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    help = __doc__
    option_list = BaseCommand.option_list + (
        make_option(
            '-c',
            '--course-id',
            dest='course_id',
            default=None,
            help=(
                u'The course for which the certifcate should be requested'
            ),
        ),
        make_option(
            '-u',
            '--user',
            dest='username_and_or_email',
            help=(
                u'The username or email address for whom certification should be requested'
            ),
        ),
        make_option(
            '-g',
            '--grade',
            dest='grade',
            default=None,
            help=(
                u'The grade string, such as "Distinction", '
                u'which should be passed to the certificate agent'
            ),
        ),
        make_option(
            '-n',
            '--noop',
            dest='noop',
            action='store_true',
            default=False,
            help=(
                u"Don't actually request certificate creation"
            ),
        ),
    )

    def handle(self, *args, **options):
        print(type('hi'))
        course = _get_course(options['course_id'])
        users = _get_users(options['username_and_or_email'], course)
        noop = options['noop']
        for user in users:
            LOGGER.info(
                u"Requesting certificate "
                u"for user %s in course '%s'...",
                user.id,
                unicode(course.id),
            )
            if not noop:
                result = request_certificate(
                    course,
                    user,
                    grade=options['grade'],
                )
                LOGGER.info(
                    (
                        u"Requested certificate "
                        u"for user %s in course '%s' (status=%s)."
                    ),
                    user.id,
                    unicode(course.id),
                    result,
                )


def _delete_badge(user, course):
    try:
        badge = BadgeAssertion.objects.get(
            user=user,
            course_id=unicode(course.id),
        )
        badge.delete()
        LOGGER.info(
            u"Cleared badge for user %s.",
            user.id,
        )
    except BadgeAssertion.DoesNotExist:
        LOGGER.debug(
            u"No badge to delete for user '%s' in course '%s'",
            user,
            course,
        )


def _get_course(course_id):
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


def _get_users(username_and_or_email, course):
    if username_and_or_email is None:
        users = User.objects.filter(
            courseenrollment__course_id=course.id,
        )
        for user in users:
            yield user
    elif '@' in username_and_or_email:
        yield User.objects.get(email=username_and_or_email)
    else:
        yield User.objects.get(username=username_and_or_email)
