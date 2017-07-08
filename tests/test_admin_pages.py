# -*- coding: utf-8 -*-
from pytest_bdd import scenarios, then

scenarios('features/admin_pages.feature')


@then('I should be able to access <page> of <app>')
def access_admin_page(client, app, page):
    response = client.get('/admin/{app}/{page}/'.format(app=app, page=page))
    assert response.status_code == 200


@then('Access the add page')
def access_admin_page(client, app, page):
    response = client.get('/admin/{app}/{page}/add/'.format(app=app, page=page))
    assert response.status_code == 200
