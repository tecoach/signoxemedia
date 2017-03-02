# -*- coding: utf-8 -*-
from django_hosts import host, patterns

host_patterns = patterns(
    '',
    host(r'admin', 'signoxe_server.urls.admin', name='admin'),
    host(r'api', 'signoxe_server.urls.api', name='api'),
    host(r'content', 'signoxe_server.urls.content', name='content'),
    host(r'devices', 'signoxe_server.urls.devices', name='devices'),
    host(r'(\w+)', 'signoxe_server.urls', name='wildcard'),
)
