from django.conf import settings
from django.conf.urls import url


urlpatterns = tuple()

if settings.SHIB_ONLY_SITE:
    urlpatterns += (
        url(
            r'^backup_signup$',
            'contentstore.views.signup',
            name='backup_signup',
        ),
        url(
            r'^backup_signin$',
            'contentstore.views.login_page',
            name='backup_login',
        ),
    )

urlpatterns += (
    url(
        r'^settings/send_test_enrollment_email/{}$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        'send_test_enrollment_email',
        name='send_test_enrollment_email',
    ),
    url(
        r'^utilities/{}$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        'utility_handler',
    ),
    url(
        r'^utility/captions/{}$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        'utility_captions_handler',
    ),
    url(
        r'^utility/bulksettings/{}$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        'utility_bulksettings_handler',
    ),
)
