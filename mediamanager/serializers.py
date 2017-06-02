# -*- coding: utf-8 -*-
""" Serializers for the media manager app. """

from django.db.models import F
from rest_framework import serializers

from mediamanager.models import (Asset, CalendarAsset, ContentFeed, ImageAsset, Playlist,
                                 PlaylistItem, Ticker, TickerSeries, VideoAsset, WebAsset,
                                 WebAssetTemplate, )
from utils.mixins import AutoAddOwnerOnCreateMixin


class TickerSerializer(serializers.ModelSerializer):
    """ Serializer for tickers. """
    position = serializers.IntegerField(required=False)

    class Meta:
        """ Meta class for :class:TickerSerializer """
        model = Ticker
        fields = (
            'id', 'position', 'text', 'colour', 'ticker_series',
            'font_size', 'font_family', 'outline', 'background',
            'speed',
        )


class TickerSeriesSerializer(AutoAddOwnerOnCreateMixin, serializers.ModelSerializer):
    """ Serializer for ticker series. """
    tickers = TickerSerializer(many=True, source='ticker_set', required=False)
    owner = serializers.Field(required=False, write_only=True)

    class Meta:
        """ Meta class for :class:TickerSeriesSerializer """
        model = TickerSeries
        fields = ('id', 'name', 'tickers', 'owner',)
        depth = 1


class ImageSerializer(AutoAddOwnerOnCreateMixin, serializers.ModelSerializer):
    """ Serializer for image assets. """
    owner = serializers.Field(required=False, write_only=True)
    metadata = serializers.ReadOnlyField(source='get_metadata_as_dict')
    full_metadata = serializers.ReadOnlyField(source='get_raw_metadata_as_dict')

    class Meta:
        """ Meta class for :class:ImageSerializer """
        model = ImageAsset
        fields = ('id', 'name', 'type', 'asset_url', 'media_file', 'thumbnail',
                  'owner', 'metadata', 'full_metadata')
        read_only_fields = ('asset_url', 'thumbnail', 'type', 'metadata', 'full_metadata')


class VideoSerializer(AutoAddOwnerOnCreateMixin, serializers.ModelSerializer):
    """ Serializer for video assets. """
    owner = serializers.Field(required=False, write_only=True)
    metadata = serializers.ReadOnlyField(source='get_metadata_as_dict')
    full_metadata = serializers.ReadOnlyField(source='get_raw_metadata_as_dict')

    class Meta:
        """ Meta class for :class:VideoSerializer """
        model = VideoAsset
        fields = ('id', 'name', 'type', 'asset_url', 'media_file', 'thumbnail',
                  'owner', 'metadata', 'full_metadata')
        read_only_fields = ('asset_url', 'thumbnail', 'type', 'metadata', 'full_metadata')


class WebSerializer(AutoAddOwnerOnCreateMixin, serializers.ModelSerializer):
    """ Serializer for web assets. """
    owner = serializers.Field(required=False, write_only=True)

    class Meta:
        """ Meta class for :class:WebSerializer """
        model = WebAsset
        fields = ('id', 'name', 'asset_url', 'content', 'url', 'owner',)
        read_only_fields = ('asset_url',)


class CalendarSerializer(AutoAddOwnerOnCreateMixin, serializers.ModelSerializer):
    """ Serializer for calendar assets. """
    owner = serializers.Field(required=False, write_only=True)

    class Meta:
        """ Meta class for :class:CalendarSerializer """
        model = CalendarAsset
        fields = ('id', 'name', 'asset_url', 'url', 'template', 'owner',)
        read_only_fields = ('asset_url',)


class AssetSerializer(serializers.ModelSerializer):
    """ Serializer for assets. """
    metadata = serializers.ReadOnlyField(source='get_metadata_as_dict')
    full_metadata = serializers.ReadOnlyField(source='get_raw_metadata_as_dict')
    tags = serializers.ReadOnlyField(source='get_tags_list')

    class Meta:
        """ Meta class for :class:AssetSerializer """
        model = Asset
        fields = (
            'id', 'name', 'type', 'thumbnail', 'asset_url', 'metadata', 'full_metadata', 'tags')
        read_only_fields = (
            'asset_url', 'type', 'thumbnail', 'metadata', 'full_metadata', 'tags')


class FeedSerializer(serializers.ModelSerializer):
    """ Serializer for feed assets. """

    class Meta:
        """ Meta class for :class:FeedSerializer """
        model = Asset
        fields = ('id', 'name', 'type', 'asset_url',)
        read_only_fields = ('asset_url', 'type')


class PlaylistItemSerializer(serializers.ModelSerializer):
    """ Serializer for playlist items. """
    position = serializers.IntegerField(required=False)

    def create(self, validated_data):
        """
        Handles the special case where a new playlist item is to be added to beginning, which
        requires shifting all other items.
        """
        position = validated_data.get('position', None)
        playlist = validated_data.get('playlist')
        if position is not None and position == -1:
            PlaylistItem.objects.filter(playlist=playlist).update(position=F('position') + 1)
            validated_data['position'] = 0
        return super().create(validated_data)

    class Meta:
        """ Meta class for :class:PlaylistItemSerializer """
        model = PlaylistItem
        fields = ('id', 'position', 'item', 'duration', 'playlist', 'expire_on', 'enabled')


class PlaylistItemSerializerForPlaylist(serializers.ModelSerializer):
    """ Serializer for playlist items inside a playlist. """
    id = serializers.IntegerField()
    playlist = serializers.IntegerField(source='playlist_id', read_only=True)
    item = AssetSerializer()

    class Meta:
        """ Meta class for :class:PlaylistItemSerializerForPlaylist """
        model = PlaylistItem
        fields = ('id', 'position', 'item', 'duration', 'playlist', 'expire_on', 'enabled')


class PlaylistSerializer(AutoAddOwnerOnCreateMixin, serializers.ModelSerializer):
    """ Serializer for playlists. """
    #: Need a custom serializer for items here, to avoid issues while performing updates.
    items = PlaylistItemSerializerForPlaylist(source='playlistitem_set',
                                              many=True,
                                              read_only=False,
                                              required=False)
    owner = serializers.Field(required=False, write_only=True)

    def update(self, instance, validated_data: dict):
        """ Handles updates for playlist API. """
        playlist_items = validated_data.pop('playlistitem_set', [])
        for item in playlist_items:
            # Update the position of items in the playlist. Since this the playlist endpoint, this
            # is the only kind of update we will allow, not updates to other fields.
            PlaylistItem.objects.filter(id=item.get('id')).update(position=item.get('position'))
        if 'name' in validated_data:
            instance.name = validated_data.get('name')
            instance.save()
        if 'auto_add_feeds' in validated_data:
            instance.auto_add_feeds = validated_data.get('auto_add_feeds')
            instance.save()
        return instance

    class Meta:
        """ Meta class for :class:PlaylistSerializer """
        model = Playlist
        fields = ('id', 'name', 'items', 'owner', 'auto_add_feeds',)


class ContentFeedSerializer(serializers.ModelSerializer):
    """ Serializer for content feed """

    class Meta:
        """ Meta class for :class:ConteFeedSerializer """
        model = ContentFeed
        fields = ('id', 'title', 'media_playlist', 'ticker_series',
                  'image_duration', 'web_duration', 'overlay_ticker',)


class WebAssetTemplateSerializer(serializers.ModelSerializer):
    """ Serializer for web asset templates. """

    class Meta:
        """ Meta class for :class:WebAssetTemplateSerializer """
        model = WebAssetTemplate
        fields = ('id', 'name', 'template', 'variables', 'calendar_support', 'data_support',
                  'help_html')
