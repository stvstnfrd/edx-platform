"""
Customize the django admin experience
"""
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
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


class AllowListFilter(SimpleListFilter):
    title = 'Allow List'
    parameter_name = 'allow'

    def lookups(self, request, model_admin):
        queryset = model_admin.get_queryset(request)
        values = tuple(
            (
                ','.join(filters[self.parameter_name] or ['None']),
                ', '.join(filters[self.parameter_name] or ['None']),
            )
            for filters in queryset.values(self.parameter_name).distinct()
        )
        return values

    def queryset(self, request, queryset):
        value = self.value()
        filter_kwargs = {}
        if value:
            if ',' not in value:
                if value == 'None':
                    filter_kwargs[self.parameter_name + '__exact'] = ''
                    return queryset.filter(**filter_kwargs)
                else:
                    filter_kwargs[self.parameter_name + '__contains'] = value
                    return queryset.filter(**filter_kwargs)
            else:
                for v in value.split(','):
                    filter_kwargs[self.parameter_name + '__contains'] = v
                    queryset = queryset.filter(**filter_kwargs)
                return queryset
        else:
            return queryset


class DenyListFilter(AllowListFilter):
    title = 'Deny List'
    parameter_name = 'deny'


# class ProviderFilterAdmin(admin.ModelAdmin):
class ProviderFilterAdmin(StackedConfigModelAdmin):
    search_fields = (
        'allow',
        'deny',
    )
    list_filter = (
        'enabled',
        AllowListFilter,
        DenyListFilter,
    )


admin.site.register(DiscussionsConfiguration, DiscussionsConfigurationAdmin)
admin.site.register(ProviderFilter, ProviderFilterAdmin)
