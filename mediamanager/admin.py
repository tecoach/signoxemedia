# -*- coding: utf-8 -*-
""" Admin setup for media manager app. """
from django.contrib import admin
from django.db import models

from mediamanager.models import (CalendarAsset, ContentFeed, ImageAsset, Playlist, PlaylistItem,
                                 Ticker, TickerSeries, VideoAsset, WebAsset, WebAssetTemplate, )
from mediamanager.widgets import AceEditorWidget
from utils.mixins import AutoAddOwnerAdminMixin


@admin.register(ImageAsset)
@admin.register(VideoAsset)
class FileAssetAdmin(AutoAddOwnerAdminMixin, admin.ModelAdmin):
    """ Admin panel setup class for file-based assets. """
    fields = ('name', 'media_file', 'owner',)
    list_display = ('name', 'created', 'owner',)
    list_filter = ('created', 'owner',)


@admin.register(WebAsset)
class WebAssetAdmin(AutoAddOwnerAdminMixin, admin.ModelAdmin):
    """ Admin panel setup class for web assets. """
    fields = ('name', 'url', 'content', 'owner',)
    list_display = ('name', 'created', 'owner',)
    list_filter = ('created', 'owner',)
    formfield_overrides = {
        models.TextField: {'widget': AceEditorWidget}
    }


class TickerInlineAdmin(admin.StackedInline):
    """ Inline admin config class for tickers. """
    model = Ticker


@admin.register(TickerSeries)
class TickerSeriesAdmin(AutoAddOwnerAdminMixin, admin.ModelAdmin):
    """ Admin panel setup class for ticker series. """
    inlines = (TickerInlineAdmin,)
    list_display = ('name', 'owner', 'ticker_count')
    list_filter = ('owner',)

    @staticmethod
    def ticker_count(obj):
        """ Returns the number of tickers in the ticker set, for display in the admin panel """
        return obj.ticker_set.count()


class PlaylistItemInlineAdmin(admin.StackedInline):
    """ Inline admin config class for playlist itens. """
    model = PlaylistItem


@admin.register(Playlist)
class PlaylistAdmin(AutoAddOwnerAdminMixin, admin.ModelAdmin):
    """ Admin panel setup class for playlists. """
    inlines = (PlaylistItemInlineAdmin,)
    list_display = ('name', 'auto_add_feeds', 'owner',)
    list_filter = ('owner',)


@admin.register(WebAssetTemplate)
class WebAssetTemplateAdmin(admin.ModelAdmin):
    """
    Admin panel setup class for web asset templates.
    This class simply overrides the widget used by the template to use out AceEditorWidget
    """
    list_display = ('name', 'calendar_support', 'data_support')
    list_filter = ('calendar_support', 'data_support')
    formfield_overrides = {
        models.TextField: {'widget': AceEditorWidget}
    }


admin.site.register(ContentFeed)
admin.site.register(CalendarAsset)
