# -*- coding: utf-8 -*-
import json
from urllib.parse import parse_qs

from channels import Group
from channels.sessions import channel_session
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

from client_manager.models import Client
from utils.mixins import get_owner_from_user


def get_group_for_client(client):
    """Returns a group name unique to a given client"""
    return 'updates-{client}-{id}'.format(client=client.name, id=client.id)


@channel_session
def notify_connect(message, **kwargs):
    params = parse_qs(message.content['query_string'])
    # The frontend will pass the user token as a parameter while connecting
    token = params.get(b'token', [b''])[0].decode('utf8')
    client = None
    user = None

    if token != '':
        try:
            auth = TokenAuthentication()
            user, _ = auth.authenticate_credentials(token)
            client = get_owner_from_user(user)
        except AuthenticationFailed:
            pass

    if client is not None:
        message.channel_session['username'] = user.username
        message.channel_session['client_id'] = client.id
        # Save the group name in channel session so disconnection
        # doesn't need the database
        group_name = get_group_for_client(client)
        message.channel_session['client_group'] = group_name
        Group(group_name).add(message.reply_channel)
        message.reply_channel.send({'accept': True})
    else:
        message.reply_channel.send({'close': True})


@channel_session
def notify_disconnect(message, **kwargs):
    try:
        group_name = message.channel_session['client_group']
        Group(group_name).discard(message.reply_channel)
    except (KeyError, Client.DoesNotExist):
        message.reply_channel.send({'close': True})


def refresh_client_users(client, refresh='all'):
    """
    Sends a refresh signal to all users of the same client.

    This signal can be handled by the frontend which can then refresh itself,
    thus keeping multiple users from the same client in sync.
    """
    group_name = get_group_for_client(client)
    Group(group_name).send({
        'text': json.dumps({
            'refresh': refresh
        })
    })
