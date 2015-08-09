# -*- coding: utf-8 -*-
from openedx.contrib.stanford.lms.envs.common import *
from lms.envs.test import *

################################# CHAT ######################################
# We'll use a SQLite DB just for the purposes of testing out the
# Django side of things. In non-test environments, this should point
# at a MySQL database that's been set up by the ejabberd provisioner.
DATABASES['jabber'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': TEST_ROOT / 'db' / 'jabber.db'
}

INSTALLED_APPS += ('jabber',)
