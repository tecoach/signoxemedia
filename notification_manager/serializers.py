# -*- coding: utf-8 -*-
from rest_framework import serializers

from notification_manager.models import Post, UserPostStatus


class PostSerializer(serializers.ModelSerializer):
    topic = serializers.CharField(source='topic.name')
    icon = serializers.FileField(source='topic.image')
    is_read = serializers.SerializerMethodField()

    def get_is_read(self, obj):
        user = self.context['request'].user
        return UserPostStatus.objects.get(user=user,
                                          post=obj).read_on is not None

    class Meta:
        model = Post
        fields = ('id', 'title', 'topic', 'icon', 'content', 'posted_on', 'is_read')
