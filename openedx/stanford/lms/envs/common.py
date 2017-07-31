from lms.envs.common import *
from glob import glob
import sys

STANFORD_ROOT = REPO_ROOT / 'openedx/stanford'

# Email to give anonymous users.  Should be a black-hole email address, but not cause errors when email is sent there
# This is actually just a base email.  We'll make it 'noreply+<username>@example.com' to ensure uniqueness
ANONYMOUS_USER_EMAIL = 'noreply@example.com'
API_DATE_FORMAT = '%Y-%m-%d'
COURSE_FORUMS_DOWNLOAD_ROUTING_KEY = HIGH_MEM_QUEUE
COURSE_MODE_DEFAULTS = {
    'currency': 'usd',
    'description': None,
    'expiration_datetime': None,
    'min_price': 0,
    'name': 'Audit',
    'sku': None,
    'slug': 'audit',
    'suggested_prices': '',
}
# Set to True for systems where students are auto-registered on login
DISABLE_REGISTER_BUTTON = False
DISPLAY_COURSE_TILES = True
EXTRA_MIMETYPES = {
    # map file extensions to mimetypes, e.g.
    # '.woff': 'application/font-woff',
}
FEATURES.update({
    'ENABLE_CHAT': False,
    'ENABLE_COURSE_SORTING_BY_START_DATE': False,
    'ENABLE_DISCUSSION_HOME_PANEL': True,
    'ENABLE_DISCUSSION_EMAIL_DIGEST': True,
    'ENABLE_PROGRESS_SUMMARY': True,
    'ENABLE_SUPERUSER_LOGIN_AS': False,
    'USE_CME_REGISTRATION': False,
    # Sends the user's deanonymized email address to xqueue with code responses
    # DO NOT SET if you don't want the anonymous user id to be linked
    #   with user.email in xqueue (Stanford does)
    'SEND_USERS_EMAILADDR_WITH_CODERESPONSE': False,
})
FORUM_MONGO_PARAMS = {
    'hosts': [
        {
            'host': 'localhost',
            'port': 27017,
        },
    ],
    'password': '',
    'user': '',
    'database': 'forum',
}
HELP_MODAL_LINKS = [
    # {'url': 'https://help.com', 'text': 'How to register an account'}
]
INLINE_ANALYTICS_SUPPORTED_TYPES = {
    'MultipleChoiceResponse': 'radio',
    'ChoiceResponse': 'checkbox',
    'OptionResponse': 'option',
    'NumericalResponse': 'numerical',
    'StringResponse': 'string',
    'FormulaResponse': 'formula',
}
INSTALLED_APPS += (
    'branding_stanford',
    'cme_registration',
    'instructor_email_widget',
    'settings_context_processor',
    # Added here to allow translations
    'freetextresponse',
)
MAKO_TEMPLATES['main'] += glob(STANFORD_ROOT / 'djangoapps/*/templates')
MAX_ENROLLEES_FOR_METRICS_USING_DB = 100
ORA2_RESPONSES_DOWNLOAD = {
    'STORAGE_TYPE': 'localfs',
    'BUCKET': 'edx-grades',
    'ROOT_PATH': '/tmp/edx-s3/ora2-responses',
}
ORA2_RESPONSES_DOWNLOAD_ROUTING_KEY = HIGH_MEM_QUEUE
PAYMENT_CONFIRM_EMAIL = PAYMENT_SUPPORT_EMAIL
PAYMENT_SUPPORT_PHONE = '1112223344'
PAYMENT_PLATFORM_NAME = 'PAYMENT PLATFORM NAME'
######################## PROGRESS SUCCESS BUTTON ##############################
# The following fields are available in the URL: {course_id} {student_id}
PROGRESS_SUCCESS_BUTTON_URL = 'http://<domain>/<path>/{course_id}'
PROGRESS_SUCCESS_BUTTON_TEXT_OVERRIDE = None
SHIB_ONLY_SITE = False
SHIB_REDIRECT_DOMAIN_WHITELIST = {
    # Mapping of hosts to a list of safe redirect domains from that host
    # (not including itself); e.g.
    # 'suclass.stanford.edu': ['studio.suclass.stanford.edu']
}
STATICFILES_DIRS += glob(STANFORD_ROOT / 'djangoapps/*/static')
STUDENT_FORUMS_DOWNLOAD_ROUTING_KEY = HIGH_MEM_QUEUE
STUDENT_RESPONSES_DOWNLOAD = {
    'STORAGE_TYPE': 'localfs',
    'BUCKET': 'edx-student-responses',
    'ROOT_PATH': '/tmp/edx-s3/student-responses',
}
STUDENT_RESPONSES_DOWNLOAD_ROUTING_KEY = HIGH_MEM_QUEUE
STUDENT_RESPONSES_REPORT_SUPPORTED_TYPES = {
    'problem',
    'submit-and-compare',
    'freetextresponse',
}
TEMPLATE_VISIBLE_SETTINGS = [
    # These settings' values will be exposed to all templates
    'FEATURES',
]
TEMPLATES[0]['DIRS'] += glob(STANFORD_ROOT / 'djangoapps/*/templates')
TEMPLATES[0]['OPTIONS']['context_processors'] += [
    # Include TEMPLATE_VISIBLE_SETTINGS in templates
    'settings_context_processor.context_processors.settings',
]
THEME_NAME = 'lagunita'
TYPES_WITH_CHILD_PROBLEMS_LIST = [
    # These types are children of children of units.
    'library_content',
]

# These are the problem types (by block_type) that an instructor can query over in the Instructor Query tab
INSTRUCTOR_QUERY_PROBLEM_TYPES = [
    'problem',
]
