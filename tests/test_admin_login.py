# -*- coding: utf-8 -*-
from pytest_bdd import scenarios, then

scenarios('features/admin_login.feature')


@then('Login should succeed')
def successful_login(client):
    response = client.get('/admin/')
    assert response.status_code == 200


@then('Login should not succeed')
def failed_login(client):
    response = client.get('/admin/')
    assert response.status_code != 200
