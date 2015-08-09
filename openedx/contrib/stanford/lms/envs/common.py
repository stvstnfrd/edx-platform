# -*- coding: utf-8 -*-
from lms.envs.common import *


ACCOUNT_NAME = "Your Account Name Here"

# Email to give anonymous users.  Should be a black-hole email address, but not cause errors when email is sent there
# This is actually just a base email.  We'll make it 'noreply+<username>@example.com' to ensure uniqueness
ANONYMOUS_USER_EMAIL = 'noreply@example.com'

#### Help Modal Links ####
# List of dict objects representing links
# For example:
# HELP_MODAL_LINKS = [
#     {'url': 'https://help.com', 'text': 'How to register an account'}
# ]
HELP_MODAL_LINKS = []

######################### VISIBLE SETTINGS ###########################
# These settings' values will be exposed to all templates
TEMPLATE_VISIBLE_SETTINGS = [
    'FEATURES',
]

############################### CHAT ################################
JABBER = {}
DATABASE_ROUTERS = []

#################### Student Responses Reports Downloads #################
STUDENT_RESPONSES_DOWNLOAD_ROUTING_KEY = HIGH_MEM_QUEUE

STUDENT_RESPONSES_DOWNLOAD = {
    'STORAGE_TYPE': 'localfs',
    'BUCKET': 'edx-student-responses',
    'ROOT_PATH': '/tmp/edx-s3/student-responses',
}

##################### ORA2 Responses Download #######################
ORA2_RESPONSES_DOWNLOAD_ROUTING_KEY = HIGH_MEM_QUEUE

ORA2_RESPONSES_DOWNLOAD = {
    'STORAGE_TYPE': 'localfs',
    'BUCKET': 'edx-grades',
    'ROOT_PATH': '/tmp/edx-s3/ora2-responses',
}

######################## PROGRESS SUCCESS BUTTON ##############################
# The following fields are available in the URL: {course_id} {student_id}
PROGRESS_SUCCESS_BUTTON_URL = 'http://<domain>/<path>/{course_id}'
PROGRESS_SUCCESS_BUTTON_TEXT_OVERRIDE = None

# Course Forums Download
COURSE_FORUMS_DOWNLOAD_ROUTING_KEY = HIGH_MEM_QUEUE

# Student Forums Download
STUDENT_FORUMS_DOWNLOAD_ROUTING_KEY = HIGH_MEM_QUEUE

### SHIB
# For SHIB backup register and login URLs
SHIB_ONLY_SITE = False
# Mapping of hosts to a list of safe redirect domains from that host (not including itself)
# For example:
# SHIB_REDIRECT_DOMAIN_WHITELIST = {
#    'suclass.stanford.edu': ['studio.suclass.stanford.edu']
# }
SHIB_REDIRECT_DOMAIN_WHITELIST = {}

####################### In-line Analytics ######################
ANALYTICS_ANSWER_DIST_URL = None
INLINE_ANALYTICS_SUPPORTED_TYPES = {
    'MultipleChoiceResponse': 'radio',
    'ChoiceResponse': 'checkbox',
    'OptionResponse': 'option',
    'NumericalResponse': 'numerical',
    'StringResponse': 'string',
    'FormulaResponse': 'formula',
}

# Metrics tab data source setting
MAX_ENROLLEES_FOR_METRICS_USING_DB = 100

# MONGO Connection parameters for the forum servers.  Bypassing cs_comment_client
FORUM_MONGO_PARAMS = {
    'host': 'localhost',
    'port': 27017,
    'password': '',
    'user': '',
    'database': 'forum',
}

################### branding - for database driven tiles ##################
INSTALLED_APPS += ('branding_stanford',)
DISPLAY_COURSE_TILES = True

# Set to True for systems where students are auto-registered on login
DISABLE_REGISTER_BUTTON = False

# Provide a UI to allow users to report problems in LMS (left-hand modal)
FEATURES['ENABLE_PROBLEM_REPORTING'] = False

# Toggle to enable chat availability (configured on a per-course
# basis in Studio)
FEATURES['ENABLE_CHAT'] = False

#Toggle using CME registration instead of normal
FEATURES['USE_CME_REGISTRATION'] = False

# OP Superusers can log in as anyone
FEATURES['ENABLE_SUPERUSER_LOGIN_AS'] = False

# Sends the user's deanonymized email address to xqueue with code responses
# DO NOT SET if you don't want the anonymous user id to be linked with user.email in xqueue (Stanford does)
FEATURES['SEND_USERS_EMAILADDR_WITH_CODERESPONSE'] = False

FEATURES['ENABLE_PROGRESS_SUMMARY'] = True

FEATURES['ENABLE_COURSE_SORTING_BY_START_DATE'] = False

TEMPLATE_CONTEXT_PROCESSORS += (
    # Include TEMPLATE_VISIBLE_SETTINGS in templates
    'settings_context_processor.context_processors.settings',
)

MIDDLEWARE_CLASSES += (
    'sneakpeek_deeplink.middleware.SneakPeekDeepLinkMiddleware',
)

INSTALLED_APPS += (
    'settings_context_processor',
    'cme_registration',
    'sneakpeek_deeplink',
    'instructor_email_widget',
)
