"""
Configure the application
"""
from django.apps import AppConfig


class SneakPeekConfig(AppConfig):
    """
    Configure the application and monkey-patch the `User` model
    """
    name = 'openedx.stanford.djangoapps.sneakpeek'
    verbose_name = "SneakPeak"

    def ready(self):
        """
        Monkey-patch `User` and `AnonymousUser` models for sneakpeek functionality
        """
        from django.contrib.auth.models import AnonymousUser
        from django.contrib.auth.models import User
        from openedx.stanford.djangoapps.sneakpeek import lib
        methods = [
            'can_enroll_nonregistered',
            'deny_nonregistered_access',
            'is_nonregistered',
            'is_registered',
        ]
        models = [
            AnonymousUser,
            User,
        ]
        for method_name in methods:
            method = getattr(lib, method_name)
            for model in models:
                if not hasattr(model, method_name):
                    if hasattr(model, 'add_to_class'):
                        model.add_to_class(method_name, method)
                    else:
                        setattr(model, method_name, method)
