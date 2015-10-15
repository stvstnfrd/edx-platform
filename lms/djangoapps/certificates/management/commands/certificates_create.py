"""
Generate a certificate for a user
"""

import logging
import copy
from optparse import make_option
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.modulestore.django import modulestore
from certificates.models import BadgeAssertion
from certificates.api import regenerate_user_certificates
from certificates.tasks import request_certificate


from openedx_certificates.gen_cert import CertificateGen

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
                'The course for which the certifcate should be requested'
            ),
        ),
        make_option(
            '-u',
            '--user',
            dest='user',
            default=None,
            help=(
                'The username or email address for whom certification should be requested'
            ),
        ),
        make_option(
            '-g',
            '--grade',
            dest='grade',
            default=None,
            help=(
                'The grade string, such as "Distinction", '
                'which should be passed to the certificate agent'
            ),
        ),
    )

    def handle(self, *args, **options):
        if not options['course_id']:
            raise CommandError("You must specify a course")

        # Scrub the username from the log message
        cleaned_options = copy.copy(options)
        if 'user' in cleaned_options:
            cleaned_options['user'] = '<USERNAME>'
        LOGGER.info(
            (
                u"Starting to create tasks to regenerate certificates "
                u"with arguments %s and options %s"
            ),
            unicode(args),
            unicode(cleaned_options)
        )

        course_id = options['course_id']
        try:
            course_id = CourseKey.from_string(course_id)
        except InvalidKeyError:
            LOGGER.warning(
                (
                    u"Course id %s could not be parsed as a CourseKey; "
                    u"falling back to SlashSeparatedCourseKey.from_deprecated_string()"
                ),
                course_id,
            )
            course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        course = modulestore().get_course(course_id, depth=2)

        if not course:
            raise CommandError("No course found")

        user = options['user']
        if user:
            if '@' in user:
                enrolled_students = [
                    User.objects.get(email=user),
                ]
            else:
                enrolled_students = [
                    User.objects.get(username=user),
                ]
        else:
            enrolled_students = User.objects.filter(
                courseenrollment__course_id=course.id,
            )

        for student in enrolled_students:
            LOGGER.info(
                u"Requesting certificate for student %s in course '%s'",
                student.id,
                course_id,
            )
            result = request_certificate(
                course,
                student,
                grade=options['grade'],
            )
            try:
                badge = BadgeAssertion.objects.get(
                    user=student,
                    course_id=course_id,
                )
                badge.delete()
                LOGGER.info(
                    u"Cleared badge for student %s.",
                    student.id,
                )
            except BadgeAssertion.DoesNotExist:
                pass
            LOGGER.info(
                (
                    u"Added a certificate regeneration task to the XQueue "
                    u"for student %s in course '%s'. "
                    u"The new certificate status is '%s'."
                ),
                student.id,
                unicode(course_id),
                result,
            )
