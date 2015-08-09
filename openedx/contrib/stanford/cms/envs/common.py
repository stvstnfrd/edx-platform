# -*- coding: utf-8 -*-
from cms.envs.common import *
from openedx.contrib.stanford.lms.envs.common import ACCOUNT_NAME

# Modulestore to use for new courses
FEATURES['DEFAULT_STORE_FOR_NEW_COURSE'] = None

# Display option to send email confirmation of course enrollment
FEATURES['ENABLE_ENROLLMENT_EMAIL'] = False

FEATURES['ALLOW_COURSE_RERUNS'] = False

############################## Utilities ##########################################

# Todo: add aws entries for this
COURSE_UTILITIES = [
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
    },
]

### SHIB
# For SHIB backup register and login URLs
SHIB_ONLY_SITE = False
SHIB_REDIRECT_DOMAIN_WHITELIST = {}

# XBlock types listed here will _always_ be selectable as Studio components
XBLOCKS_ALWAYS_IN_STUDIO = [
]

MIDDLEWARE_CLASSES += (
    # Log out sneakpeek users
    'sneakpeek.middleware.SneakPeekLogoutMiddleware',
)
