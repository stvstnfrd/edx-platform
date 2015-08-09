from django.conf import settings
from django.conf.urls import url
urlpatterns = tuple()

if settings.FEATURES.get('ENABLE_SUPERUSER_LOGIN_AS'):
    urlpatterns += (
        url(
            r'^su_login_as/(?P<username>[\w.@+-]+)/?$',
            'student.views.superuser_login_as',
            name='impersonate',
        ),
    )

if settings.COURSEWARE_ENABLED:
    urlpatterns += (
        url(
            r'^get_analytics_answer_dist/',
            'courseware.views.get_analytics_answer_dist',
            name='get_analytics_answer_dist',
        ),
        url(
            r"^course_sneakpeek/{course_id}/$".format(
                course_id=settings.COURSE_ID_PATTERN,
            ),
            'student.views.setup_sneakpeek',
            name='course_sneakpeek',
        ),
    )

if settings.SHIB_ONLY_SITE:
    urlpatterns += (
        url(
            r'^backup_login$',
            'student.views.signin_user',
            name='backup_signin_user',
        ),
        url(
            r'^backup_register$',
            'student.views.register_user',
            name='backup_register_user',
        ),
    )
