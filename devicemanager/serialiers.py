# -*- coding: utf-8 -*-
""" Serializers for device manager. """
from rest_framework import serializers

from devicemanager.models import Device, DeviceGroup, DeviceScreenShot, PriorityMessage
from mediamanager.models import ContentFeed
from mediamanager.serializers import ContentFeedSerializer
from schedule_manager.serializers import ScheduledContentSerializer, SpecialContentSerializer
from utils.mixins import AutoAddOwnerOnCreateMixin


class DeviceSerializer(AutoAddOwnerOnCreateMixin, serializers.ModelSerializer):
    """ Serializer for devices. """
    owner = serializers.Field(required=False, write_only=True)

    class Meta:
        """ Meta class for :class:DeviceSerializer """
        model = Device
        fields = ('id', 'device_id', 'group', 'name', 'build_version',
                  'last_ping', 'debug_mode', 'enabled', 'owner',)
        read_only_fields = ('device_id', 'build_version', 'last_ping', 'owner',)


class DeviceScreenShotSerializer(serializers.ModelSerializer):
    """ Serializer for device screen-shots. """

    class Meta:
        """ Meta class for :class:DeviceScreenShotSerializer """
        model = DeviceScreenShot
        fields = ('id', 'device', 'image', 'thumbnail', 'timestamp')


class PriorityMessageSerializer(serializers.ModelSerializer):
    """Serializer for priority messages"""

    class Meta:
        model = PriorityMessage
        fields = ('id', 'device_group', 'duration', 'activated_on', 'message')
        read_only_fields = ('device_group', 'activated_on')


class DeviceGroupSerializer(AutoAddOwnerOnCreateMixin, serializers.ModelSerializer):
    """ Serializer for device groups. """
    devices = DeviceSerializer(many=True, source='device_set', required=False)
    feed = ContentFeedSerializer(required=False)
    owner = serializers.Field(required=False, write_only=True)
    schedule = ScheduledContentSerializer(many=True, source='scheduledcontent_set', required=False)
    specials = SpecialContentSerializer(many=True, source='specialcontent_set', required=False)
    priority_message = PriorityMessageSerializer(source='prioritymessage', required=False)

    def create(self, validated_data):
        """ Handles creation of new device group. """
        # When a new device group is created, automatically create a content feed for it.
        if 'feed' not in validated_data:
            validated_data['feed'] = ContentFeed.objects.create(
                    title='AutoFeed: ({})'.format(validated_data['name']),
                    auto_created=True
            )
        return super().create(validated_data)

    class Meta:
        """ Meta class for :class:DeviceGroupSerializer """
        model = DeviceGroup
        fields = ('id', 'devices', 'name', 'feed', 'owner', 'display_date_time',
                  'schedule', 'specials', 'priority_message',)
        read_only_fields = ('owner', 'schedule', 'specials', 'priority_message')
