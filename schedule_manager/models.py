# -*- coding: utf-8 -*-
import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from mediamanager.models import ContentFeed


class WeekDays:
    """ Days of the week """
    MONDAY = 'mon'
    TUESDAY = 'tue'
    WEDNESDAY = 'wed'
    THURSDAY = 'thu'
    FRIDAY = 'fri'
    SATURDAY = 'sat'
    SUNDAY = 'sun'

    CHOICES = (
        (MONDAY, 'Monday'),
        (TUESDAY, 'Tuesday'),
        (WEDNESDAY, 'Wednesday'),
        (THURSDAY, 'Thursday'),
        (FRIDAY, 'Friday'),
        (SATURDAY, 'Saturday'),
        (SUNDAY, 'Sunday'),
    )

    CODES = [
        MONDAY,
        TUESDAY,
        WEDNESDAY,
        THURSDAY,
        FRIDAY,
        SATURDAY,
        SUNDAY,
    ]

    @staticmethod
    def today():
        """ Returns weekday code for today. """
        weekday = datetime.date.today().weekday()
        return WeekDays.CHOICES[weekday][0]


class ScheduledContent(models.Model):
    """ Model to associate a schedule with a content feed. """
    day = models.CharField(choices=WeekDays.CHOICES, max_length=4)
    default = models.BooleanField(default=False)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    content = models.ForeignKey(ContentFeed, on_delete=models.CASCADE)
    bring_to_front = models.BooleanField(default=False)
    device_group = models.ForeignKey('devicemanager.DeviceGroup', on_delete=models.CASCADE)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None,
             validate=True):
        """ Enforce validation on save. """
        if validate:
            self.clean()
        self._ensure_content_feed()
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        if self.default:
            return '{group}: {day} (default)'.format(
                    group=self.device_group,
                    day=self.get_day_display(),
            )
        else:
            return '{group}: {day} {start_time:%H:%M} to {end_time:%H:%M}'.format(
                    group=self.device_group,
                    day=self.get_day_display(),
                    start_time=self.start_time,
                    end_time=self.end_time,
            )

    def clean(self):
        """ Ensure that schedules don't clash, and that schedules have a valid time range. """
        if self.default:
            if self.start_time is not None or self.end_time is not None:
                raise ValidationError('Default schedules cannot have a start and/or end time')
        else:

            if self.start_time is None:
                raise ValidationError({'start_time': 'Start time cannot be empty.'})

            if self.end_time is None:
                raise ValidationError({'end_time': 'End time cannot be empty.'})

            if self.end_time <= self.start_time:
                raise ValidationError('Ending time must be after starting time.')

            # Find intersecting schedules where one schedule starts in the middle of another
            # on the same day for the same device.
            intersecting_schedules = ScheduledContent.objects.filter(
                    day=self.day,
                    device_group=self.device_group
            ).filter(
                    # Find schedules starting in the middle of this schedule
                    Q(start_time__gte=self.start_time, start_time__lt=self.end_time) |
                    # Find schedules ending in the middle of this schedule
                    Q(end_time__gt=self.start_time, end_time__lte=self.end_time) |
                    # Find schedules that start before this schedule but end after it
                    Q(start_time__lte=self.start_time, end_time__gte=self.end_time)
            ).exclude(id=self.id)
            # Also filter current id in case we are editing an existing schedule, in which case
            # it will probably intersect with itself.

            if intersecting_schedules:
                raise ValidationError('Two schedules should not intersect.')

    class Meta:
        verbose_name = 'Scheduled Content'
        verbose_name_plural = 'Scheduled Content'
        # Ensures that the schedules are sorted by starting time with default schedules at the end
        ordering = ('-default', 'start_time',)

    def _ensure_content_feed(self):
        if not hasattr(self, 'content'):
            content_feed = self.device_group.feed
            content_feed.id = None
            content_feed.title = 'Content for {}'.format(self)
            content_feed.auto_created = True
            content_feed.save()
            self.content = content_feed


class SpecialContent(models.Model):
    """ Allows setting a special content feed for a particular date. """
    date = models.DateField()
    content = models.ForeignKey(ContentFeed, on_delete=models.CASCADE)
    device_group = models.ForeignKey('devicemanager.DeviceGroup', on_delete=models.CASCADE)

    def _ensure_content_feed(self):
        if not hasattr(self, 'content'):
            content_feed = self.device_group.feed
            content_feed.id = None
            content_feed.title = 'Content for {}'.format(self)
            content_feed.auto_created = True
            content_feed.save()
            self.content = content_feed

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        Ensure that newly added spcial content automatically gets an associated content feed.
        """
        self._ensure_content_feed()
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        return '{group}: {date}'.format(
                group=self.device_group,
                date=self.date
        )

    class Meta:
        verbose_name_plural = 'Special Content'
        unique_together = (('device_group', 'date',),)
        ordering = ('date',)
