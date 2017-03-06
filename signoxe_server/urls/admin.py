# -*- coding: utf-8 -*-
""" URL routing configuration for the admin domain. """
from django.conf.urls import include, url
from django.contrib import admin

import client_manager.urls
import feedmanager.admin_urls
from signoxe_server.system_info import system_info

admin.site.site_header = 'Signoxe Administration'
admin.site.site_title = 'Signoxe admin panel'

urlpatterns = [
    url(r'^', admin.site.urls),
    url(r'^sys-info/', system_info),
    url(r'^', include(client_manager.urls)),
    url(r'^', include(feedmanager.admin_urls)),
]
