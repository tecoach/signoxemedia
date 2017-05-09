# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from pytest_bdd import given
from pytest_bdd.parsers import parse


@given(parse("I'm a {user_type} user"))
def user_object(user_type, transactional_db):
    UserModel = get_user_model()
    user = UserModel.objects.create_user('{}_user'.format(user_type),
                                         password='test_user_password')
    if user_type == 'super':
        user.is_staff = True
        user.is_superuser = True
    elif user_type == 'staff':
        user.is_staff = True
    user.save()
    return user


@given('I log in')
def logged_in_client(user_object, client):
    assert client.login(username=user_object.username, password='test_user_password')
    return client
