"""
URLs for the Enrollment API

"""
from django.conf import settings
<<<<<<< HEAD
from django.conf.urls import include
from django.conf.urls import patterns, url
=======
from django.conf.urls import url
>>>>>>> 7ad437b52cb5b2d65ab1b65e6147bcced05c42e4

from .views import EnrollmentCourseDetailView, EnrollmentListView, EnrollmentView, UnenrollmentView

urlpatterns = [
    url(r'^enrollment/{username},{course_key}$'.format(
        username=settings.USERNAME_PATTERN,
        course_key=settings.COURSE_ID_PATTERN),
        EnrollmentView.as_view(), name='courseenrollment'),
    url(r'^enrollment/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
        EnrollmentView.as_view(), name='courseenrollment'),
    url(r'^enrollment$', EnrollmentListView.as_view(), name='courseenrollments'),
<<<<<<< HEAD
    url(
        r'^course/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
        EnrollmentCourseDetailView.as_view(),
        name='courseenrollmentdetails'
    ),
)
urlpatterns += (
    url(r'', include('openedx.stanford.common.djangoapps.enrollment.urls')),
)
=======
    url(r'^course/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
        EnrollmentCourseDetailView.as_view(), name='courseenrollmentdetails'),
    url(r'^unenroll/$', UnenrollmentView.as_view(), name='unenrollment'),
]
>>>>>>> 7ad437b52cb5b2d65ab1b65e6147bcced05c42e4
