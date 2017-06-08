# -*- coding: utf-8 -*-
"""
Views for the device manager app
"""
import json
import logging

from django.core.cache import cache
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from raven.contrib.django.raven_compat.models import client
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from client_manager.models import ClientSettings
from devicemanager.models import (AppBuild, Device, DeviceGroup, DeviceScreenShot, MirrorServer,
                                  PriorityMessage, )
from devicemanager.serialiers import (DeviceGroupSerializer, DeviceScreenShotSerializer,
                                      DeviceSerializer, PriorityMessageSerializer, )
from feedmanager.models import ImageSnippet, VideoSnippet, WebSnippet
from mediamanager.models import ContentFeed
from schedule_manager.models import ScheduledContent, WeekDays
from utils.mixins import FilterByOwnerMixin, get_owner_from_request

logger = logging.getLogger(__name__)


def get_owner_settings(owner):
    logo_url, logo_checksum = owner.get_logo_data()
    update_interval = owner.update_interval.total_seconds() * 1000
    settings, _ = ClientSettings.objects.get_or_create(client=owner)
    return {
        'displayLogo': owner.display_device_logo,
        'idleDetectionEnabled': settings.idle_detection_enabled,
        'idleThreshold': settings.idle_detection_threshold,
        'logoURL': logo_url,
        'logoChecksum': logo_checksum,
        'heartbeatInterval': update_interval,
    }


def get_device_group_settings(device_group):
    return {
        'displayDateTime': device_group.display_date_time,
        'orientation': device_group.orientation,
    }


@method_decorator(csrf_exempt, name='dispatch')
class DeviceFeedView(View):
    """ View class that handles interactions with media player clients. """

    def get(self, request, device_id):
        """
        Returns the configured feed for a device.
        Creates a new device with provided id if none exist.
        Returns an error message in case of any misconfiguration in the device.
        """
        # Device feeds are stored by the device id with dashes removed.
        feed = cache.get(device_id.replace('-', ''))
        if feed:
            # Commands should only go to the device once.
            feed['command'] = None
            return JsonResponse(feed)

        try:
            device = Device.objects.select_related('group', 'group__feed').get(device_id=device_id)
        except Device.DoesNotExist:
            Device.objects.create(device_id=device_id, last_ping=timezone.now(), enabled=False)
            message = 'New device connected from IP {}'.format(request.META['REMOTE_ADDR'])
            client.captureMessage(message, level='info')
            logger.info(message)
            return JsonResponse({'message': 'New device.'})
        except ValueError:
            client.captureMessage('Invalid device ID requested: {}'.format(device_id), )
            return JsonResponse({'error': 'Invalid device ID.'})

        self._update_device_ping_time_and_save(device)

        if not device.enabled:
            return JsonResponse({'message': 'Device not enabled.'})
        elif device.group is None:
            return JsonResponse({'message': 'Device not configured.'})
        elif device.owner is None:
            return JsonResponse({'message': 'Invalid device configuration.'})

        try:
            device_feed = device.group.get_group_feed()
        except ContentFeed.PlaylistNotSetError:
            return JsonResponse({'message': 'Device group has no playlist configured.'})
        except (VideoSnippet.DoesNotExist, ImageSnippet.DoesNotExist, WebSnippet.DoesNotExist):
            return JsonResponse({'message': 'Feed error: contact admin.'})
        except AttributeError:
            # This error means someone has messed up something in the backend, and it will need
            # manual intervention to fix.
            return JsonResponse({'message': 'ContentFeed error: contact admin.'})

        # Send the device the command, and immediately reset it so the device doesn't get the
        # command multiple times
        device_feed['command'] = device.command
        if device.command is not None:
            device.command = None
            device.save()

        device_feed.update(device.group.priority_feed())

        device_feed['settings']['displayErrorLog'] = device.debug_mode

        device_feed['settings'].update(get_device_group_settings(device.group))
        device_feed['settings'].update(get_owner_settings(device.owner))

        # If device group has a mirror associated with it, send it's address in the feed as the
        # backendUrl, so future updates will happen from that url.
        if device.group.mirror and device.group.mirror.address:
            feed_url = device.group.mirror.address
            device_feed['settings']['backendUrl'] = feed_url

        # App update manifest
        device_feed['updates'] = AppBuild.get_latest_app_manifest(device.owner.app_build_channel)

        # Save the feed to the cache using the device id (with dashes removed) as the key.
        cache.set(device_id.replace('-', ''), device_feed)

        return JsonResponse(device_feed)

    @staticmethod
    def _update_device_ping_time_and_save(device):
        device.last_ping = timezone.now()
        device.save()

    def post(self, request, device_id):
        """ Updates the device's status. Currently only the app build number. """
        try:
            device = Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            return JsonResponse({'error': 'New or invalid device.'})

        try:
            data = json.loads(request.body.decode('utf-8'))  # type: dict
            app_build = data['app_build']
            device.build_version = int(app_build)
            self._update_device_ping_time_and_save(device)  # also saves
        except (KeyError, ValueError):
            # Invalid JSON data, no app_build field present, or app_build field is not a valid int
            return JsonResponse({'error': 'Invalid payload.'})
        return JsonResponse({'message': 'Status updated.'})


device_feed_view = DeviceFeedView.as_view()


class DeviceViewSet(FilterByOwnerMixin,
                    mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    viewsets.GenericViewSet):
    """ API ViewSet class for devices. """
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

    # noinspection PyUnusedLocal
    @list_route(methods=['GET'])
    def ungrouped(self, request):
        """
        This exposes an API endpoint at /devices/ungrouped that returns all devices that have not
        been added to any group.
        """
        ungrouped_devices = Device.objects.filter(group=None).filter(
                owner=get_owner_from_request(request))
        serializer = self.serializer_class(ungrouped_devices, many=True)
        return Response(serializer.data)

    def _screenshot(self, burst=False):
        device = self.get_object()

        if burst is True:
            device.command = device.TAKE_SCREENSHOT_BURST
        else:
            device.command = device.TAKE_SCREENSHOT

        device.save()

    @detail_route(methods=['POST'])
    def screenshot(self, request, pk=None):
        """ API endpoint to request a device screenshot, or screenshot burst. """
        self._screenshot()
        return JsonResponse({'message': 'Request sent'})

    @detail_route(methods=['POST'])
    def screenshot_burst(self, request, pk=None):
        """ API endpoint to request a device screenshot, or screenshot burst. """
        self._screenshot(burst=True)
        return JsonResponse({'message': 'Request sent'})


class DeviceScreenShotViewSet(mixins.ListModelMixin,
                              mixins.RetrieveModelMixin,
                              mixins.DestroyModelMixin,
                              viewsets.GenericViewSet):
    """ API ViewSet class for devices. """
    queryset = DeviceScreenShot.objects.all()
    serializer_class = DeviceScreenShotSerializer

    def get_queryset(self):
        """ Returns the queryset filtered by owner based on the user from the request. """
        return self.queryset.filter(device__owner=get_owner_from_request(self.request))


class DeviceGroupViewSet(FilterByOwnerMixin,
                         mixins.CreateModelMixin,
                         mixins.ListModelMixin,
                         mixins.UpdateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.DestroyModelMixin,
                         viewsets.GenericViewSet):
    """ API ViewSet class for device groups. """
    queryset = DeviceGroup.objects.all()
    serializer_class = DeviceGroupSerializer

    @detail_route(methods=['post'])
    def enable_scheduling(self, request, pk=None):
        """ Enables scheduling for this device group. """
        device_group = self.get_object()
        for day in WeekDays.CODES:
            # Create a default scheduled content entry for each day of the week.
            ScheduledContent.objects.get_or_create(
                    day=day,
                    default=True,
                    device_group=device_group,
            )
        serializer = self.serializer_class(device_group)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def disable_scheduling(self, request, pk=None):
        """ Disable scheduling for this device group. """
        device_group = self.get_object()
        ScheduledContent.objects.filter(device_group=device_group).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post', 'patch', 'delete'])
    def priority_message(self, request, pk=None):
        device_group = self.get_object()
        # Create a new priority message if one doesn't exist.
        priority_message, _ = PriorityMessage.objects.get_or_create(device_group=device_group)

        # Don't delete the object, just deactivate it.
        if request.method == 'DELETE':
            priority_message.deactivate()
        else:
            # request.method is post or patch
            data = dict(request.data)
            serializer = PriorityMessageSerializer(data=data, partial=True,
                                                   instance=priority_message)

            serializer.is_valid(raise_exception=True)

            if request.method == 'POST':
                # In case of POST activate the message
                serializer.save(activated_on=timezone.now())
            elif request.method == 'PATCH':
                # In case of PATCH / updates just change the data
                serializer.save()

        response_serializer = self.serializer_class(device_group)
        return Response(response_serializer.data)


@method_decorator(csrf_exempt, name='dispatch')
class MirrorFeedView(View):
    """ View class that handles interactions with mirror servers. """

    @staticmethod
    def _update_mirror_ping_time_and_save(mirror):
        mirror.last_ping = timezone.now()
        mirror.save()

    def get(self, request, mirror_id):
        """
        Returns the configured feed for a device.
        Creates a new device with provided id if none exist.
        Returns an error message in case of any misconfiguration in the device.
        """
        try:
            mirror = MirrorServer.objects.get(mirror_id=mirror_id)
        except MirrorServer.DoesNotExist:
            MirrorServer.objects.create(mirror_id=mirror_id,
                                        last_ping=timezone.now(),
                                        name='New Mirror {}'.format(timezone.now()))
            message = 'New mirror connected from IP {}'.format(request.META['REMOTE_ADDR'])
            client.captureMessage(message, level='info')
            logger.info(message)
            return JsonResponse({'message': 'New mirror.'})

        self._update_mirror_ping_time_and_save(mirror)

        if mirror.address is None:
            return JsonResponse({'message': 'Device not enabled.'})

        settings = get_owner_settings(mirror.owner)
        settings['backendUrl'] = mirror.address

        updates = AppBuild.get_latest_app_manifest(mirror.owner.app_build_channel)

        group_feeds = {}
        device_feeds = {}
        for device_group in mirror.devicegroup_set.all():
            try:
                group_feeds[device_group.id] = device_group.get_group_feed()
            except ContentFeed.PlaylistNotSetError:
                group_feeds[device_group.id] = {
                    'message': 'Device group has no playlist configured.'
                }
            except AttributeError:
                group_feeds[device_group.id] = {'message': 'ContentFeed error: contact admin.'}

            group_feeds[device_group.id].update(device_group.priority_feed())

            for device in device_group.device_set.all():
                device_hex_id = device.device_id.hex
                device_feed = {'command': device.command, 'settings': {}}
                if device.command is not None:
                    device.command = None
                    device.save()

                device_feed['settings']['displayErrorLog'] = device.debug_mode
                device_feed['settings'].update(get_device_group_settings(device.group))
                device_feed['group_id'] = device.group_id
                device_feeds[device_hex_id] = device_feed

        return JsonResponse({
            'device_feeds': device_feeds,
            'group_feeds': group_feeds,
            'settings': settings,
            'updates': updates,
        })


mirror_feed_view = MirrorFeedView.as_view()


@method_decorator(csrf_exempt, name='dispatch')
class DeviceScreenShotView(View):
    """ View class that handles devices posting screenshots. """

    def post(self, request: HttpRequest, device_id):
        try:
            device = Device.objects.get(device_id=device_id)
        except (Device.DoesNotExist, ValueError):
            return JsonResponse({'error': 'Invalid device'})

        screenshot_file = request.FILES.get('screenshot', None)

        if screenshot_file is None:
            return JsonResponse({'error': 'No screenshot attached.'})

        device_screenshot = DeviceScreenShot.objects.create(device=device, image=screenshot_file)
        serializer = DeviceScreenShotSerializer(device_screenshot)
        return JsonResponse(serializer.data)


device_screenshot_view = DeviceScreenShotView.as_view()
