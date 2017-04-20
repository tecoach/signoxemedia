# -*- coding: utf-8 -*-
""" Admin configuration for client manager app. """
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django_hosts import reverse

from client_manager.models import (Client, ClientSettings, ClientSubscriptionData,
                                   ClientUserProfile, Features, )


class ClientUserProfileAdminInline(admin.StackedInline):
    """
    This inline admin config allow a user to associate a client with a user from the backend panel
    """
    model = ClientUserProfile
    can_delete = False


def user_login_link(obj):
    link = reverse('login-as-view', args=[str(obj.pk)], host='admin')
    return format_html('<a href="{link}" target="_blank">'
                       'View frontend as {username}'
                       '</a>'.format(link=link, username=obj.username))


class AppUserAdmin(UserAdmin):
    """
    This admin class extends the user admin setup to include the client user profile as a
    configurable option.
    """
    inlines = (ClientUserProfileAdminInline,)
    list_display = ('username', user_login_link, 'email', 'first_name', 'last_name', 'is_staff')


class ClientSubscriptionDataAdminInline(admin.StackedInline):
    """Inline admin config for Client Subscription data."""
    model = ClientSubscriptionData
    can_delete = False


class ClientSettingsAdminInline(admin.StackedInline):
    """Inline admin config for Client Settings."""
    model = ClientSettings
    can_delete = False


class FeaturesAdminInline(admin.StackedInline):
    """Inline admin config for Client Features."""
    model = Features
    can_delete = False


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'app_build_channel'),
        }),
        ('Logo', {
            'fields': (('logo',), ('display_device_logo', 'device_logo',), ('update_interval',))
        }),
        ('Profile', {
            'fields': (
                ('organisation_name', 'organisation_address',),
                ('primary_contact_name', 'primary_contact_email', 'primary_contact_phone',),
                ('technical_contact_name', 'technical_contact_email', 'technical_contact_phone',),
                ('financial_contact_name', 'financial_contact_email', 'financial_contact_phone',),
            ),
        })
    )
    inlines = (ClientSubscriptionDataAdminInline, ClientSettingsAdminInline, FeaturesAdminInline)


# The user model is already registered, we need to un-register it before we can register our own
# custom user admin class
admin.site.unregister(User)
admin.site.register(User, AppUserAdmin)
