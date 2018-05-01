"""
Admin registration for tags models
"""
from django.contrib import admin
<<<<<<< HEAD
from .models import TagCategories, TagAvailableValues
=======

from .models import TagAvailableValues, TagCategories
>>>>>>> f9fa460a74446b533b356e754848af6f56c141a1


class TagCategoriesAdmin(admin.ModelAdmin):
    """Admin for TagCategories"""
    search_fields = ('name', 'title')
    list_display = ('id', 'name', 'title')


class TagAvailableValuesAdmin(admin.ModelAdmin):
    """Admin for TagAvailableValues"""
    list_display = ('id', 'category', 'value')


admin.site.register(TagCategories, TagCategoriesAdmin)
admin.site.register(TagAvailableValues, TagAvailableValuesAdmin)
