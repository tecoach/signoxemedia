# -*- coding: utf-8 -*-
from django.db import transaction
from rest_framework import mixins, viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response

from schedule_manager.models import ScheduledContent, SpecialContent
from schedule_manager.serializers import ScheduledContentSerializer, SpecialContentSerializer


class ScheduledContentViewSet(mixins.CreateModelMixin,
                              mixins.UpdateModelMixin,
                              mixins.DestroyModelMixin,
                              viewsets.GenericViewSet):
    """ API ViewSet class for Scheduled Content. """
    queryset = ScheduledContent.objects.all()
    serializer_class = ScheduledContentSerializer

    @list_route(methods=['post'])
    def bulk_update(self, request):
        """ Provides an API to modify multiple schedules at once. """
        schedules = []
        with transaction.atomic():
            for entry in request.data:
                schedule = ScheduledContent.objects.get(pk=entry['id'])
                schedules.append(schedule)
                schedule.start_time = entry['start_time']
                schedule.end_time = entry['end_time']
                schedule.save(validate=False)
            for schedule in schedules:
                schedule.clean()
        serializer = self.serializer_class(schedules, many=True)
        return Response(serializer.data)


class SpecialContentViewSet(mixins.CreateModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            viewsets.GenericViewSet):
    """ API ViewSet class for Scheduled Content. """
    queryset = SpecialContent.objects.all()
    serializer_class = SpecialContentSerializer
