# -*- coding: utf-8 -*-
from django.contrib import admin
from django.db import models

from mediamanager.widgets import AceEditorWidget
from notification_manager.models import Post, PostTopic


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'posted_on')
    list_filter = ('topic', 'posted_on')
    formfield_overrides = {
        models.TextField: {'widget': AceEditorWidget}
    }


admin.site.register(PostTopic)
