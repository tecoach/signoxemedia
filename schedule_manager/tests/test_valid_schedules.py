# -*- coding: utf-8 -*-
import datetime

import pytest
from django.core.exceptions import ValidationError

from schedule_manager.models import ScheduledContent, WeekDays


@pytest.mark.django_db
def test_disallow_start_time_after_end_time(device_group_1, content_feed_1):
    scheduled_content = ScheduledContent(
            day=WeekDays.FRIDAY,
            default=False,
            start_time=datetime.time(11, 5, 0),
            end_time=datetime.time(10, 2, 3),
            content=content_feed_1,
            device_group=device_group_1
    )
    with pytest.raises(ValidationError):
        scheduled_content.save()


@pytest.mark.django_db
@pytest.mark.parametrize('group_1,group_2,day_1,day_2', (
        ('device_group_1', 'device_group_1', WeekDays.MONDAY, WeekDays.TUESDAY),
        ('device_group_1', 'device_group_2', WeekDays.MONDAY, WeekDays.MONDAY),
        ('device_group_1', 'device_group_2', WeekDays.MONDAY, WeekDays.TUESDAY),
))
@pytest.mark.parametrize('start_time_1,end_time_1,start_time_2,end_time_2', (
        # Second slice contained in first slice
        (datetime.time(11, 5, 0), datetime.time(12, 0, 5),
         datetime.time(11, 11, 3), datetime.time(11, 55, 50),),
        # First slice contained in second slice
        (datetime.time(11, 5, 0), datetime.time(12, 0, 5),
         datetime.time(10, 11, 3), datetime.time(13, 55, 50),),
        # Second start contained in first slice
        (datetime.time(11, 5, 0), datetime.time(12, 0, 5),
         datetime.time(11, 11, 3), datetime.time(13, 55, 50),),
        # Second end contained in first slice
        (datetime.time(11, 5, 0), datetime.time(12, 0, 5),
         datetime.time(10, 11, 3), datetime.time(11, 55, 50),),
))
def test_allow_intersection_across_days_and_groups(group_1, group_2,
                                                   day_1, day_2,
                                                   start_time_1, end_time_1,
                                                   start_time_2, end_time_2,
                                                   content_feed_1,
                                                   request):
    group_1 = request.getfuncargvalue(group_1)
    group_2 = request.getfuncargvalue(group_2)
    ScheduledContent.objects.create(
            day=day_1,
            default=False,
            start_time=start_time_1,
            end_time=end_time_1,
            content=content_feed_1,
            device_group=group_1
    )
    scheduled_content = ScheduledContent(
            day=day_2,
            default=False,
            start_time=start_time_2,
            end_time=end_time_2,
            content=content_feed_1,
            device_group=group_2
    )
    assert scheduled_content.save() is None


@pytest.mark.django_db
@pytest.mark.parametrize('start_time_1,end_time_1,start_time_2,end_time_2', (
        # Second slice contained in first slice
        (datetime.time(11, 5, 0), datetime.time(12, 0, 5),
         datetime.time(11, 11, 3), datetime.time(11, 55, 50),),
        # First slice contained in second slice
        (datetime.time(11, 5, 0), datetime.time(12, 0, 5),
         datetime.time(10, 11, 3), datetime.time(13, 55, 50),),
        # Second start contained in first slice
        (datetime.time(11, 5, 0), datetime.time(12, 0, 5),
         datetime.time(11, 11, 3), datetime.time(13, 55, 50),),
        # Second end contained in first slice
        (datetime.time(11, 5, 0), datetime.time(12, 0, 5),
         datetime.time(10, 11, 3), datetime.time(11, 55, 50),),
))
def test_disallow_intersection_for_same_day_and_group(device_group_1,
                                                      start_time_1, end_time_1,
                                                      start_time_2, end_time_2,
                                                      content_feed_1):
    ScheduledContent.objects.create(
            day=WeekDays.FRIDAY,
            default=False,
            start_time=start_time_1,
            end_time=end_time_1,
            content=content_feed_1,
            device_group=device_group_1
    )
    scheduled_content = ScheduledContent(
            day=WeekDays.FRIDAY,
            default=False,
            start_time=start_time_2,
            end_time=end_time_2,
            content=content_feed_1,
            device_group=device_group_1
    )
    with pytest.raises(ValidationError):
        scheduled_content.save()


@pytest.mark.django_db
def test_allow_editing_range_for_existing_schedule(device_group_1, content_feed_1):
    scheduled_content = ScheduledContent(
            day=WeekDays.FRIDAY,
            default=False,
            start_time=datetime.time(9, 5, 0),
            end_time=datetime.time(10, 2, 3),
            content=content_feed_1,
            device_group=device_group_1
    )
    scheduled_content.save()
    scheduled_content.start_time = datetime.time(9, 10, 0)
    scheduled_content.save()


@pytest.mark.django_db
@pytest.mark.parametrize('start_time,end_time', (
        (datetime.time(11, 5, 0), datetime.time(12, 0, 5)),
        (datetime.time(11, 5, 0), None,),
        (None, datetime.time(12, 0, 5),),
))
def test_ensure_no_start_end_time_for_default(start_time,
                                              end_time,
                                              content_feed_1,
                                              device_group_1):
    scheduled_content = ScheduledContent(
            day=WeekDays.WEDNESDAY,
            default=True,
            start_time=start_time,
            end_time=end_time,
            content=content_feed_1,
            device_group=device_group_1
    )

    with pytest.raises(ValidationError):
        scheduled_content.save()


@pytest.mark.django_db
@pytest.mark.parametrize('start_time,end_time', (
        (datetime.time(11, 5, 0), None,),
        (None, datetime.time(12, 0, 5),),
        (None, None),
))
def test_ensure_start_end_time_for_non_default(start_time, end_time, content_feed_1,
                                               device_group_1):
    scheduled_content = ScheduledContent(
            day=WeekDays.THURSDAY,
            default=False,
            start_time=start_time,
            end_time=end_time,
            content=content_feed_1,
            device_group=device_group_1
    )

    with pytest.raises(ValidationError):
        scheduled_content.save()
