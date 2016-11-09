# -*- coding: utf-8 -*-
""" URL routing configuration for API. """
from django.conf.urls import include, url
from rest_framework import routers
from rest_framework.schemas import get_schema_view

from devicemanager.views import DeviceGroupViewSet, DeviceScreenShotViewSet, DeviceViewSet
from mediamanager.views import (AssetViewSet, CalendarViewSet, ContentFeedViewSet,
                                FeedViewSet,
                                ImageViewSet, PlaylistItemViewSet, PlaylistViewSet,
                                TickerSeriesViewSet, TickerViewSet,
                                VideoViewSet, WebAssetTemplateViewSet, WebViewSet, )
from notification_manager.views import PostViewSet
from schedule_manager.views import ScheduledContentViewSet, SpecialContentViewSet

schema_view = get_schema_view(title='Signoxe Frontend API',
                              urlconf='signoxe_server.urls.api')

router = routers.DefaultRouter()
router.register(r'assets', AssetViewSet)
router.register(r'calendar_assets', CalendarViewSet)
router.register(r'content_feeds', ContentFeedViewSet)
router.register(r'device_groups', DeviceGroupViewSet)
router.register(r'device_screenshots', DeviceScreenShotViewSet)
router.register(r'devices', DeviceViewSet)
router.register(r'feed_assets', FeedViewSet)
router.register(r'image_assets', ImageViewSet)
router.register(r'playlist_items', PlaylistItemViewSet)
router.register(r'playlists', PlaylistViewSet)
router.register(r'scheduled_content', ScheduledContentViewSet)
router.register(r'special_content', SpecialContentViewSet)
router.register(r'ticker_series', TickerSeriesViewSet)
router.register(r'tickers', TickerViewSet)
router.register(r'video_assets', VideoViewSet)
router.register(r'web_asset_templates', WebAssetTemplateViewSet)
router.register(r'web_assets', WebViewSet)
router.register(r'notifications', PostViewSet)

urlpatterns = [
    url('^$', schema_view),
    url(r'', include(router.urls, namespace='api')),
    url(r'auth/', include('djoser.urls.base')),
    url(r'auth/', include('djoser.urls.authtoken')),
]
