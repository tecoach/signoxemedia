# -*- coding: utf-8 -*-
""" Models for the client manager app. """
from datetime import datetime, timedelta
from pathlib import PurePath

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify
from rest_framework.authtoken.models import Token

from utils.files import calculate_checksum
from utils.storage import NormalStorage


def build_upload_location(instance, filename, upload_name):
    client_dir = slugify(instance.name)
    return 'clients/{client_dir}/{upload_name}{extension}'.format(
            client_dir=client_dir,
            upload_name=upload_name,
            extension=PurePath(filename).suffix)


def upload_location_logo(instance, filename):
    return build_upload_location(instance, filename, 'logo')


def upload_location_device_logo(instance, filename):
    return build_upload_location(instance, filename, 'device_logo')


class Client(models.Model):
    """
    This model represents a client, or a customer of this app. It can be used to isolate content of
    different clients such that they cannot see each others' content or edit / manage it.
    """
    name = models.CharField(
            max_length=100,
            help_text='Name of client')

    logo = models.ImageField(
            upload_to=upload_location_logo,
            storage=NormalStorage(),
            help_text='A logo of the client for use in the frontend.')
    logo_checksum = models.CharField(
            max_length=120,
            editable=False,
            null=True,
            blank=True)

    update_interval = models.DurationField(
            default=timedelta(minutes=2),
            help_text='How often should devices check for updates')

    device_logo = models.ImageField(
            upload_to=upload_location_device_logo,
            storage=NormalStorage(),
            null=True,
            blank=True,
            help_text='A logo of the client for use on the device. '
                      'If no device logo is provided, the main logo will be used.')
    device_logo_checksum = models.CharField(
            max_length=120,
            editable=False,
            null=True,
            blank=True)
    display_device_logo = models.BooleanField(
            default=True,
            help_text='Whether a logo should be shown on the device or not.', )

    app_build_channel = models.ForeignKey(
            'devicemanager.AppBuildChannel',
            null=True,
            blank=True,
            help_text='All devices owned by this client will '
                      'receive updates published to this channel.')

    organisation_name = models.CharField(
            max_length=100,
            null=True,
            blank=True,
            help_text='Name of the organisation')
    organisation_address = models.CharField(
            max_length=255,
            null=True,
            blank=True,
            help_text='Primary address of the organisation')

    primary_contact_name = models.CharField(
            max_length=100,
            null=True,
            blank=True,
            help_text='Name of primary contact.')
    primary_contact_email = models.EmailField(
            null=True,
            blank=True,
            help_text='E-Mail address of primary contact.')
    primary_contact_phone = models.CharField(
            max_length=100,
            null=True,
            blank=True,
            help_text='Phone number of primary contact.')

    technical_contact_name = models.CharField(
            max_length=100,
            null=True,
            blank=True,
            help_text='Name of technical contact.')
    technical_contact_email = models.EmailField(
            null=True,
            blank=True,
            help_text='E-Mail address of technical contact.')
    technical_contact_phone = models.CharField(
            max_length=100,
            null=True,
            blank=True,
            help_text='Phone number of technical contact.')

    financial_contact_name = models.CharField(
            max_length=100,
            null=True,
            blank=True,
            help_text='Name of financial contact.')
    financial_contact_email = models.EmailField(
            max_length=100,
            null=True,
            blank=True,
            help_text='E-Mail address of financial contact.')
    financial_contact_phone = models.CharField(
            max_length=100,
            null=True,
            blank=True,
            help_text='Phone number of financial contact.')

    def get_logo_data(self):
        """ Returns the URL of the logo for this client. """
        if self.device_logo:
            if self.device_logo_checksum is None:
                self.save()
            return self.device_logo.url, self.device_logo_checksum
        else:
            if self.logo_checksum is None:
                self.save()
            return self.logo.url, self.logo_checksum

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.logo_checksum = calculate_checksum(self.logo)

        if self.device_logo:
            self.device_logo_checksum = calculate_checksum(self.device_logo)

        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return self.name


class ClientSubscriptionData(models.Model):
    activation_date = models.DateField(default=datetime.now)
    renewal_date = models.DateField(default=datetime.now)
    client = models.OneToOneField(Client, related_name='subscription')

    @property
    def next_renewal_date(self):
        return self.renewal_date + relativedelta(months=1)

    def __str__(self):
        return 'Subscription(Started: {}, Last Renewed: {})'.format(
                self.activation_date,
                self.renewal_date)

    class Meta:
        verbose_name_plural = 'Client Subscription Data'
        verbose_name = 'Client Subscription Data'


class ClientUserProfile(models.Model):
    """
    This model connects the user model to the client model allowing users to be associated with a
    client and limits the data they can interact with to that associated with the client.
    """
    user = models.OneToOneField(User, related_name='profile')
    client = models.ForeignKey(Client)

    def __str__(self):
        return '"{user}" of "{client}"'.format(user=self.user, client=self.client)


class ClientSettings(models.Model):
    client = models.OneToOneField(Client, related_name='settings')
    idle_detection_enabled = models.BooleanField(
            default=False,
            help_text='Should the app auto-launch during idle periods.')
    idle_detection_threshold = models.PositiveSmallIntegerField(
            default=15,
            help_text='How long (in minutes) should the device be idle before '
                      'the app is launched.')

    def __str__(self):
        return 'Settings for {}'.format(self.client)


class Features(models.Model):
    client = models.OneToOneField(Client, related_name='features')
    screenshots = models.BooleanField(
            default=False,
            help_text='Enables or disable the screenshot feature for the client.')
    smart_notice_board = models.BooleanField(
            default=False,
            help_text='Enabled or disables smart notice board support. '
                      'This includes support for the Windows client with idle '
                      'detection, scheduled launching, and push messaging.')

    def __str__(self):
        return 'Feature set for {}'.format(self.client)


# noinspection PyUnusedLocal
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """ Automatically creates a new token for a user when a new user is added. """
    if created:
        Token.objects.create(user=instance)
