# -*- coding: utf-8 -*-
""" Tests for feed manager. """

import pytest
from PIL import Image
from django.core.files.base import ContentFile
from io import BytesIO

from client_manager.models import Client
from feedmanager.models import Category, ImageFeed
from mediamanager.models import FeedAsset, Playlist


@pytest.fixture
def test_image():
    image_file = BytesIO()
    image = Image.new('RGBA', size=(50, 50), color=(256, 0, 0))
    image.save(image_file, 'png')
    image_file.seek(0)
    return ContentFile(image_file.read(), 'test.png')


@pytest.fixture
@pytest.mark.django_db
def category():
    return Category.objects.create(name='test-category')


@pytest.fixture
@pytest.mark.django_db
def client_1(test_image):
    return Client.objects.create(name='test client 1', logo=test_image)


@pytest.fixture
@pytest.mark.django_db
def client_2(test_image):
    return Client.objects.create(name='test client 2', logo=test_image)


@pytest.fixture
@pytest.mark.django_db
def playlist_1(client_1):
    return Playlist.objects.create(name='test playlist 1', owner=client_1)


@pytest.fixture
@pytest.mark.django_db
def playlist_2(client_2):
    return Playlist.objects.create(name='test playlist 1', owner=client_2)


@pytest.fixture
@pytest.mark.django_db
def feed(category):
    imgfeed = ImageFeed(name='test feed 1', category=category, published=True)
    imgfeed.save()
    return imgfeed


@pytest.fixture
@pytest.mark.django_db
def feed_with_client_1(category, client_1):
    imgfeed = ImageFeed.objects.create(name='test feed 2',
                                       category=category,
                                       published=True, )
    imgfeed.save()
    imgfeed.publish_to.add(client_1)
    imgfeed.save()
    return imgfeed


@pytest.fixture
@pytest.mark.django_db
def feed_with_client_1(category, client_1):
    imgfeed = ImageFeed.objects.create(name='test feed with client 1',
                                       category=category,
                                       published=True, )
    imgfeed.save()
    imgfeed.publish_to.add(client_1)
    imgfeed.save()
    return imgfeed


@pytest.mark.django_db
def test_feed_creates_feed_asset(feed):
    """ Ensure that creating a new Feed object creates the corresponding FeedAsset. """
    assert FeedAsset.objects.filter(feed=feed).exists()


@pytest.mark.django_db
def test_feed_creates_playlist_items_for_playlists_of_published_clients(playlist_1,
                                                                        playlist_2,
                                                                        feed_with_client_1):
    assert playlist_1.playlistitem_set.filter(
            item__feedasset__feed=feed_with_client_1).exists()


@pytest.mark.django_db
def test_feed_doesnt_create_playlist_items_for_playlists_of_non_published_clients(
        playlist_1,
        playlist_2,
        feed_with_client_1):
    assert not playlist_2.playlistitem_set.filter(
            item__feedasset__feed=feed_with_client_1).exists()


@pytest.mark.django_db
def test_new_playlist_gets_feeds_published_to_owner(client_1, feed_with_client_1):
    playlist = Playlist.objects.create(name='test playlist w/ client 1', owner=client_1)
    assert playlist.playlistitem_set.filter(item__feedasset__feed=feed_with_client_1).exists()


@pytest.mark.django_db
def test_new_client_for_feed_gets_feeds_published(client_1, playlist_1: Playlist, feed):
    feed.publish_to.add(client_1)
    feed.save()
    assert playlist_1.playlistitem_set.filter(item__feedasset__feed=feed).exists()
