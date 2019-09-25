from cms.envs.test import *


# Remove sneakpeek during tests to prevent unwanted redirect
MIDDLEWARE_CLASSES = tuple([
    mwc for mwc in MIDDLEWARE_CLASSES
    if mwc != 'openedx.stanford.djangoapps.sneakpeek.middleware.SneakPeekLogoutMiddleware'
])
