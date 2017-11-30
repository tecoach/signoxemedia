# -*- coding: utf-8 -*-
from rest_framework import serializers

from mediamanager.serializers import ContentFeedSerializer
from schedule_manager.models import ScheduledContent, SpecialContent


class ScheduledContentSerializer(serializers.ModelSerializer):
    """ Serializer for Scheduled Content """

    content = ContentFeedSerializer(required=False, read_only=True)

    class Meta:
        model = ScheduledContent
        fields = ('id', 'day', 'default', 'start_time', 'end_time', 'content', 'device_group',
                  'bring_to_front',)
        read_only_fields = ('default', 'content',)
        extra_kwargs = {
            'day': {'required': False},
            'device_group': {'required': False},
        }


class SpecialContentSerializer(serializers.ModelSerializer):
    """ Serializer for Special Content """

    content = ContentFeedSerializer(required=False)

    class Meta:
        model = SpecialContent
        fields = ('id', 'date', 'content', 'device_group',)
        read_only_fields = ('content',)
        extra_kwargs = {
            'device_group': {'required': False},
        }
