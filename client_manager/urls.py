# -*- coding: utf-8 -*-
""" URL routing configuration for client manager app. """
from django.conf.urls import url

from .views import login_as_user

urlpatterns = [
    url(r'login-as/(?P<user_id>\d+)/', login_as_user, name='login-as-view'),
]
