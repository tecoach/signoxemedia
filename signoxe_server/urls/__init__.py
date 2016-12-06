# -*- coding: utf-8 -*-
"""
Fallback URL routing configuration for the project to maintain compatibility with existing URLs
while clients are being migrated.
"""
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.views.generic import TemplateView

from . import admin, api, content, devices

urlpatterns = [
    url(r'^admin/', include(admin)),
    url(r'^api/', include(api)),
    url(r'^devices/', include(devices)),
    url(r'^feeds/', include(content)),
    url(r'^$', TemplateView.as_view(template_name='home.html'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
