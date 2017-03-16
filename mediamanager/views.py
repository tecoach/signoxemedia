# -*- coding: utf-8 -*-
"""
View for media manager app.
"""
from channels import Channel
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.views.decorators.clickjacking import xframe_options_exempt
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from mediamanager.models import (Asset, CalendarAsset, ContentFeed, FeedAsset, ImageAsset,
                                 Playlist, PlaylistItem, Ticker, TickerSeries, VideoAsset,
                                 WebAsset, WebAssetTemplate, )
from mediamanager.serializers import (AssetSerializer, CalendarSerializer, ContentFeedSerializer,
                                      FeedSerializer, ImageSerializer, PlaylistItemSerializer,
                                      PlaylistSerializer, TickerSerializer,
                                      TickerSeriesSerializer, VideoSerializer,
                                      WebAssetTemplateSerializer, WebSerializer, )
from utils.errors import NoContentAssetError
from utils.files import verify_mime
from utils.mixins import FilterByOwnerMixin, get_owner_from_request


# noinspection PyUnusedLocal
class TickerSeriesViewSet(FilterByOwnerMixin, viewsets.ModelViewSet):
    """ API ViewSet class for ticker series. """
    queryset = TickerSeries.objects.all()
    serializer_class = TickerSeriesSerializer

    @detail_route(methods=['POST'])
    def clone(self, request, pk=None):
        """ Creates a copy of the ticker series along with all tickers. """
        ticker_series = self.get_object()  # type: TickerSeries
        tickers = ticker_series.ticker_set.all()
        ticker_series.pk = None
        ticker_series.save()
        ticker_series.name = '{} ({})'.format(ticker_series.name, ticker_series.id)
        ticker_series.save()
        for ticker in tickers:
            ticker.pk = None
            ticker.ticker_series = ticker_series
            ticker.save()
        serializer = self.serializer_class(ticker_series)
        return Response(serializer.data)


class TickerViewSet(viewsets.ModelViewSet):
    """ API ViewSet class for tickers. """
    queryset = Ticker.objects.all()
    serializer_class = TickerSerializer


class PlaylistViewSet(FilterByOwnerMixin, viewsets.ModelViewSet):
    """ API ViewSet class for playlists. """
    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer

    @detail_route(methods=['POST'])
    def clone(self, request, pk=None):
        """ Creates a copy of the ticker series along with all tickers. """
        playlist = self.get_object()  # type: Playlist
        playlist_items = playlist.playlistitem_set.all()
        # Saving original value and setting auto add feeds to false to avoid
        # feeds being duplicated.
        auto_add_feeds = playlist.auto_add_feeds
        playlist.auto_add_feeds = False
        playlist.pk = None
        playlist.save()
        playlist.auto_add_feeds = auto_add_feeds
        playlist.name = '{} ({})'.format(playlist.name, playlist.id)
        for item in playlist_items:
            item.pk = None
            item.playlist = playlist
            item.save()
        playlist.save()
        serializer = self.serializer_class(playlist)
        return Response(serializer.data)


class PlaylistItemViewSet(viewsets.ModelViewSet):
    """ API ViewSet class for playlist items. """
    queryset = PlaylistItem.objects.all()
    serializer_class = PlaylistItemSerializer


class ValidateMimesOnCreateMixin:
    """ A mixin to validate the mime-type of uploaded files. """

    def create(self, request, *args, **kwargs):
        """ While uploading a file, check if the mime type is valid, and if not, raise error. """
        if not verify_mime(request.FILES[self.file_field],
                           supported_types=self.supported_mimes):
            raise ValidationError('Invalid file type')
        return super().create(request, *args, **kwargs)


class AssetViewSet(FilterByOwnerMixin, viewsets.ModelViewSet):
    """ API ViewSet class for assets. """
    queryset = Asset.objects.order_by('-created')
    serializer_class = AssetSerializer

    @detail_route(methods=['GET', 'POST', 'PUT', 'DELETE'])
    def tags(self, request, pk=None):
        asset = self.get_object()
        if request.method == 'DELETE':
            tags = request.data
            if not tags:
                asset.tags.clear()
            elif isinstance(tags, list):
                asset.tags.remove(*tags)
            else:
                raise ValidationError
            return Response(status=status.HTTP_204_NO_CONTENT)
        if request.method == 'PUT':
            tags = request.data
            if isinstance(tags, list):
                asset.tags.set(*tags)
            else:
                raise ValidationError
        if request.method == 'POST':
            tags = request.data
            if isinstance(tags, list):
                asset.tags.add(*tags)
            else:
                raise ValidationError
        return Response(asset.get_tags_list())


class ImageViewSet(FilterByOwnerMixin, ValidateMimesOnCreateMixin, viewsets.ModelViewSet):
    """ API ViewSet class for image assets. """
    queryset = ImageAsset.objects.all()
    serializer_class = ImageSerializer

    supported_mimes = ['image/png', 'image/jpeg', 'image/pjpeg']
    file_field = 'media_file'


class VideoViewSet(FilterByOwnerMixin, ValidateMimesOnCreateMixin, viewsets.ModelViewSet):
    """ API ViewSet class for video assets. """
    queryset = VideoAsset.objects.all()
    serializer_class = VideoSerializer

    supported_mimes = ['video/mp4', 'video/webm']
    file_field = 'media_file'


class FeedViewSet(viewsets.ModelViewSet):
    """ API ViewSet class for feed assets. """
    queryset = FeedAsset.objects.all()
    serializer_class = FeedSerializer

    def get_queryset(self):
        """
        Filters the Feed assets to only list feed assets that have a feed that's published to
        the currently logged in user's client.
        """
        owner = get_owner_from_request(self.request)
        return self.queryset.filter(feed__publish_to__in=[owner])


class WebViewSet(FilterByOwnerMixin, viewsets.ModelViewSet):
    """ API ViewSet class for web assets. """
    queryset = WebAsset.objects.all()
    serializer_class = WebSerializer


class CalendarViewSet(FilterByOwnerMixin, viewsets.ModelViewSet):
    """ API ViewSet class for calendar assets. """
    queryset = CalendarAsset.objects.all()
    serializer_class = CalendarSerializer

    @detail_route(methods=['POST'])
    def refresh(self, request, pk=None):
        cal_asset_id = self.get_object().id  # type: CalendarAsset
        Channel('update-calendar-assets').send({'ids': [cal_asset_id]})
        return Response({})


class ContentFeedViewSet(mixins.UpdateModelMixin,
                         mixins.RetrieveModelMixin,
                         viewsets.GenericViewSet):
    """ API ViewSet class for content feeds. """
    queryset = ContentFeed.objects.all()
    serializer_class = ContentFeedSerializer


class WebAssetTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """ API ViewSet class for web asset templates. """
    queryset = WebAssetTemplate.objects.all()
    serializer_class = WebAssetTemplateSerializer


def filter_by_owner(queryset, owner):
    """ Helper function to filter a queryset by owner. """
    if owner is not None:
        return queryset.filter(owner=owner)
    else:
        return queryset


def asset_view(request, asset_id):
    """ This view redirects to the assets's media location or web page. """
    owner = get_owner_from_request(request)
    try:
        asset = filter_by_owner(Asset.objects, owner).get(pk=asset_id)
    except Asset.DoesNotExist:
        return HttpResponseNotFound()
    return HttpResponseRedirect(asset.get_asset_url())


@xframe_options_exempt
def web_asset_view(request, asset_id):
    """ This view renders a web asset's content page. """
    # TODO: Add authentication for client devices
    # owner = get_owner_from_request(request)
    try:
        # webasset = filter_by_owner(WebAsset.objects, owner).get(pk=asset_id)
        webasset = WebAsset.objects.get(pk=asset_id)
    except WebAsset.DoesNotExist:
        return HttpResponseNotFound()
    return HttpResponse(webasset.content)


@xframe_options_exempt
def cal_asset_view(request, asset_id):
    """ This view renders a calendar asset's content page. """
    # TODO: Add authentication for client devices
    # owner = get_owner_from_request(request)
    try:
        calasset = CalendarAsset.objects.get(pk=asset_id)
    except CalendarAsset.DoesNotExist:
        return HttpResponseNotFound()
    try:
        content = calasset.rendered_content
        return HttpResponse(content)
    except NoContentAssetError:
        return HttpResponse(status=204)
