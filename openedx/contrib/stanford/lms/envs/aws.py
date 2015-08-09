# -*- coding: utf-8 -*-
from openedx.contrib.stanford.lms.envs.common import *
from lms.envs.aws import *


ACCOUNT_NAME = ENV_TOKENS.get('ACCOUNT_NAME', ACCOUNT_NAME)
CERT_NAME_SHORT = ENV_TOKENS.get('CERT_NAME_SHORT', CERT_NAME_SHORT)
CERT_NAME_LONG = ENV_TOKENS.get('CERT_NAME_LONG', CERT_NAME_LONG)
DISPLAY_COURSE_TILES = ENV_TOKENS.get('DISPLAY_COURSE_TILES', True)
HELP_MODAL_LINKS = ENV_TOKENS.get('HELP_MODAL_LINKS', [])

# Student Responses Download
STUDENT_RESPONSES_DOWNLOAD_ROUTING_KEY = HIGH_MEM_QUEUE
STUDENT_RESPONSES_DOWNLOAD = ENV_TOKENS.get("STUDENT_RESPONSES_DOWNLOAD", STUDENT_RESPONSES_DOWNLOAD)

# ORA2 Responses Download
ORA2_RESPONSES_DOWNLOAD_ROUTING_KEY = HIGH_MEM_QUEUE
ORA2_RESPONSES_DOWNLOAD = ENV_TOKENS.get("ORA2_RESPONSES_DOWNLOAD", ORA2_RESPONSES_DOWNLOAD)

# TODO: Get Course Forums Download and Student Forums download from env_tokens instead of common
# Course Forums Download
COURSE_FORUMS_DOWNLOAD_ROUTING_KEY = HIGH_MEM_QUEUE

# Student Forums Download
STUDENT_FORUMS_DOWNLOAD_ROUTING_KEY = HIGH_MEM_QUEUE

##### SHIB #####
SHIB_ONLY_SITE = ENV_TOKENS.get('SHIB_ONLY_SITE', SHIB_ONLY_SITE)
SHIB_REDIRECT_DOMAIN_WHITELIST = ENV_TOKENS.get('SHIB_REDIRECT_DOMAIN_WHITELIST', SHIB_REDIRECT_DOMAIN_WHITELIST)

####################### In-line Analytics ######################
ANALYTICS_ANSWER_DIST_URL = ENV_TOKENS.get("ANALYTICS_ANSWER_DIST_URL", ANALYTICS_ANSWER_DIST_URL)
INLINE_ANALYTICS_SUPPORTED_TYPES = ENV_TOKENS.get("INLINE_ANALYTICS_SUPPORTED_TYPES", INLINE_ANALYTICS_SUPPORTED_TYPES)

##### METRICS DATA SOURCE #####
MAX_ENROLLEES_FOR_METRICS_USING_DB = ENV_TOKENS.get('MAX_ENROLLEES_FOR_METRICS_USING_DB', MAX_ENROLLEES_FOR_METRICS_USING_DB)

# Forum mongo credentials
FORUM_MONGO_PARAMS = AUTH_TOKENS.get('FORUM_MONGO_PARAMS', FORUM_MONGO_PARAMS)

# Register button on home page
DISABLE_REGISTER_BUTTON = ENV_TOKENS.get('DISABLE_REGISTER_BUTTON', DISABLE_REGISTER_BUTTON)

JABBER = ENV_TOKENS.get('JABBER', {})
DATABASE_ROUTERS = ENV_TOKENS.get('DATABASE_ROUTERS', [])

# Chat
if FEATURES.get("ENABLE_CHAT"):
    MAKO_TEMPLATES['main'].append(PROJECT_ROOT / 'djangoapps' / 'jabber' / 'templates')
    STATICFILES_DIRS.append(PROJECT_ROOT / 'djangoapps' / 'jabber' / 'static')
