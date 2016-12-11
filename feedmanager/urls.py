# -*- coding: utf-8 -*-
""" URL routing configuration for feed manager app. """
from django.conf.urls import url

from feedmanager.views import image_feed_view, video_feed_view, web_feed_view

urlpatterns = [
    url(r'web/(?P<slug>[-\w]+)/', web_feed_view, name='web-feed-view'),
    url(r'image/(?P<slug>[-\w]+)/', image_feed_view, name='image-feed-view'),
    url(r'video/(?P<slug>[-\w]+)/', video_feed_view, name='video-feed-view'),
]
