"""
Settings for the LMS that runs alongside the CMS on AWS
"""

# We intentionally define lots of variables that aren't used, and
# want to import all variables from base settings files
# pylint: disable=wildcard-import, unused-wildcard-import

from ..dev import *

FEATURES['AUTH_USE_CERTIFICATES'] = False

VIRTUAL_UNIVERSITIES = ['edge']

META_UNIVERSITIES = {}

CONTENTSTORE = {
    'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
    'DOC_STORE_CONFIG': {
        'host': 'localhost',
        'db': 'xcontent',
    }
}

INSTALLED_APPS += (
    # Mongo perf stats
    'debug_toolbar_mongo',
)


DEBUG_TOOLBAR_PANELS += (
    'debug_toolbar_mongo.panel.MongoDebugPanel',
)

# HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS defines, as dictionary of regex's, a set of mappings of HTTP request hostnames to
# what the 'default' modulestore to use while processing the request
# for example 'preview.edx.org' should use the draft modulestore
HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS = {
    'preview\.': 'draft-preferred'
}
