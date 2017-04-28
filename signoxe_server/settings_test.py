# -*- coding: utf-8 -*-
""" Setting for use while testing """
# noinspection PyUnresolvedReferences
from .settings import *

# Reset staticfile storage so we don't get manifest errors
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
