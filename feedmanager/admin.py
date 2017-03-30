# -*- coding: utf-8 -*-
""" Admin setup for feed manager app. """
from django.contrib import admin
from django.db import models

from feedmanager.models import (Category, ImageFeed, ImageSnippet, Template, VideoFeed,
                                VideoSnippet, WebFeed, WebSnippet)
from mediamanager.widgets import AceEditorWidget


@admin.register(WebFeed)
class WebFeedAdmin(admin.ModelAdmin):
    """ Admin panel setup class for web feeds. """
    list_display = ('name', 'category', 'template', 'published',)
    list_filter = ('category', 'published',)
    filter_horizontal = ('publish_to',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ImageFeed)
@admin.register(VideoFeed)
class ImageVideoFeedAdmin(admin.ModelAdmin):
    """ Admin panel setup class for file-based feeds. """
    list_display = ('name', 'category', 'published',)
    list_filter = ('category', 'published',)
    filter_horizontal = ('publish_to',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(WebSnippet)
@admin.register(ImageSnippet)
@admin.register(VideoSnippet)
class SnippetAdmin(admin.ModelAdmin):
    """ Admin panel setup class for snippets. """
    list_display = ('title', 'category', 'date')
    list_filter = ('category',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """ Admin panel setup class for categories. """
    list_display = ('name', 'type',)
    list_filter = ('type',)


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    """ Admin panel setup class for templates. """
    list_display = ('name', 'duration')
    formfield_overrides = {
        models.TextField: {'widget': AceEditorWidget}
    }
