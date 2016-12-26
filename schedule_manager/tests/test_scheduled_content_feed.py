# -*- coding: utf-8 -*-
import datetime

import pytest

from schedule_manager.models import SpecialContent


@pytest.mark.django_db
def test_feed_for_no_schedule(device_group_with_feed_1, content_feed_1):
    assert device_group_with_feed_1._get_group_content_feed() == device_group_with_feed_1.feed


@pytest.mark.django_db
def test_feed_for_default_schedule(device_group_with_feed_1,
                                   scheduled_content_default_today):
    assert (
            device_group_with_feed_1._get_group_content_feed()
            ==
            scheduled_content_default_today.content
    )


@pytest.mark.django_db
def test_feed_for_timed_schedule(device_group_with_feed_1,
                                 scheduled_content_default_today,
                                 scheduled_content_current):
    assert device_group_with_feed_1._get_group_content_feed() == scheduled_content_current.content


@pytest.mark.django_db
def test_feed_for_special_content(device_group_with_feed_1, content_feed_3,
                                  scheduled_content_default_today):
    special_content = SpecialContent.objects.create(
            date=datetime.date.today(),
            content=content_feed_3,
            device_group=device_group_with_feed_1,
    )
    assert device_group_with_feed_1._get_group_content_feed() == content_feed_3


@pytest.mark.django_db
def test_feed_for_special_content_and_schedule_1(device_group_with_feed_1, content_feed_1,
                                                 scheduled_content_current, content_feed_4):
    special_content = SpecialContent.objects.create(
            date=datetime.date.today(),
            content=content_feed_4,
            device_group=device_group_with_feed_1,
    )
    assert device_group_with_feed_1._get_group_content_feed() == content_feed_4
