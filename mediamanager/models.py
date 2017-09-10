# -*- coding: utf-8 -*-
""" Models for the media manager app. """
import datetime
import json
from pathlib import Path
from subprocess import CalledProcessError
from uuid import uuid4

import hashlib
import os
import re
import requests
from channels import Channel
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.template import Context, Template
from django.utils import timezone
from django.utils.text import Truncator
from django_hosts.resolvers import reverse
from icalendar import Calendar
from mistune import markdown
from raven.contrib.django.raven_compat.models import client
from taggit.managers import TaggableManager

from client_manager.models import Client
from mediamanager.types import AssetTypes
from utils.errors import InvalidAssetError, NoContentAssetError
from utils.files import (clean_image_metadata, clean_video_metadata, generate_image_thumbnail,
                         generate_video_thumbnail, generate_web_thumbnail, md5_file_name)
from utils.storage import NormalStorage

THUMBNAIL_STORAGE = NormalStorage()


class TickerSpeeds:
    """ This class consolidates the data about ticker speed choices into a single class. """
    FASTEST = 100
    FASTER = 200
    FAST = 300
    NORMAL = 400
    SLOW = 500
    SLOWER = 600
    SLOWEST = 700

    #: Choices that a Django field can use.
    CHOICES = (
        (FASTEST, 'FASTEST'),
        (FASTER, 'FASTER'),
        (FAST, 'FAST'),
        (NORMAL, 'NORMAL'),
        (SLOW, 'SLOW'),
        (SLOWER, 'SLOWER'),
        (SLOWEST, 'SLOWEST'),
    )


class TickerSeries(models.Model):
    """
    This model represents a ticker series. A ticker series is a collection of tickers ordered by
    position.
    """
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(Client, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name

    def as_list(self):
        """
        Returns this tickers in this ticker series as a pure python list ordered by their
        position.
        """
        return [ticker.as_dict() for ticker in self.ticker_set.order_by('position')]

    class Meta:
        verbose_name = 'Ticker Series'
        verbose_name_plural = 'Ticker Series'


class Ticker(models.Model):
    """
    Represents a single ticker in a ticker series.
    """
    text = models.TextField()
    speed = models.IntegerField(
            choices=TickerSpeeds.CHOICES,
            default=TickerSpeeds.NORMAL)
    font_family = models.CharField(
            default='sans',
            max_length=100,
            null=True,
            blank=True)
    font_size = models.DecimalField(
            default=22,
            max_digits=4,
            decimal_places=1,
            null=True,
            blank=True)
    colour = models.CharField(
            default='#000000',
            max_length=10,
            null=True,
            blank=True)
    outline = models.CharField(
            default='',
            max_length=10,
            null=True,
            blank=True)
    background = models.CharField(
            default='#FFFFFF',
            max_length=10,
            null=True,
            blank=True)
    position = models.PositiveIntegerField()
    ticker_series = models.ForeignKey(TickerSeries)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """ Adds extra logic to add a position for a ticker when it is newly added. """
        if self.position is None:
            # Get the ticker with the largest position value. This works
            # because tickers are already ordered by position.
            last_ticker = self.ticker_series.ticker_set.last()
            if last_ticker is None:
                self.position = 0  # No tickers in the series yet, set position to 0.
            else:
                self.position = last_ticker.position + 1
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return Truncator(self.text).words(10)

    def as_dict(self):
        """
        Returns a dictionary representation of this ticker so it can be included as-in in a feed.
        """
        return {
            'text': self.text,
            'speed': self.speed,
            'fontfamily': self.font_family,
            'fontsize': self.font_size,
            'color': self.colour,
            'outline': self.outline,
            'background': self.background,
        }

    class Meta:
        ordering = ('position',)


class Asset(models.Model):
    """
    This models servers as a base for all kinds of assets and includes data common to all assets. s
    """
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=25, editable=False)
    raw_metadata = models.TextField(editable=False, blank=True)
    metadata = models.TextField(editable=False, blank=True)
    asset_url = models.CharField(max_length=255, editable=False)
    thumbnail = models.CharField(max_length=255, null=True, blank=True, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(Client, null=True, blank=True, on_delete=models.SET_NULL)

    tags = TaggableManager()

    def get_tags_list(self):
        return self.tags.names()

    def build_clean_metadata(self):
        if self.type == AssetTypes.VIDEO:
            self.metadata = clean_video_metadata(self.get_raw_metadata_as_dict())
        elif self.type == AssetTypes.IMAGE:
            self.metadata = clean_image_metadata(self.get_raw_metadata_as_dict())

    def get_metadata_as_dict(self):
        if self.metadata is None or self.metadata == '':
            return None
        return json.loads(self.metadata)

    def get_raw_metadata_as_dict(self):
        if self.raw_metadata is None or self.raw_metadata == '':
            return None
        return json.loads(self.raw_metadata)

    def get_subtype(self):
        """
        Uses the stored type to figure out the type of the asset and accordingly returns the
        associated child class.
        """
        if self.type == AssetTypes.VIDEO:
            return self.videoasset
        elif self.type == AssetTypes.IMAGE:
            return self.imageasset
        elif self.type == AssetTypes.WEB:
            return self.webasset
        elif self.type == AssetTypes.FEED:
            return self.feedasset
        elif self.type == AssetTypes.CALENDAR:
            return self.calendarasset
        else:
            raise ValueError

    def get_absolute_url(self):
        """ Returns a friendly url for this asset. """
        return reverse('asset-view', args=[str(self.pk)], host='content')

    def get_asset_url(self):
        """
        Returns a direct url for this asset. It also caches the url into a field in the model.
        """
        self._save_asset_url()
        return self.asset_url

    def as_dict(self):
        return self.get_subtype().as_dict()

    def _save_asset_url(self, force=False):
        """
        Save the asset url to the field in the model so it doesn't need to be calculated each time.
        """
        if force or not self.asset_url:
            self.asset_url = self.get_subtype().get_asset_url()
            self.save()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """ Adds logic to save the asset URL while saving if one is not already present. """
        super().save(force_insert, force_update, using, update_fields)
        self._save_asset_url()

    def __str__(self):
        return self.name

    def add_thumbnail(self, force):
        if self.thumbnail is None or force:
            try:
                self._get_or_generate_thumbnail(force=force)
                self.save()
            except CalledProcessError:
                client.captureException()

    def _get_or_generate_thumbnail(self, force=False):
        storage = THUMBNAIL_STORAGE
        if self.thumbnail is None:
            thumbnail_path = self._get_thumbnail_path()
        else:
            thumbnail_path = str(Path(self.thumbnail).relative_to(storage.url('/')))

        if force or not storage.exists(thumbnail_path):  # Thumbnail doesn't exist, generate it.
            thumbnail = self.generate_thumbnail()
            storage.save(thumbnail_path, thumbnail)
            self.thumbnail = storage.url(thumbnail_path)

        return storage.url(thumbnail_path)

    def _get_thumbnail_path(self):
        raise NotImplementedError()

    def generate_thumbnail(self):
        """ Thumbnails can only be generated for specific types of assets """
        raise NotImplementedError


class FileAsset(Asset):
    """
    This model serves as a base for all file-based assets such as a images and videos. It is an
    abstract includes data common to file-based assets.
    """
    media_file = models.FileField(upload_to=md5_file_name, )
    checksum = models.CharField(max_length=120, editable=False)

    def _get_thumbnail_path(self):
        # This gets the filename and path within the media folder.
        _, filename_with_ext = os.path.split(self.media_file.name)
        filename, ext = os.path.splitext(filename_with_ext)
        # The thumbnail name is simply tn_ prepended to the hashed file name.
        thumbnail_name = '{}.jpeg'.format(filename)
        # The thumbnail is stored it the same path.
        thumbnail_path = os.path.join('thumbnails', self.type.lower(), thumbnail_name)
        return thumbnail_path

    def generate_thumbnail(self):
        """ Generates the correct thumbnail for asset type and returns thumbnail image data. """
        return self.get_subtype().generate_thumbnail()

    def save(self, *args, **kwargs):
        """
        Adds logic to save the type of the model for the field so no unnecessary lookups are
        required while accessing a child model from the Asset model.
        """
        if hasattr(self, 'TYPE'):
            self.type = self.TYPE
        if not self.pk:
            # If this is a newly-created asset, here we calculate the md5 hash for the file and
            # store it in the checksum field
            md5 = hashlib.md5()
            for chunk in self.media_file.chunks():
                md5.update(chunk)
            self.checksum = md5.hexdigest()
        super().save(*args, **kwargs)

    def get_asset_url(self):
        """ Returns the direct URL for the file associated with this asset. """
        return self.media_file.url

    class Meta:
        abstract = True


class VideoAsset(FileAsset):
    """ This model represents a Video Asset. """
    TYPE = AssetTypes.VIDEO

    def generate_thumbnail(self):
        """ Generates thumbnail for video asset and returns thumbnail image data. """
        return generate_video_thumbnail(source=self.media_file.url,
                                        width=settings.SIGNOXE_THUMBNAIL_WIDTH,
                                        height=settings.SIGNOXE_THUMBNAIL_HEIGHT)

    def as_dict(self):
        """ Returns a dictionary representation of this video asset. """
        return {
            'url': self.media_file.url,
            'checksum': self.checksum,
            'type': 'video',
        }


class ImageAsset(FileAsset):
    """ This model represents an Image Asset. """
    TYPE = AssetTypes.IMAGE

    def generate_thumbnail(self):
        """ Generates thumbnail for image asset and returns thumbnail image data. """
        return generate_image_thumbnail(source=self.media_file,
                                        width=settings.SIGNOXE_THUMBNAIL_WIDTH,
                                        height=settings.SIGNOXE_THUMBNAIL_HEIGHT)

    def as_dict(self):
        """ Returns a dictionary representation of this image asset. """
        return {
            'url': self.media_file.url,
            'checksum': self.checksum,
            'type': 'image',
        }


class WebAsset(Asset):
    """ This model represents a Web Asset. """
    TYPE = AssetTypes.WEB
    content = models.TextField(null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)

    def _get_thumbnail_path(self):
        return 'thumbnails/web/tn_wa{}-{}.jpeg'.format(self.id, uuid4().hex)

    def generate_thumbnail(self):
        """ Generates thumbnail for web asset and returns thumbnail image data. """
        return generate_web_thumbnail(source=self.get_asset_url(),
                                      width=settings.SIGNOXE_THUMBNAIL_WIDTH,
                                      height=settings.SIGNOXE_THUMBNAIL_HEIGHT)

    def clean(self):
        """
        Validates that a web asset includes at least one, and only one of the fields between url
        and content.
        """
        if not self.url and not self.content:
            raise ValidationError('Web Asset must include at least one of "url" and "content"')

    def save(self, *args, **kwargs):
        """ Adds the extra logic of setting the type while saving the model. """
        if hasattr(self, 'TYPE'):
            self.type = self.TYPE
        super().save(*args, **kwargs)

    def get_asset_url(self):
        """ Returns the asset's url field or the content rendered in the page. """
        if self.url:
            return self.url
        else:
            return reverse('webasset-view', args=[self.pk], host='content')

    @property
    def checksum(self):
        """Calculates checksum for Web asset based on content."""
        md5 = hashlib.md5()
        md5.update(self.content.encode('utf-8'))
        return md5.hexdigest()

    def as_dict(self):
        """ Returns a dictionary representation of this web asset. """
        return {
            'url': self.get_asset_url(),
            'checksum': self.checksum,
            'type': 'web',
        }

    class Meta:
        verbose_name = 'Web Asset'
        verbose_name_plural = 'Web Asset'


class FeedAsset(Asset):
    """
    This model represents a Feed Asset.
    A FeedAsset behaves like a regular asset while being linked to a feed model which provides its
    content.
    """
    TYPE = AssetTypes.FEED
    feed = models.OneToOneField('feedmanager.Feed')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        Adds the type while saving. Also sets owner to None since FeedAssets
        are managed by the main site.
        """
        if hasattr(self, 'TYPE'):
            self.type = self.TYPE
        self.owner = None
        super().save(force_insert, force_update, using, update_fields)

    def get_asset_url(self):
        """ Returns the url to the asset linked to this feed. """
        return self.feed.get_absolute_url()

    def as_dict(self):
        """ Returns a dictionary representation of this asset. """
        return self.feed.as_dict()


class PlaylistItem(models.Model):
    """
    This model represents a Playlist Item.

    A PlaylistItem adds playlist-related metadata to an asset, such as the duration (unless the
    asset has an explicit duration, like a video), and a position in the playlist.
    """
    position = models.PositiveIntegerField()
    playlist = models.ForeignKey('Playlist')
    item = models.ForeignKey(Asset)
    duration = models.PositiveIntegerField(null=True, blank=True)
    expire_on = models.DateTimeField(null=True, blank=True)

    @property
    def enabled(self):
        return self.expire_on is None or timezone.now() < self.expire_on

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """ Adds logic to add a position to the playlistitem, unless one is already provided. """
        if self.position is None:
            # For new playlists there won't be an existing position, in that case set the position
            # to 0 if it's the only item in the playlist, or set one more than the largest position
            # value.
            last_item = self.playlist.playlistitem_set.last()
            if last_item is None:
                self.position = 0
            else:
                self.position = last_item.position + 1
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return '({position}) {item} in {playlist}'.format(position=self.position,
                                                          item=self.item,
                                                          playlist=self.playlist)

    class Meta:
        ordering = ('position',)


class Playlist(models.Model):
    """
    This model represents a Playlist.
    """
    name = models.CharField(max_length=255)
    items = models.ManyToManyField(Asset, through=PlaylistItem)
    auto_add_feeds = models.BooleanField(default=True)
    owner = models.ForeignKey(Client, null=True, blank=True, on_delete=models.SET_NULL)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        Adds logic to automatically add all existing feeds to this playlist if it's new and allows
        automatically adding feeds.
        """
        is_new = self.pk is None  # No primary key assigned, this Playlist is new.
        super().save(force_insert, force_update, using, update_fields)
        from feedmanager.models import Feed

        if is_new and self.auto_add_feeds:
            Feed.add_feeds_to_playlist(self)

    def __str__(self):
        return self.name

    def as_list(self):
        """
        Returns a list with the dictionary representation of all the items in this playlist.
        """
        playlist = []
        playlist_items = self.playlistitem_set.exclude(expire_on__lt=timezone.now())
        playlist_items = playlist_items.order_by('position')
        for pl_item in playlist_items:
            try:
                media_item = pl_item.item.get_subtype().as_dict()
            except (NoContentAssetError, InvalidAssetError, ObjectDoesNotExist):
                # If a feed doesn't have snippets for today (or at all), or a Calendar asset has no
                # events for right now, or has no data, it will be skipped.
                continue
            else:
                if 'duration' not in media_item:
                    media_item['duration'] = pl_item.duration
                playlist.append(media_item)

        return playlist

    def get_absolute_url(self):
        """ Returns the preview url for this playlist. """
        return reverse('playlist-view', args=[str(self.pk)], host='content')


class ContentFeed(models.Model):
    """
    This model represents a Content Feed.
    A content feed is a collection of media content, a playlist, a ticker series and other
    configuration parameters that are needed for a device to show something. It is linked to a
    device group.
    """
    title = models.CharField(max_length=100)
    media_playlist = models.ForeignKey(Playlist,
                                       null=True, blank=True,
                                       on_delete=models.SET_NULL)
    ticker_series = models.ForeignKey(TickerSeries,
                                      null=True, blank=True,
                                      on_delete=models.SET_NULL)
    image_duration = models.IntegerField(default=4500)
    web_duration = models.IntegerField(default=4500)
    overlay_ticker = models.BooleanField(default=True)
    auto_created = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def settings(self):
        """ Returns all the device settings for this feed. """
        return {
            'imageDuration': self.image_duration,
            'webDuration': self.web_duration,
            'overlayTicker': self.overlay_ticker,
            'displayTicker': self.ticker_series is not None
        }

    def as_dict(self):
        """
        Returns a dictionary representation of this content feed.
        Can raise an error if the media_playlist is missing.
        """
        if self.media_playlist is None:
            raise ContentFeed.PlaylistNotSetError('No playlist configured for device group.')
        feed_dict = {
            'playlist': self.media_playlist.as_list(),
            'tickers': self.ticker_series.as_list() if self.ticker_series else [],
            'settings': self.settings(),
        }
        return feed_dict

    class PlaylistNotSetError(AttributeError):
        """
        Custom error to throw when a playlist has not been set for this content feed. A playlist is
        essential to render a content feed.
        """
        pass

    class Meta:
        verbose_name = 'Content Feed'
        verbose_name_plural = 'Content Feeds'


class WebAssetTemplate(models.Model):
    """Web Asset Templates to make it easier for users to create web assets."""
    name = models.CharField(
            max_length=100,
            help_text='The template name is what users select on the frontend so '
                      'it should be descriptive.')
    template = models.TextField(
            help_text='This is the HTML template that will be rendered by the '
                      'client and sent as a web asset.')
    variables = models.CharField(
            max_length=200,
            help_text='The variables present in the template that will need '
                      'to be filled in by the user in the frontend.')
    help_text = models.TextField(
            help_text='Some helpful text to describe how to use this '
                      'template and it\'s variables.')
    calendar_support = models.BooleanField(default=False)
    data_support = models.BooleanField(default=False)

    @property
    def help_html(self):
        return markdown(self.help_text)

    def clean(self):
        """Validates variable names and calendar and data support."""

        if self.calendar_support and self.data_support:
            raise ValidationError('Calendar and data support cannot be enabled '
                                  'in the same template.', code='invalid')

        self.variables = self.variables.replace(' ', '')
        if re.fullmatch(r'([a-zA-Z_]*,?)*', self.variables) is None:
            raise ValidationError({
                'variables': 'You need to enter one or more variable names separated by commas',
            }, code='invalid')

    def render(self, context):
        return Template(self.template).render(Context(context))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Web Asset Template'


class CalendarAsset(Asset):
    """ This model represents a Calendar Asset. """
    TYPE = AssetTypes.CALENDAR
    template = models.ForeignKey(WebAssetTemplate, limit_choices_to={'calendar_support': True},
                                 on_delete=models.CASCADE)
    url = models.CharField(max_length=255)
    data = models.TextField(editable=False, null=True, blank=True)
    last_update = models.DateTimeField(editable=False, null=True, blank=True)

    def save(self, *args, **kwargs):
        """ Adds the extra logic of setting the type while saving the model. """
        self.type = self.TYPE
        super().save(*args, **kwargs)

    def get_asset_url(self):
        """ Returns the asset's url field or the content rendered in the page. """
        return reverse('calasset-view', args=[self.pk], host='content')

    def update_calendar_data(self):
        """ Fetches latest ics data from the url and caches it. """
        self.data = requests.get(self.url).text
        self.last_update = timezone.now()
        self.save()

    def validate(self):
        if self.data is None:
            raise InvalidAssetError

    def get_current_event(self):
        self.validate()
        try:
            cal = Calendar.from_ical(self.data)
            for event in cal.subcomponents:
                start = event.decoded('DTSTART')
                end = event.decoded('DTEND')

                if isinstance(start, datetime.datetime):
                    now = timezone.now()
                else:
                    now = timezone.now().date()

                if start <= now <= end:
                    return {
                        'title': event.decoded('SUMMARY').decode('utf-8'),
                        'content': event.decoded('DESCRIPTION').decode('utf-8'),
                    }
        except (ValueError, KeyError):
            #  The calendar has returned invalid data, this asset is invalid.
            raise InvalidAssetError

    @property
    def rendered_content(self):
        cal_data = self.get_current_event()
        if cal_data is None:
            raise NoContentAssetError
        else:
            return self.template.render(cal_data)

    @property
    def checksum(self):
        """ Calculates checksum for calendar asset based on content. """
        md5 = hashlib.md5()
        md5.update(self.rendered_content.encode('utf-8'))
        return md5.hexdigest()

    def as_dict(self):
        """ Returns a dictionary representation of this web asset. """
        return {
            'url': self.get_asset_url(),
            'checksum': self.checksum,
            'type': 'web',
        }


# noinspection PyUnusedLocal
def build_metadata_and_thumbnails(sender, instance=None, created=False, **kwargs):
    if isinstance(instance, VideoAsset):
        Channel('update-video-metadata').send({'ids': [instance.id]})
    elif isinstance(instance, ImageAsset):
        Channel('update-image-metadata').send({'ids': [instance.id]})
    if created:
        Channel('create-thumbnail').send({'ids': [instance.id]})


post_save.connect(build_metadata_and_thumbnails, sender=VideoAsset)
post_save.connect(build_metadata_and_thumbnails, sender=ImageAsset)
post_save.connect(build_metadata_and_thumbnails, sender=WebAsset)
