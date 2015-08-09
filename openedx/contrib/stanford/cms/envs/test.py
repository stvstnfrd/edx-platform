# -*- coding: utf-8 -*-
from openedx.contrib.stanford.cms.envs.common import *
from cms.envs.test import *

# Remove sneakpeek during tests to prevent unwanted redirect
MIDDLEWARE_CLASSES = tuple([
    mwc for mwc in MIDDLEWARE_CLASSES
    if mwc != 'sneakpeek.middleware.SneakPeekLogoutMiddleware'
])

# This is to disable tests CME Registration tests, under common, that will not pass when run under CMS
FEATURES['DISABLE_CME_REGISTRATION_TESTS'] = True
