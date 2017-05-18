# -*- coding: utf-8 -*-
"""
Contains a view function to display basic system information.
"""
import subprocess
import sys

import django
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse

git_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'])
formatted_settings = '\n'.join(
    '{} = {}'.format(setting, getattr(settings, setting))
    for setting in filter(lambda s: s[0].isupper(), dir(settings))
)


@staff_member_required
def system_info(request):
    """
    This view displays a simple HTML page that displays system information such as the Python
    version, the Django version, the version of the server, and whether the app is running in
    production mode.
    """
    message = """<html>
    <head><title>Server Information</title></head>
    <table>
    <tr><td>Python version:</td><td>{python_version}</td></tr>
    <tr><td>Django version:</td><td>{django_version}</td></tr>
    <tr>
    <td>Signoxe version:</td>
    <td>
    <a href='https://bitbucket.org/signoxe/signoxe-server/commits/{signoxe_version}'>
    {signoxe_version}
    </a>
    </td>
    </tr>
    <tr><td>Production mode:</td><td>{is_production}</td></tr>
    </table>
    <p>Settings:</p>
    <pre>{settings}</pre>
    </html>
    """.format(
        python_version=sys.version,
        django_version=django.get_version(),
        signoxe_version=git_hash.decode(),
        is_production=not settings.DEBUG,
        settings=formatted_settings
    )
    return HttpResponse(message)
