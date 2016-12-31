# -*- coding: utf-8 -*-
""" URL routing configuration for media manager app """
from django.conf.urls import url

from mediamanager.views import asset_view, cal_asset_view, web_asset_view

urlpatterns = [
    url(r'^preview/(?P<asset_id>\d+)/', asset_view, name='asset-view'),
    url(r'^web/(?P<asset_id>\d+)/', web_asset_view, name='webasset-view'),
    url(r'^cal/(?P<asset_id>\d+)/', cal_asset_view, name='calasset-view'),
]
