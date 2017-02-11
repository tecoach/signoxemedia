# -*- coding: utf-8 -*-
""" URL routing configuration for device manager app. """
from django.conf.urls import url

from devicemanager.views import device_feed_view, device_screenshot_view, mirror_feed_view

urlpatterns = [
    url(r'mirror/(?P<mirror_id>[0-9a-f-]{32,36})/$', mirror_feed_view, name='mirror-feed-view'),
    url(r'(?P<device_id>[0-9a-f-]{32,36})/screenshot/$',
        device_screenshot_view,
        name='device-screenshot-view'),
    url(r'(?P<device_id>[0-9a-f-]{32,36})/$', device_feed_view, name='device-feed-view'),

]
