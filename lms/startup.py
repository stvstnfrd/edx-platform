"""
Module for code that should run during LMS startup (deprecated)
"""

import django
from django.conf import settings

# Force settings to run so that the python path is modified
settings.INSTALLED_APPS  # pylint: disable=pointless-statement


def run():
    """
    Executed during django startup

<<<<<<< HEAD
        # register InstructorService (for deleting student attempts and user staff access roles)
        set_runtime_service('instructor', InstructorService())

    # In order to allow modules to use a handler url, we need to
    # monkey-patch the x_module library.
    # TODO: Remove this code when Runtimes are no longer created by modulestores
    # https://openedx.atlassian.net/wiki/display/PLAT/Convert+from+Storage-centric+runtimes+to+Application-centric+runtimes
    xmodule.x_module.descriptor_global_handler_url = lms_xblock.runtime.handler_url
    xmodule.x_module.descriptor_global_local_resource_url = lms_xblock.runtime.local_resource_url

    # Set the version of docs that help-tokens will go to.
    settings.HELP_TOKENS_LANGUAGE_CODE = settings.LANGUAGE_CODE
    settings.HELP_TOKENS_VERSION = doc_version()

    # validate configurations on startup
    validate_lms_config(settings)

    from branding_stanford.api import patch as patch_stanford_branding
    patch_stanford_branding()


def add_mimetypes():
    """
    Add extra mimetypes. Used in xblock_resource.

    If you add a mimetype here, be sure to also add it in cms/startup.py.
    """
    import mimetypes

    mimetypes.add_type('application/vnd.ms-fontobject', '.eot')
    mimetypes.add_type('application/x-font-opentype', '.otf')
    mimetypes.add_type('application/x-font-ttf', '.ttf')
    mimetypes.add_type('application/font-woff', '.woff')
    for extension, mimetype in settings.EXTRA_MIMETYPES.iteritems():
        mimetypes.add_type(mimetype, extension)


def enable_microsites():
    """
    Calls the enable_microsites function in the microsite backend.
    Here for backwards compatibility
=======
    NOTE: DO **NOT** add additional code to this method or this file! The Platform Team
          is moving all startup code to more standard locations using Django best practices.
>>>>>>> 7ad437b52cb5b2d65ab1b65e6147bcced05c42e4
    """
    django.setup()
