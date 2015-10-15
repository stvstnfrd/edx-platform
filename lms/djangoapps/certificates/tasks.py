# -*- coding: utf-8 -*-
import logging
import lxml.html
from lxml.etree import XMLSyntaxError, ParserError  # pylint:disable=no-name-in-module
import random

from django.test.client import RequestFactory

from capa.xqueue_interface import make_xheader, make_hashkey
from certificates.api import has_html_certificates_enabled
from certificates.models import CertificateStatuses
from certificates.models import CertificateWhitelist
from certificates.models import GeneratedCertificate
from certificates.models import certificate_status_for_student
from certificates.queue import XQueueCertInterface
from courseware import grades
from course_modes.models import CourseMode
from student.models import UserProfile, CourseEnrollment
from verify_student.models import SoftwareSecurePhotoVerification

from openedx_certificates.gen_cert import CertificateGen

LOGGER = logging.getLogger(__name__)
valid_statuses = [
    CertificateStatuses.generating,
    CertificateStatuses.unavailable,
    CertificateStatuses.deleted,
    CertificateStatuses.error,
    CertificateStatuses.notpassing,
    CertificateStatuses.downloadable
]


def request_certificate(
        course,
        student,
        grade=None,
):
    xqueue = XQueueCertInterface()
    generate_pdf = not has_html_certificates_enabled(course.id, course)
    try:
        certificate = GeneratedCertificate.objects.get(
            user=student,
            course_id=course.id,
        )
        LOGGER.info(
            (
                u"Found an existing certificate entry for student %s "
                u"in course '%s' "
                u"with status '%s' while regenerating certificates. "
            ),
            student.id,
            unicode(course.id),
            certificate.status
        )
        certificate.status = CertificateStatuses.unavailable
        certificate.save()
        LOGGER.info(
            (
                u"The certificate status for student %s "
                u"in course '%s' has been changed to '%s'."
            ),
            student.id,
            unicode(course.id),
            certificate.status
        )
    except GeneratedCertificate.DoesNotExist:
        pass
    cert_status = certificate_status_for_student(student, course.id)['status']
    new_status = cert_status
    cert = None
    if cert_status not in valid_statuses:
        LOGGER.warning(
            (
                u"Cannot create certificate generation task for user %s "
                u"in the course '%s'; "
                u"the certificate status '%s' is not one of %s."
            ),
            student.id,
            unicode(course.id),
            cert_status,
            unicode(valid_statuses)
        )
        return new_status, cert
    profile = UserProfile.objects.get(user=student)
    profile_name = profile.name
    course_name = course.display_name or unicode(course.id)
    is_whitelisted = CertificateWhitelist.objects.all().filter(
        user=student,
        course_id=course.id,
        whitelist=True,
    ).exists()
    factory = RequestFactory()
    request = factory.get('/')
    request.user = student
    request.session = {}
    grade = grades.grade(student, request, course)
    enrollment_mode, __ = CourseEnrollment.enrollment_mode_for_user(student, course.id)
    mode_is_verified = enrollment_mode in GeneratedCertificate.VERIFIED_CERTS_MODES
    user_is_verified = SoftwareSecurePhotoVerification.user_is_verified(student)
    cert_mode = enrollment_mode
    course_id = course.id
    if cert_mode == CourseMode.CREDIT_MODE:
        cert_mode = CourseMode.VERIFIED
    if mode_is_verified and user_is_verified:
        template_pdf = "certificate-template-{id.org}-{id.course}-verified.pdf".format(id=course_id)
    elif mode_is_verified and not user_is_verified:
        template_pdf = "certificate-template-{id.org}-{id.course}.pdf".format(id=course_id)
        cert_mode = GeneratedCertificate.MODES.honor
    else:
        # honor code and audit students
        template_pdf = "certificate-template-{id.org}-{id.course}.pdf".format(id=course_id)
    cert, __ = GeneratedCertificate.objects.get_or_create(user=student, course_id=course_id)
    cert.mode = cert_mode
    cert.user = student
    cert.grade = grade['percent']
    cert.course_id = course_id
    cert.name = profile_name
    cert.download_url = ''
    grade_contents = grade.get('grade', None)
    try:
        grade_contents = lxml.html.fromstring(grade_contents).text_content()
    except (TypeError, XMLSyntaxError, ParserError) as exc:
        LOGGER.info(
            (
                u"Could not retrieve grade for student %s "
                u"in the course '%s' "
                u"because an exception occurred while parsing the "
                u"grade contents '%s' as HTML. "
                u"The exception was: '%s'"
            ),
            student.id,
            unicode(course_id),
            grade_contents,
            unicode(exc)
        )
        # Despite blowing up the xml parser, bad values here are fine
        grade_contents = None
    if is_whitelisted or grade_contents is not None:
        if is_whitelisted:
            LOGGER.info(
                u"Student %s is whitelisted in '%s'",
                student.id,
                unicode(course_id),
            )
        restricted = UserProfile.objects.filter(allow_certificate=False)
        if restricted.filter(user=student).exists():
            # check to see whether the student is on the
            # the embargoed country restricted list
            # otherwise, put a new certificate request
            # on the queue
            new_status = status.restricted
            cert.status = new_status
            cert.save()
            LOGGER.info(
                (
                    u"Student %s is in the embargoed country restricted "
                    u"list, so their certificate status has been set to '%s' "
                    u"for the course '%s'. "
                    u"No certificate generation task was sent to the XQueue."
                ),
                student.id,
                new_status,
                unicode(course_id)
            )
        else:
            key = make_hashkey(random.random())
            cert.key = key
            if generate_pdf:
                new_status = CertificateStatuses.generating
            else:
                new_status = CertificateStatuses.downloadable
                cert.verify_uuid = uuid4().hex
            cert.status = new_status
            cert.save()
            if generate_pdf:
                cert2 = CertificateGen(
                    unicode(course_id),
                    template_pdf,
                    # aws_id=args.aws_id,
                    # aws_key=args.aws_key,
                    long_course=course_name.encode('utf-8'),
                    # issued_date=issued_date,
                )
                LOGGER.info(
                    "Generating certificate for {username} ({name}), "
                    "in {course_id}, with grade {grade}".format(
                        username=student.username.encode('utf-8'),
                        name=profile_name,
                        course_id=unicode(course_id),
                        grade=grade,
                    )
                )
                designation = None
                (download_uuid, verify_uuid, download_url) = cert2.create_and_upload(
                    profile_name.encode('utf-8'),
                    grade=grade, designation=designation,
                    upload=False,
                 )
                LOGGER.info(
                    (
                        u"The certificate status has been set to '%s'.  "
                        u"A request has been generated."
                    ),
                    new_status,
                )
    else:
        new_status = CertificateStatuses.notpassing
        cert.status = new_status
        cert.save()
        LOGGER.info(
            (
                u"Student %s does not have a grade for '%s', "
                u"so their certificate status has been set to '%s'. "
                u"No certificate generation task was sent to the XQueue."
            ),
            student.id,
            unicode(course_id),
            new_status
        )
    return new_status, cert
    print(profile_name, course_name, grade, cert_mode)
    return 'womp'
