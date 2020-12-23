"""
Provide django models to back the discussions app
"""
from __future__ import annotations
import logging

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_mysql.models import ListCharField
from jsonfield import JSONField
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import LearningContextKeyField
from simple_history.models import HistoricalRecords

from lti_consumer.models import LtiConfiguration
from organizations.models import Organization

from openedx.core.djangoapps.config_model_utils.models import StackedConfigurationModel
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

log = logging.getLogger(__name__)


def get_default_providers():
    providers = [
        'cs_comments_service',
        'lti-base',
    ]
    return providers


class ProviderFilter(StackedConfigurationModel):
    allow = ListCharField(
        base_field=models.CharField(
            choices=[
                (provider, provider)
                for provider in get_default_providers()
            ],
            max_length=20,
        ),
        blank=True,
        help_text=_("Comma-separated list of providers to allow, eg: {choices}").format(
            choices=','.join(get_default_providers()),
        ),
        # max_length = (size * (max_length + 1)) # to include the comma
        max_length=(len(get_default_providers()) * 21),
        size=len(get_default_providers()),
        verbose_name=_('Allow List'),
    )
    deny = ListCharField(
        base_field=models.CharField(
            choices=[
                (provider, provider)
                for provider in get_default_providers()
            ],
            max_length=20,
        ),
        blank=True,
        help_text=_("Comma-separated list of providers to deny, eg: {choices}").format(
            choices=','.join(get_default_providers()),
        ),
        # max_length = (size * (max_length + 1)) # to include the comma
        max_length=(len(get_default_providers()) * 21),
        size=len(get_default_providers()),
        verbose_name=_('Deny List'),
    )

    STACKABLE_FIELDS = ('allow', 'deny')

    @classmethod
    def default_providers(cls) -> list[str]:
        # TODO: Load this from the entry points
        return []

    @property
    def allow_list(self) -> list[str]:
        if self.allow:
            return self.allow
        return []

    @property
    def deny_list(self) -> list[str]:
        if self.deny:
            return self.deny
        return []

    def __str__(self):
        return 'ProviderFilter(org="{org}", allow="{allow}", deny="{deny}")'.format(
            allow=self.allow,
            deny=self.deny,
            org=self.org,
        )

    @property
    def available_providers(self) -> list[str]:
        _providers = ProviderFilter.current().default_providers()
        if self.allow_list:
            _providers = [
                provider
                for provider in _providers
                if provider in self.allow_list
            ]
        if self.deny_list:
            _providers = [
                provider
                for provider in _providers
                if provider not in self.deny_list
            ]
        return _providers

    @classmethod
    def get(cls, course_key) -> cls:
        _filter = cls.current(course_key=course_key)
        return _filter

    @classmethod
    def get_available_providers(cls, course_key) -> list[str]:
        _filter = cls.get(course_key)
        providers = _filter.available_providers
        return providers


class DiscussionsConfiguration(TimeStampedModel):
    """
    Associates a learning context with discussion provider and configuration
    """

    context_key = LearningContextKeyField(
        primary_key=True,
        db_index=True,
        unique=True,
        max_length=255,
        # Translators: A key specifying a course, library, program, website, or some other collection of content where learning happens.
        verbose_name=_("Learning Context Key"),
    )
    enabled = models.BooleanField(
        default=True,
        help_text=_("If disabled, the discussions in the associated learning context/course will be disabled.")
    )
    lti_configuration = models.ForeignKey(
        LtiConfiguration,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_("The LTI configuration data for this context/provider."),
    )
    plugin_configuration = JSONField(
        blank=True,
        default={},
        help_text=_("The plugin configuration data for this context/provider."),
    )
    provider_type = models.CharField(
        blank=False,
        max_length=100,
        verbose_name=_("Discussion provider"),
        help_text=_("The discussion tool/provider's id"),
    )
    history = HistoricalRecords()

    def clean(self):
        """
        Validate the model

        Currently, this only support courses, this can be extended
        whenever discussions are available in other contexts
        """
        if not CourseOverview.course_exists(self.context_key):
            raise ValidationError('Context Key should be an existing learning context.')

    def __str__(self):
        return "{context_key}: provider={provider} enabled={enabled}".format(
            context_key=self.context_key,
            provider=self.provider_type,
            enabled=self.enabled,
        )

    @classmethod
    def is_enabled(cls, context_key) -> bool:
        """
        Check if there is an active configuration for a given course key

        Default to False, if no configuration exists
        """
        configuration = cls.get(context_key)
        return configuration.enabled

    @classmethod
    def get(cls, context_key) -> cls:
        """
        Lookup a model by context_key
        """
        try:
            configuration = cls.objects.get(context_key=context_key)
        except cls.DoesNotExist:
            configuration = cls(context_key=context_key, enabled=False)
        return configuration

    @property
    def available_providers(self) -> list[str]:
        return ProviderFilter.current(course_key=self.context_key).available_providers

    @classmethod
    def get_available_providers(cls, context_key) -> list[str]:
        return ProviderFilter.current(course_key=context_key).available_providers
