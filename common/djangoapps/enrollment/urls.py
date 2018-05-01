"""
URLs for the Enrollment API

"""
from django.conf import settings
from django.conf.urls import patterns, url

from .views import EnrollmentCourseDetailView, EnrollmentListView, EnrollmentView
from .views import EnrollmentCourseRosterView

urlpatterns = patterns(
    'enrollment.views',
    url(
        r'^roster/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
        EnrollmentCourseRosterView.as_view(),
        name='courseenrollmentroster',
    ),
    url(
        r'^enrollment/{username},{course_key}$'.format(
            username=settings.USERNAME_PATTERN, course_key=settings.COURSE_ID_PATTERN
        ),
        EnrollmentView.as_view(),
        name='courseenrollment'
    ),
    url(
        r'^enrollment/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
        EnrollmentView.as_view(),
        name='courseenrollment'
    ),
    url(r'^enrollment$', EnrollmentListView.as_view(), name='courseenrollments'),
    url(
        r'^course/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
        EnrollmentCourseDetailView.as_view(),
        name='courseenrollmentdetails'
    ),
)
