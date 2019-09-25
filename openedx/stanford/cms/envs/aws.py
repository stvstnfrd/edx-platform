from cms.envs.aws import *
from lms.envs.common import COURSE_MODE_DEFAULTS


CMS_BASE = ENV_TOKENS.get(
    'CMS_BASE',
)
COPYRIGHT_EMAIL = ENV_TOKENS.get(
    'COPYRIGHT_EMAIL',
    COPYRIGHT_EMAIL
)
DEFAULT_COURSE_ABOUT_IMAGE_URL = ENV_TOKENS.get(
    'DEFAULT_COURSE_ABOUT_IMAGE_URL',
    DEFAULT_COURSE_ABOUT_IMAGE_URL
)
EXTRA_MIMETYPES = ENV_TOKENS.get('EXTRA_MIMETYPES', EXTRA_MIMETYPES)
SHIB_ONLY_SITE = ENV_TOKENS.get(
    'SHIB_ONLY_SITE',
    SHIB_ONLY_SITE
)
SHIB_REDIRECT_DOMAIN_WHITELIST = ENV_TOKENS.get(
    'SHIB_REDIRECT_DOMAIN_WHITELIST',
    SHIB_REDIRECT_DOMAIN_WHITELIST
)
XBLOCKS_ALWAYS_IN_STUDIO = ENV_TOKENS.get(
    'XBLOCKS_ALWAYS_IN_STUDIO',
    XBLOCKS_ALWAYS_IN_STUDIO
)

INSTRUCTOR_QUERY_PROBLEM_TYPES = ENV_TOKENS.get(
    'INSTRUCTOR_QUERY_PROBLEM_TYPES',
    INSTRUCTOR_QUERY_PROBLEM_TYPES
)
