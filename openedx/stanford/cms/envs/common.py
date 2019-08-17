from glob import glob

from cms.envs.common import *
from openedx.stanford.lms.envs.common import (
    COURSE_MODE_DEFAULTS,
    DEFAULT_COURSE_ABOUT_IMAGE_URL,
    EXTRA_MIMETYPES,
    INSTRUCTOR_QUERY_PROBLEM_TYPES,
)

STANFORD_ROOT = REPO_ROOT / 'openedx/stanford'

CELERY_IMPORTS = (
    'openedx.stanford.cms.djangoapps.contentstore.views.utilities.tasks',
)
COPYRIGHT_EMAIL = 'copyright@example.com'
COURSE_UTILITIES = [
    # Todo: add aws entries for this
    {
        'short_description': 'Bulk Operations',
        'items': [
            {
                'short_description': 'Get all captions from YouTube',
                'long_description': (
                    'This utility will attempt to get or update captions for all videos '
                    'in the course from YouTube. Please allow it a couple of minutes to run.'
                ),
                'action_url': 'utility_captions_handler',
                'action_text': 'Check Captions',
                'action_external': False,
            },
            {
                'short_description': 'Bulk view problem settings',
                'long_description': (
                    'This utility will allow you to view all section, subsection '
                    'and problem settings in one page.'
                ),
                'action_url': 'utility_bulksettings_handler',
                'action_text': 'View Problem Settings',
                'action_external': False,
            },
        ],
    }
]
FEATURES.update({
    'ALLOW_HIDING_DISCUSSION_TAB': True,
    # Display option to send email confirmation of course enrollment
    'ENABLE_ENROLLMENT_EMAIL': False,
})
INSTALLED_APPS += (
    'openedx.stanford.djangoapps.course_utils',
    'openedx.stanford.djangoapps.student_utils',
    # Added here to allow translations
    'freetextresponse',
    'submit_and_compare',
    'inline_dropdown',
    'xblockmufi',
)
MAKO_TEMPLATE_DIRS_BASE += glob(STANFORD_ROOT / 'djangoapps/*/templates')
MAKO_TEMPLATE_DIRS_BASE += glob(STANFORD_ROOT / 'common/djangoapps/*/templates')
MAKO_TEMPLATE_DIRS_BASE += glob(STANFORD_ROOT / 'cms/djangoapps/*/templates')
MIDDLEWARE_CLASSES += (
    'openedx.stanford.djangoapps.sneakpeek.middleware.SneakPeekLogoutMiddleware',
)
SHIB_ONLY_SITE = False
SHIB_REDIRECT_DOMAIN_WHITELIST = {}
STATICFILES_DIRS += glob(STANFORD_ROOT / 'djangoapps/*/static')
STATICFILES_DIRS += glob(STANFORD_ROOT / 'common/djangoapps/*/static')
STATICFILES_DIRS += glob(STANFORD_ROOT / 'cms/djangoapps/*/static')
XBLOCKS_ALWAYS_IN_STUDIO = []
