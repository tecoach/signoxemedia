# -*- coding: utf-8 -*-
""" Mixing utilities. """

from rest_framework.exceptions import PermissionDenied

from client_manager.models import ClientUserProfile


def get_owner_from_request(request):
    """
    Returns the owner associated with the user currently logged in.
    If no user is logged in, it raises a permission error.
    """
    if request.user.is_anonymous:
        raise PermissionDenied
    return get_owner_from_user(request.user)


def get_owner_from_user(user):
    try:
        userprofile = user.profile  # type: ClientUserProfile
    except ClientUserProfile.DoesNotExist:
        return None
    return userprofile.client


class AutoAddOwnerOnCreateMixin:
    """
    This mixin automatically fills in the owner when creating an object.
    It is intended to be mixed in with a Serializer class.
    """

    def create(self, validated_data: dict):
        """
        Automatically add the owner to the model based on the owner associated with the user
        currently logged in.
        """
        request = self.context.get('request')
        validated_data['owner'] = get_owner_from_request(request)
        return super().create(validated_data)


class FilterByOwnerMixin:
    """
    Filters a viewset's queryset based on the owner associated with the currently-logged-in user.
    """
    def get_queryset(self):
        """ Returns the queryset filtered by owner based on the user from the request. """
        return self.queryset.filter(owner=get_owner_from_request(self.request))


class AutoAddOwnerAdminMixin:
    """
    This mixin automatically adds an owner while saving an object without an owner in the admin
    panel.
    """
    def save_model(self, request, obj, form, change):
        """ Add owner if none is provided while saving the model via the admin panel. """
        if getattr(obj, 'owner', None) is None:
            obj.owner = get_owner_from_request(request)
        super().save_model(request, obj, form, change)
