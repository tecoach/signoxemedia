# -*- coding: utf-8 -*-
import datetime

import pytest

from devicemanager.models import DeviceGroup
from mediamanager.models import ContentFeed
from schedule_manager.models import ScheduledContent, WeekDays


@pytest.fixture
@pytest.mark.django_db
def device_group_1():
    return DeviceGroup.objects.create(name='Device Group 1')


@pytest.fixture
@pytest.mark.django_db
def device_group_2():
    return DeviceGroup.objects.create(name='Device Group 2')


@pytest.fixture
@pytest.mark.django_db
def content_feed_1():
    return ContentFeed.objects.create(title='Content Feed 1')


@pytest.fixture
@pytest.mark.django_db
def content_feed_2():
    return ContentFeed.objects.create(title='Content Feed 2')


@pytest.fixture
@pytest.mark.django_db
def content_feed_3():
    return ContentFeed.objects.create(title='Content Feed 3')


@pytest.fixture
@pytest.mark.django_db
def content_feed_4():
    return ContentFeed.objects.create(title='Content Feed 4')


@pytest.fixture
@pytest.mark.django_db
def device_group_with_feed_1(content_feed_1):
    return DeviceGroup.objects.create(name='Device Group with Feed 1', feed=content_feed_1)


@pytest.fixture
@pytest.mark.django_db
def device_group_with_feed_2(content_feed_2):
    return DeviceGroup.objects.create(name='Device Group with Feed 2', feed=content_feed_2)


@pytest.fixture
@pytest.mark.django_db
def scheduled_content_default_today(content_feed_2, device_group_with_feed_1):
    return ScheduledContent.objects.create(
            day=WeekDays.today(),
            default=True,
            content=content_feed_2,
            device_group=device_group_with_feed_1,
    )


@pytest.fixture
@pytest.mark.django_db
def scheduled_content_default_not_today(content_feed_2, device_group_with_feed_1):
    if WeekDays.today() == WeekDays.MONDAY:
        weekday = WeekDays.TUESDAY
    else:
        weekday = WeekDays.MONDAY

    return ScheduledContent.objects.create(
            day=weekday,
            default=True,
            content=content_feed_2,
            device_group=device_group_with_feed_1,
    )


@pytest.fixture
@pytest.mark.django_db
def scheduled_content_current(content_feed_3, device_group_with_feed_1):
    time_now = datetime.datetime.now()
    start_time = (time_now - datetime.timedelta(hours=1)).time()
    end_time = (time_now + datetime.timedelta(hours=1)).time()
    if datetime.time(23, 00) <= time_now.time() <= datetime.time(23, 59):
        end_time = datetime.time(23, 59)
    if datetime.time(00, 00) <= time_now.time() <= datetime.time(1, 00):
        start_time = datetime.time(0, 0)
    return ScheduledContent.objects.create(
            day=WeekDays.today(),
            default=False,
            start_time=start_time,
            end_time=end_time,
            content=content_feed_3,
            device_group=device_group_with_feed_1,
    )
