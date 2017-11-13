# -*- coding: utf-8 -*-
""" URL routing configuration for feed manager app. """
from django.conf.urls import url

from feedmanager.views import BulkUploadSnippetsView

urlpatterns = [
    url(r'bulk-upload-snippets/', BulkUploadSnippetsView.as_view(), name='bulk-upload-snippets')
]
