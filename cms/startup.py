"""
Module for code that should run during Studio startup (deprecated)
"""

import django
from django.conf import settings

# Force settings to run so that the python path is modified
settings.INSTALLED_APPS  # pylint: disable=pointless-statement


def run():
    """
    Executed during django startup

    NOTE: DO **NOT** add additional code to this method or this file! The Platform Team
          is moving all startup code to more standard locations using Django best practices.
    """
<<<<<<< HEAD
    Add extra mimetypes. Used in xblock_resource.

    If you add a mimetype here, be sure to also add it in lms/startup.py.
    """
    import mimetypes

    mimetypes.add_type('application/vnd.ms-fontobject', '.eot')
    mimetypes.add_type('application/x-font-opentype', '.otf')
    mimetypes.add_type('application/x-font-ttf', '.ttf')
    mimetypes.add_type('application/font-woff', '.woff')
    for extension, mimetype in settings.EXTRA_MIMETYPES.iteritems():
        mimetypes.add_type(mimetype, extension)
=======
    django.setup()
>>>>>>> 7ad437b52cb5b2d65ab1b65e6147bcced05c42e4
