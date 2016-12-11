# -*- coding: utf-8 -*-
# Create your views here.
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from notification_manager.models import Post, UserPostStatus
from notification_manager.serializers import PostSerializer


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            raise PermissionDenied
        one_month_ago = timezone.now() - timezone.timedelta(days=31)
        # Return posts that are either from the past one month, or are unread by the
        # current user.
        return self.queryset.filter(
                Q(posted_on__gte=one_month_ago) |
                Q(userpoststatus__user=user, userpoststatus__read_on=None)).distinct()

    # noinspection PyUnusedLocal
    @detail_route(methods=['POST'])
    def mark_read(self, request, pk=None):
        user = request.user
        post = self.get_object()
        post.userpoststatus_set.filter(user=user).update(read_on=timezone.now())
        serializer = self.serializer_class(post, context=self.get_serializer_context())
        return Response(serializer.data)

    @list_route(methods=['POST'])
    def mark_all_read(self, request):
        user = request.user
        unread_post_statuses = UserPostStatus.objects.filter(user=user, read_on=None)
        unread_post_statuses.update(read_on=timezone.now())
        serializer = self.serializer_class(self.get_queryset(),
                                           many=True,
                                           context=self.get_serializer_context())
        return Response(serializer.data)
