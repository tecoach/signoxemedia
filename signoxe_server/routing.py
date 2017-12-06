# -*- coding: utf-8 -*-

from channels.routing import route

from client_manager.consumers import notify_connect, notify_disconnect
from mediamanager.consumers import (create_thumbnail, update_calendar_assets,
                                    update_image_metadata,
                                    update_video_metadata)

channel_routing = [
    route('update-video-metadata', update_video_metadata),
    route('update-image-metadata', update_image_metadata),
    route('update-calendar-assets', update_calendar_assets),
    route('create-thumbnail', create_thumbnail),
    route('websocket.connect', notify_connect, path=r'^/notify_updates/$'),
    route('websocket.disconnect', notify_disconnect, path=r'^/notify_updates/$'),
]
