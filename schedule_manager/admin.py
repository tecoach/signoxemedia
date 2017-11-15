# -*- coding: utf-8 -*-
from django.contrib import admin

from schedule_manager.models import ScheduledContent, SpecialContent


@admin.register(ScheduledContent)
class ScheduledContentAdmin(admin.ModelAdmin):
    fields = (
        ('device_group',),
        ('day', 'default',),
        ('start_time', 'end_time',),
        'content'
    )
    list_display = ('device_group', 'day', 'default', 'start_time', 'end_time', 'content',)
    list_filter = ('device_group', 'day', 'default',)


@admin.register(SpecialContent)
class SpecialContentAdmin(admin.ModelAdmin):
    list_display = ('device_group', 'date', 'content',)
