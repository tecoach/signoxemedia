# -*- coding: utf-8 -*-
""" URL routing configuration for the devices sub-domain. """
from django.conf.urls import include, url

import devicemanager.urls

urlpatterns = [
    url(r'', include(devicemanager.urls)),
]
