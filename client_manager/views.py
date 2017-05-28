# -*- coding: utf-8 -*-
""" Views for the client manager app. """
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.shortcuts import render
from rest_framework.authtoken.models import Token


@staff_member_required
def login_as_user(request, user_id):
    """
    Renders the login as page with the user credentials.

    .. note:
    This view sends the username and token of the requested user to an html page, which in turn
    posts the credentials to a page hosted in the frontend subdomain. The frontend stores those
    credentials effectively logging in as that user in the frontend.
    """
    user = User.objects.get(pk=user_id)
    token, _ = Token.objects.get_or_create(user=user)
    if settings.DEBUG:
        iframe_url = 'http://192.168.1.64:3000'
    else:
        iframe_url = 'https://app.digitalnoticeboard.in/'
    # This sends the login_as_user.html page the username and token. The login_as_user.html page
    # embeds the app frontend and using the messaging api to post the login details to the embedded
    # app, which then logs in as the user.
    return render(request, 'login_as_user.html', {
        'username': user.username,
        'token': token.key,
        'iframe_url': iframe_url
    })
