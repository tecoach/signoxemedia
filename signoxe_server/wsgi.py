# -*- coding: utf-8 -*-
""" WSGI module for Signoxe server. """

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'signoxe_server.settings')

application = get_wsgi_application()
