# -*- coding: utf-8 -*-
""" Models for the feed manager app. """
from datetime import date

import hashlib
from django import template
from django.core.exceptions import ValidationError
from django.db import models
from django.template import Context
from django.utils import timezone
from django.utils.text import slugify
from django_hosts.resolvers import reverse

from client_manager.models import Client
from mediamanager.models import FeedAsset, Playlist
from mediamanager.types import AssetTypes
from utils.files import md5_file_name


def md5_checksum(content):
    """Calculates md5_checksum text content """
    md5 = hashlib.md5()
    md5.update(content.encode('utf-8'))
    return md5.hexdigest()


class Category(models.Model):
    """
    This model represents a category for Feeds.
    A category can be date-based or random. In the first case the contents of the category are
    sensitive to date, for instance a category like "This day in History" only makes sense if the
    content being shown is for the correct date.
    A random category is one where the content needs to change each day, but the content itself is
    not date sensitive.
    """
    RANDOM_TYPE = 'RANDOM'
    DATED_TYPE = 'DATED'
    TYPES = ((RANDOM_TYPE, 'Random'),
             (DATED_TYPE, 'Dated'))
    name = models.CharField(max_length=100,
                            help_text='Enter a helpful name for this feed category. Example: '
                                      '<em>"Word of the Day"</em>')
    type = models.CharField(max_length=10,
                            choices=TYPES,
                            help_text='Select whether this option is time-sensitive or not.'
                                      'For a time-sensitive category '
                                      '(e.g. "This day in history"), '
                                      'only content relevant to the current date will be fetched.')

    def get_snippets(self, snippet_type):
        """
        Returns the snippets associated with this category while applying the
        date filter if needed.
        """
        snippets = snippet_type.objects.filter(category=self)
        if self.type == 'DATED':
            snippets = snippets.filter(date=timezone.now().date())
        return snippets

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'


class Snippet(models.Model):
    """
    This model represents a Snippet.
    A snippet is a small piece of content and this class serves as a base for the Image, Video, and
    Web snippet classes.
    """
    title = models.CharField(max_length=255,
                             null=True, blank=True,
                             help_text='Pick a good topic or title for the snippet. In some cases '
                                       'this might be visible to end-users. ')
    date = models.DateField(null=True, blank=True,
                            help_text='Enter a date here if this snippet is date-sensitive. This '
                                      'will only have an effect if the snippet category itself is '
                                      'date-sensitive.')
    category = models.ForeignKey(Category,
                                 help_text='Select which category should display this snippet.')

    def __str__(self):
        return self.title


class WebSnippet(Snippet):
    """
    This model represents a web snippet.
    A web snippet stores a bunch of text content to render on the device.
    """
    content = models.TextField(help_text='This is the actual content of the web snippet. How and '
                                         'where it appears depends on the template used to render '
                                         'it. Some templates strip HTML content.')


class FileSnippet(Snippet):
    """
    This model serves as a base for file-based snippets.
    It includes data and functionality common for any file-based snippet type.
    """
    media = models.FileField(upload_to=md5_file_name,
                             help_text='This is the media file that will be served in the feed '
                                       'directly.')
    checksum = models.CharField(max_length=120, editable=False)

    def save(self, *args, **kwargs):
        """
        Adds logic to create an MD5 checksum of uploaded file and save it to the checksum field of
        the model.
        """
        if not self.pk:
            md5 = hashlib.md5()
            for chunk in self.media.chunks():
                md5.update(chunk)
            self.checksum = md5.hexdigest()
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class ImageSnippet(FileSnippet):
    """ This model represents an ImageSnippet. """
    pass


class VideoSnippet(FileSnippet):
    """ This model represents an VideoSnippet. """
    pass


class Template(models.Model):
    """
    This model represents a Template.
    This store a template in the Django template format that can be combined with data in a snippet
    to produce a rendered HTML page.
    """
    name = models.CharField(max_length=100,
                            help_text='This is just a friendly name to help you recognise the '
                                      'purpose of the template. It is not visible to users.')
    template_data = models.TextField(help_text='This is the actual content of the template. The '
                                               'title and content snippets will be filled in here '
                                               'to render the final page that will be pushed to '
                                               'devices.')
    duration = models.PositiveIntegerField(
            default=10000,  # 10 seconds
            help_text='How long should a slide using this template be visible on screen. <br/>'
                      'If a template has an animation this time should ensure that the animation '
                      'has enough time to complete. '
    )

    def render(self, context):
        """
        Creates a Django template object using the template data and renders it using the supplied
        context.
        """
        return template.Template(self.template_data).render(context)

    def __str__(self):
        return self.name


class Feed(models.Model):
    """
    This model represents a Feed.
    It serves as a base class for the more specialsed Image, Video and Web Feed classes.
    """
    name = models.CharField(max_length=100,
                            help_text='This is a friendly name to identify this feed, it is not '
                                      'visible to end-users. ')
    slug = models.SlugField(help_text='This field should be filled in automatically based on the '
                                      'name. It is a simplified representation of the name such '
                                      'that it can be part of a URL.')
    published = models.BooleanField(default=False,
                                    help_text='A feed that is published will appear in users\' '
                                              'asset lists. For a feed to be published it needs '
                                              'to have a valid snippet.')
    type = models.CharField(max_length=25, editable=False)
    category = models.ForeignKey(Category,
                                 help_text='The feed category decides what snippets appear in '
                                           'this feed.')
    publish_to = models.ManyToManyField(Client)

    asset_type = None

    snippet_type = None

    @property
    def checksum(self):
        """Returns checksum for today's asset for this feed"""
        if type(self) == Feed:
            return self.get_subtype().checksum
        else:
            return self.get_snippet_for_today().checksum

    def clean(self):
        """
        Disallows saving a feed that has no snippets assigned since that would cause errors in
        multiple other places
        """
        # Don't check for snippets if clean is called on base Feed object since it might not have
        # set up a type yet.
        if self.published and type(self) is not Feed and not self.snippets.exists():
            raise ValidationError({'published': 'You cannot publish a feed that has no snippets.'})

    @classmethod
    def add_feeds_to_playlist(cls, playlist: Playlist):
        """ This class method will add all published feeds to the supplied playlist. """
        for feed in cls.objects.filter(published=True, publish_to__in=[playlist.owner]).distinct():
            feed.add_feed_item_to_playlist(playlist)

    def add_feed_item_to_playlist(self, playlist: Playlist, feed_asset: FeedAsset = None):
        """
        Adds a feed item to a playlist by fetching an existing feed item for the feed or creating a
        new one if none is present.
        """
        if feed_asset is None:
            feed_asset = FeedAsset.objects.get(feed=self)
        playlist.playlistitem_set.create(item=feed_asset)

    def _create_playlist_items(self, feed_asset):
        """
        Creates a playlist item for this feed in every playlist subscribed to feeds.
        :param feed_asset: The feed asset associated with this Feed
        :type feed_asset: FeedAsset
        :rtype: None
        """
        if self.published:
            for playlist in Playlist.objects.filter(auto_add_feeds=True,
                                                    owner__in=self.publish_to.all()):
                if not playlist.playlistitem_set.filter(item=feed_asset).exists():
                    self.add_feed_item_to_playlist(playlist)

    def _manage_feed_asset(self):
        """
        Automatically cretes a FeedAsset for this feed. If a FeedAsset is alredy present, it
        will update the existing feed asset. If the feed is unpublished, it will delete the
        associated FeedAsset object.

        :return: Newly created or updated FeedAsset or None if assets were deleted
        :rtype: Union[FeedAsset, None]
        """
        if self.published:
            feed_asset, created = FeedAsset.objects.update_or_create(
                    feed=self,
                    defaults={
                        'name': '{name} Feed'.format(name=self.name),
                    })
            return feed_asset
        else:
            FeedAsset.objects.filter(feed=self).delete()

    def get_absolute_url(self):
        """ Returns the URL for this feed based on the type. """
        if self.type == AssetTypes.WEB:
            return reverse('web-feed-view', args=[str(self.slug)], host='content')
        elif self.type == AssetTypes.IMAGE:
            return reverse('image-feed-view', args=[str(self.slug)], host='content')
        elif self.type == AssetTypes.VIDEO:
            return reverse('video-feed-view', args=[str(self.slug)], host='content')
        else:
            raise ValueError

    def get_asset_url(self):
        """ Returns the URL for this feed based on the type. """
        if self.type == AssetTypes.WEB:
            return reverse('web-feed-view', args=[str(self.slug)], host='content')
        elif self.type == AssetTypes.IMAGE or self.type == AssetTypes.VIDEO:
            snippet = self.get_subtype().get_snippet_for_today()
            return snippet.media.url
        else:
            raise ValueError

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        Adds logic to the standard save method.
        * Adds the feed type to the Feed.
        * Adds a slug based on the name.
        * Runs the manage feed asset private method to update, create or delete the associated
          feed asset based on whether the feed is updated, published, or unpublished.
        * Adds associated feed asset to all subscribed playlists.
        """
        if type(self) is not Feed:
            self.type = self.asset_type

        if not self.slug:
            self.slug = slugify(self.name)

        super().save(force_insert, force_update, using, update_fields)

        if type(self) is not Feed:
            # Now that the Feed has been saved, create / update / delete the associated FeedAsset
            feed_asset = self._manage_feed_asset()
            # If a new FeedAsset was created, also add it to all subscribed playlists.
            if feed_asset is not None:
                self._create_playlist_items(feed_asset)

    def get_subtype(self):
        """Get's the child model for this feed instance."""
        if self.type == AssetTypes.WEB:
            return self.webfeed
        elif self.type == AssetTypes.IMAGE:
            return self.imagefeed
        elif self.type == AssetTypes.VIDEO:
            return self.videofeed
        else:
            raise ValueError

    @property
    def snippets(self):
        """Returns the snippets for this feed."""
        if isinstance(self, Feed):
            snippet_type = self.get_subtype().snippet_type
        else:
            snippet_type = self.snippet_type
        return self.category.get_snippets(snippet_type)

    def get_snippet_for_today(self):
        """ Retuns the snippet for the day. """
        snippets = self.snippets
        snippet_count = snippets.count()

        if snippet_count == 0:  # If there are no snippets this feed is invalid.
            raise self.snippet_type.DoesNotExist

        # index = hash(date.today()) % snippet_count
        # date.today().timetuple().tm_yday returns the day of the year for today.
        index = date.today().timetuple().tm_yday % snippet_count
        return snippets[index]

    def __str__(self):
        return self.name

    def as_dict(self):
        """Returns a dictionary representation of this feed"""
        if self.type == AssetTypes.WEB:
            return self.webfeed.as_dict()
        return {
            'url': self.get_asset_url(),
            'checksum': self.checksum,
            'type': self.type.lower(),
        }


class WebFeed(Feed):
    """
    This model represents a WebFeed.
    """
    template = models.ForeignKey(Template,
                                 help_text='Web feeds fill in the data from web snippets into '
                                           'this template to produce the final page that will '
                                           'be seen by on devices.')

    asset_type = AssetTypes.WEB

    snippet_type = WebSnippet

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._rendered_content = None
        self._checksum = None

    def get_absolute_url(self):
        """ Returns the URL for this web feed. """
        return reverse('web-feed-view', args=[str(self.slug)], host='content')

    def get_asset_url(self):
        """ Returns a URL for this web feed. """
        return self.get_absolute_url()

    def rendered_content(self):
        """ Renders this current snippet to HTML using the associated template. """
        if self._rendered_content is None:
            snippet = self.get_snippet_for_today()
            self._rendered_content = self.template.render(Context({
                'title': snippet.title,
                'content': snippet.content
            }))
        return self._rendered_content

    @property
    def checksum(self):
        """Returns md5_checksum for today's asset for this feed"""
        if self._checksum is None:
            self._checksum = md5_checksum(self.rendered_content())
        return self._checksum

    def as_dict(self):
        """Returns a dictionary representation of this feed"""
        return {
            'url': self.get_asset_url(),
            'checksum': self.checksum,
            'type': self.type.lower(),
            'duration': self.template.duration,
        }


class ImageFeed(Feed):
    """
    This model represents an Image Feed.
    """
    asset_type = AssetTypes.IMAGE

    snippet_type = ImageSnippet

    def get_absolute_url(self):
        """ Returns a URL for this feed. """
        return reverse('image-feed-view', args=[str(self.slug)], host='content')

    def get_asset_url(self):
        """ Returns a URL for this feed. """
        return self.get_absolute_url()


class VideoFeed(Feed):
    """ This model represents a Video Feed. """
    asset_type = AssetTypes.VIDEO

    snippet_type = VideoSnippet

    def get_absolute_url(self):
        """ Returns a URL for this feed. """
        return reverse('video-feed-view', args=[str(self.slug)], host='content')

    def get_asset_url(self):
        """ Returns a URL for this feed. """
        return self.get_absolute_url()
