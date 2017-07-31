from cms.envs.test import *


FEATURES['ALLOW_COURSE_RERUNS'] = True
INSTALLED_APPS += (
    'openedx.stanford.djangoapps.register_cme',
)
