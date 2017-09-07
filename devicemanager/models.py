# -*- coding: utf-8 -*-
""" Models for the device manager app. """
import datetime
import logging
import uuid
from pathlib import Path
from subprocess import CalledProcessError

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from django_hosts.resolvers import reverse
from faker import Faker
from raven.contrib.django.raven_compat.models import client

from client_manager.models import Client
from mediamanager.models import Asset, ContentFeed, PlaylistItem, Ticker
from schedule_manager.models import ScheduledContent, SpecialContent, WeekDays
from utils.files import calculate_checksum, generate_image_thumbnail
from utils.storage import NormalStorage

fake = Faker()
logger = logging.getLogger(__name__)


class ScreenOrientation:
    LANDSCAPE = 'LANDSCAPE'
    REVERSE_LANDSCAPE = 'REVERSE_LANDSCAPE'
    PORTRAIT = 'PORTRAIT'
    REVERSE_PORTRAIT = 'REVERSE_PORTRAIT'

    CHOICES = ((LANDSCAPE, 'Landscape'),
               (REVERSE_LANDSCAPE, 'Landscape Reversed'),
               (PORTRAIT, 'Portrait'),
               (REVERSE_PORTRAIT, 'Portrait Reversed'),)


class MirrorServer(models.Model):
    name = models.CharField(max_length=255, help_text='A name for the mirror server.')
    mirror_id = models.UUIDField(editable=False)
    address = models.CharField(max_length=255, null=True, blank=True,
                               help_text='The local address of the mirror at which devices can '
                                         'connect to it.')
    owner = models.ForeignKey(Client, null=True, blank=True, on_delete=models.SET_NULL)
    last_ping = models.DateTimeField(editable=False, default=timezone.now)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """ Returns the url for this mirror. """
        return reverse('mirror-feed-view', args=[str(self.mirror_id)], host='devices')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):

        # For new mirrors assign a random uuid4 as the mirror id.
        if self.mirror_id is None:
            self.mirror_id = uuid.uuid4()

        # Make sure that the mirror address ends with a /
        if self.address is not None and not self.address.endswith('/'):
            self.address = self.address + '/'

        super().save(force_insert, force_update, using, update_fields)


class DeviceGroup(models.Model):
    """
    This model represents a device group.
    """
    name = models.CharField(max_length=255)
    feed = models.ForeignKey(ContentFeed, null=True, blank=True, on_delete=models.SET_NULL)
    owner = models.ForeignKey(Client, null=True, blank=True, on_delete=models.SET_NULL)
    display_date_time = models.BooleanField(default=False)
    mirror = models.ForeignKey(MirrorServer, null=True, blank=True)
    orientation = models.CharField(
            max_length=20,
            default=ScreenOrientation.LANDSCAPE,
            choices=ScreenOrientation.CHOICES)

    def get_priority_message(self):
        """Returns the priority message for this group if any."""
        try:
            if self.prioritymessage.is_active():
                return self.prioritymessage.message.as_dict()
        except PriorityMessage.DoesNotExist:
            return None

    def get_special_content(self, date=None):
        """ Returns the special content associated with this device group for today if any. """
        try:
            date = date or datetime.date.today()
            special_content = self.specialcontent_set.get(date=date)
            return special_content
        except SpecialContent.DoesNotExist:
            return None

    def get_scheduled_content(self):
        """ Returns the content scheduled for the current timeslot for the current weekday """
        time_now = datetime.datetime.now().time()
        # First priority goes to the scheduled content for the current time.
        try:
            scheduled_content = self.scheduledcontent_set.get(
                    day=WeekDays.today(),
                    start_time__lte=time_now,
                    end_time__gt=time_now,
                    default=False,
            )
            return scheduled_content
        except ScheduledContent.DoesNotExist:
            pass

        # If there is no scheduled content for the current time slot, return the default scheduled
        # content for the day.
        try:
            default_scheduled_content = self.scheduledcontent_set.get(
                    day=WeekDays.today(),
                    default=True,
            )
            return default_scheduled_content
        except ScheduledContent.DoesNotExist:
            return None

    def _get_group_content_feed(self):
        # For a device group, the first priority for content is the special content for this date
        special_content = self.get_special_content()

        if special_content is not None:
            return special_content.content

        # Second priority is the scheduled content for the weekday / time.
        scheduled_content = self.get_scheduled_content()
        if scheduled_content is not None:
            return scheduled_content.content

        # Finally if all else fails return the main content feed.
        # (this shouldn't happen for devices with a schedule)
        return self.feed

    def priority_feed(self):
        """Returns the priority feed dictionary."""
        priority_message = self.get_priority_message()
        if priority_message is not None:
            return {'bringToFront': True, 'priorityMessage': priority_message}

        scheduled_content = self.get_scheduled_content()
        if scheduled_content is not None and scheduled_content.bring_to_front:
            return {'bringToFront': True, 'priorityMessage': None}

        return {'bringToFront': False, 'priorityMessage': None}

    def get_group_feed(self):
        """ Returns the content feed for this device group. """
        return self._get_group_content_feed().as_dict()

    def delete(self, using=None, keep_parents=False):
        """ Handles deleting a device group. """
        # If a content feed was automatically created for this group, delete it otherwise let it
        # be since it might be used by other device groups.
        if self.feed and self.feed.auto_created:
            self.feed.delete()
        return super().delete(using, keep_parents)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Device Group'
        verbose_name_plural = 'Device Groups'


class Device(models.Model):
    """
    This model represents a device connected to the service.
    """

    # Supported commands
    REBOOT_COMMAND = 'reboot'
    FREESPACE_COMMAND = 'free-space'
    CLEAR_COMMAND = 'clear-media'
    RESET_COMMAND = 'reset-device'
    SET_REALM_DEV = 'change-realm:dev'
    SET_REALM_STAGING = 'change-realm:stage'
    SET_REALM_LIVE = 'change-realm:live'
    TAKE_SCREENSHOT = 'screenshot'
    TAKE_SCREENSHOT_BURST = 'screenshot:burst'
    COMMANDS = (
        (REBOOT_COMMAND, 'Reboot Device'),
        (FREESPACE_COMMAND, 'Delete Unused Media'),
        (CLEAR_COMMAND, 'Clear All Device Media'),
        (RESET_COMMAND, 'Reset Device'),
        (SET_REALM_DEV, 'Device Realm: development'),
        (SET_REALM_STAGING, 'Device Realm: staging'),
        (SET_REALM_LIVE, 'Device Realm: live'),
        (TAKE_SCREENSHOT, 'Take screenshot'),
        (TAKE_SCREENSHOT_BURST, 'Take screenshot burst'),
    )

    device_id = models.UUIDField()
    name = models.CharField(max_length=255)
    last_ping = models.DateTimeField(editable=False, default=timezone.now)
    group = models.ForeignKey(DeviceGroup, null=True, blank=True, on_delete=models.SET_NULL)
    debug_mode = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    owner = models.ForeignKey(Client, null=True, blank=True, on_delete=models.SET_NULL)
    build_version = models.PositiveIntegerField(null=True, blank=True, editable=False)
    command = models.CharField(max_length=20, null=True, blank=True,
                               choices=COMMANDS)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """ Adds extra logic for when a new device is being saved. """
        if not self.name:
            # Generate a fake name for the device if none provided.
            self.name = ' '.join(fake.words(2)).title()
        super().save(force_insert, force_update, using, update_fields)

    def get_absolute_url(self):
        """ Returns the url for this device as accessed by the device. """
        return reverse('device-feed-view', args=[str(self.device_id)], host='devices')

    def __str__(self):
        return self.name


def screenshot_upload_location(instance, filename=''):
    # type: (DeviceScreenShot, str) -> str
    """ Builds an upload location for device screenshots. """
    # Screenshots will be placed in teh screenshots folder, with a subdirectory for each
    # device.
    return 'screenshots/{device_id}/{timestamp:%Y-%m-%d_%H.%M.%S.%f%z}.jpg'.format(
            device_id=instance.device.device_id,
            timestamp=timezone.now()
    )


class DeviceScreenShot(models.Model):
    device = models.ForeignKey(Device)
    image = models.ImageField(storage=NormalStorage(),
                              upload_to=screenshot_upload_location)
    thumbnail = models.CharField(max_length=255, null=True, blank=True, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def get_thumbnail_path(self):
        # Returns the same path as the image, but with a tn_ prepended
        image_path = Path(self.image.name)
        return str(image_path.with_name('tn_' + image_path.name))

    def _generate_thumbnail(self, force=False):
        storage = NormalStorage()
        thumbnail_path = self.get_thumbnail_path()

        if force or not storage.exists(thumbnail_path):  # Thumbnail doesn't exist, generate it.
            try:
                thumbnail = generate_image_thumbnail(self.image, 384, 216)
                storage.save(thumbnail_path, thumbnail)
                self.thumbnail = storage.url(thumbnail_path)
                self.save()
            except CalledProcessError:
                client.captureException()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)
        if self.thumbnail is None:
            self._generate_thumbnail()

    def __str__(self):
        return 'Screenshot of {device} on {timestamp:%Y-%m-%d_%H.%M.%S}'.format(
                device=self.device,
                timestamp=self.timestamp,
        )


@receiver(pre_delete, sender=DeviceScreenShot)
def device_screen_shot_delete(sender, instance, **kwargs):
    # type: (DeviceScreenShot, DeviceScreenShot) -> None
    # Delete the screenshot file when deleting the screenshot entry from the database.
    thumbnail_path = instance.get_thumbnail_path()
    instance.image.delete(save=False)
    storage = NormalStorage()
    if storage.exists(thumbnail_path):
        storage.delete(thumbnail_path)


class AppBuildChannel(models.Model):
    """ App Build Channels allow creating distinct update channels for app builds. """

    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


def build_upload_location(instance, filename):
    """ Returns the location where app builds can be saved """
    # type: (AppBuild, str) -> str
    channel = instance.release_channel or '--default--'
    return 'appbuilds/{channel}/signoxe-v{version}.apk'.format(channel=channel,
                                                               version=instance.version_code)


class AppBuild(models.Model):
    """ App Builds store builds of the android client that can be pushed to devices. """
    version_code = models.PositiveIntegerField(
            help_text='The version of code of the Android application. This value should always '
                      'increase. The app build with the highest version will be pushed to the '
                      'devices.')
    app_build = models.FileField(upload_to=build_upload_location,
                                 storage=NormalStorage(),
                                 help_text='The app APK file.')
    release_channel = models.ForeignKey(AppBuildChannel, null=True, blank=True,
                                        help_text='Pick a release channel for this build. Devices '
                                                  'will get latest build in the channel they are '
                                                  'subscribed to.')
    checksum = models.CharField(max_length=120, editable=False)

    def __str__(self):
        return 'Signoxe App build {}'.format(self.version_code)

    def clean(self):
        """ Makes sure an existing uploaded build cannot be edited. """
        if self.pk:
            raise ValidationError('Cannot edit a build after it has been added.')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """ Adds app file checksum. """
        if not self.pk:
            self.checksum = calculate_checksum(self.app_build)
        super().save(force_insert, force_update, using, update_fields)

    @classmethod
    def get_latest_app_manifest(cls, build_channel):
        """
        Creates a manifest dict containing the version, the apk url and checksum for the latest
        build of the app.
        """
        channel_builds = cls.objects.filter(release_channel=build_channel)
        latest_build = channel_builds.order_by('-version_code').first()
        if latest_build is None:
            # In case no latest build is present for the channel, return a basic update manifest
            # that will work on the device.
            return {
                'version': 1,
                'update_url': '',
                'checksum': '',
            }
        update_url = latest_build.get_absolute_url()
        return {
            'version': latest_build.version_code,
            'update_url': update_url,
            'checksum': latest_build.checksum,
        }

    def get_absolute_url(self):
        """ Returns path to the app apk file. """
        return self.app_build.url


class PriorityMessage(models.Model):
    device_group = models.OneToOneField(DeviceGroup)
    activated_on = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(
            null=True, blank=True,
            choices=((0, 'Indefinite'),
                     (15, '15 Minutes'),
                     (30, '30 Minutes'),
                     (45, '45 Minutes'),
                     (60, '60 Minutes'),))
    message = models.ForeignKey(Asset, null=True, blank=True)

    def is_active(self):
        # If the priority message is not fully defined, it is inactive.
        if self.activated_on is None or self.duration is None or self.message is None:
            return False

        # If the duration is set to 0, and the message is active, then it will
        # stay on indefinitely.
        if self.duration == 0 and self.activated_on:
            return True

        # If the message duration hasn't elapsed, the message is active. Else deactivate it.
        end_time = self.activated_on + timezone.timedelta(minutes=self.duration)
        if timezone.now() <= end_time:
            return True
        else:
            self.deactivate()
            return False

    def deactivate(self):
        """Deactivates the priority message."""
        self.activated_on = None
        self.save()

    def __str__(self):
        return '{} Priority Message'.format(self.device_group)


def clear_cache_for_devices(device_query):
    """Clears the cache for all devices in the supplied query."""
    device_ids = [device_id.hex
                  for device_id in device_query.values_list('device_id', flat=True)]
    logger.info('clearing cache for devices: {}'.format(device_ids))
    cache.delete_many(device_ids)


@receiver(post_save)
@receiver(pre_delete)
def clear_cache_on_save_delete(sender, instance, **kwargs):
    """Clears the cache when there are any changes that would affect device feeds."""
    if isinstance(instance, Device):
        cache.delete(str(instance.device_id).replace('-', ''))
    elif isinstance(instance, DeviceGroup):
        clear_cache_for_devices(instance.device_set)
    elif isinstance(instance, ContentFeed):
        clear_cache_for_devices(Device.objects.filter(group__in=instance.devicegroup_set.all()))
    elif isinstance(instance, Ticker):
        clear_cache_for_devices(Device.objects.filter(owner=instance.ticker_series.owner))
    elif isinstance(instance, PlaylistItem):
        clear_cache_for_devices(Device.objects.filter(owner=instance.playlist.owner))
    elif isinstance(instance, (ScheduledContent, SpecialContent, PriorityMessage)):
        clear_cache_for_devices(instance.device_group.device_set)
    else:
        try:
            clear_cache_for_devices(instance.owner.device_set)
        except AttributeError:  # Above an trigger this error if object doesn't have an owner.
            logger.debug('Unhandled signal for {}'.format(sender))
            pass
