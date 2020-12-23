"""
Customize the django admin experience
"""
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from openedx.core.djangoapps.config_model_utils.admin import StackedConfigModelAdmin

from .models import DiscussionsConfiguration
from .models import ProviderFilter


class DiscussionsConfigurationAdmin(SimpleHistoryAdmin):
    search_fields = (
        'context_key',
        'enabled',
        'provider_type',
    )
    list_filter = (
        'enabled',
        'provider_type',
    )


# class ProviderFilterAdmin(admin.ModelAdmin):
class ProviderFilterAdmin(StackedConfigModelAdmin):
    search_fields = (
        'allow',
        'deny',
    )
    list_filter = (
        'enabled',
        'allow',
        'deny',
    )


admin.site.register(DiscussionsConfiguration, DiscussionsConfigurationAdmin)
admin.site.register(ProviderFilter, ProviderFilterAdmin)
