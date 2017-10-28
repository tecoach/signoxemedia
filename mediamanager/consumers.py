# -*- coding: utf-8 -*-
import json

from mediamanager.models import Asset, ImageAsset, VideoAsset, CalendarAsset
from utils.files import get_image_metadata, get_video_metadata


def _queryset_from_message(message, model):
    ids_to_update = message.content.get('ids', None)
    force_update = message.content.get('force_update', False)
    queryset = model.objects.all()

    if ids_to_update is not None:
        queryset = queryset.filter(pk__in=ids_to_update)

    return queryset, force_update


def update_metadata(message, asset_type, metadata_extractor):
    queryset, force_update = _queryset_from_message(message, asset_type)

    for idx, asset in enumerate(queryset):
        file = asset.media_file
        if force_update or asset.raw_metadata is None or asset.raw_metadata == '':
            metadata = metadata_extractor(file)
            asset.raw_metadata = json.dumps(metadata)
            asset.build_clean_metadata()
            asset.save()


def update_video_metadata(message):
    update_metadata(message, VideoAsset, get_video_metadata)


def update_image_metadata(message):
    update_metadata(message, ImageAsset, get_image_metadata)


def create_thumbnail(message):
    queryset, force_update = _queryset_from_message(message, Asset)

    for asset in queryset:
        asset.get_subtype().add_thumbnail(force=force_update)


def update_calendar_assets(message):
    queryset, force_update = _queryset_from_message(message, CalendarAsset)
    for cal in queryset:
        cal.update_calendar_data()
