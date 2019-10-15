from django.conf import settings
from django.conf.urls import url

import contentstore.views
from openedx.stanford.cms.djangoapps.contentstore.views import utility
from openedx.stanford.cms.djangoapps.contentstore.views.utilities import bulksettings
from openedx.stanford.cms.djangoapps.contentstore.views.utilities import bulkupdate
from openedx.stanford.cms.djangoapps.contentstore.views.utilities import captions


urlpatterns = [
    url(
        r'^settings/send_test_enrollment_email/{}$'.format(settings.COURSE_KEY_PATTERN),
        contentstore.views.send_test_enrollment_email,
        name='send_test_enrollment_email',
    ),
    url(
        r'^utilities/{}$'.format(settings.COURSE_KEY_PATTERN),
        utility.utility_handler,
        name='utility_handler',
    ),
    url(
        r'^utility/captions/{}$'.format(settings.COURSE_KEY_PATTERN),
        captions.utility_captions_handler,
        name='utility_captions_handler',
    ),
    url(
        r'^utility/bulksettings/{}$'.format(settings.COURSE_KEY_PATTERN),
        bulksettings.utility_bulksettings_handler,
        name='utility_bulksettings_handler',
    ),
    url(
        r'^utility/bulkupdate/{}$'.format(
            settings.COURSE_KEY_PATTERN,
        ),
        bulkupdate.utility_bulkupdate_handler,
        name='utility_bulkupdate_handler',
    ),
]
if settings.SHIB_ONLY_SITE:
    urlpatterns += [
        url(
            r'^backup_signup$',
            contentstore.views.signup,
            name='backup_signup',
        ),
        url(
            r'^backup_signin$',
            contentstore.views.login_page,
            name='backup_login',
        ),
    ]
