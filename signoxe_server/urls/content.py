# -*- coding: utf-8 -*-
""" URL routing configuration for the content sub-domain. """
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static

import feedmanager.urls
import mediamanager.urls

urlpatterns = [
    url(r'feeds/', include(feedmanager.urls)),
    url(r'media/', include(mediamanager.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
