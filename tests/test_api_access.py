# -*- coding: utf-8 -*-
from pytest_bdd import given, scenarios, then
from rest_framework.test import APIClient

scenarios('features/api_access.feature')


@given('I request an auth token')
def api_client(user_object):
    client = APIClient()
    response = client.post('/api/auth/token/create/', {'username': user_object.username,
                                                       'password': 'test_user_password'})
    assert response.status_code == 200, 'Login Failed'
    token = response.json()['auth_token']

    assert len(token) == 40, 'Invalid token'

    client.credentials(HTTP_AUTHORIZATION='Token {}'.format(token))

    return client


@then('I should be able to access my profile API')
def access_profile_page(api_client):
    response = api_client.get('/api/auth/me/')
    assert response.status_code == 200, 'Failed to access profile page'


@then('I should be able to access the API <api>')
def access_api(api_client, api):
    response = api_client.get('/api/{}/'.format(api))
    assert response.status_code == 200, 'Failed to access api {}'.format(api)
