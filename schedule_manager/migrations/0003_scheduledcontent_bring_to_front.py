# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-16 07:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('schedule_manager', '0002_auto_20170305_0251'),
    ]

    operations = [
        migrations.AddField(
                model_name='scheduledcontent',
                name='bring_to_front',
                field=models.BooleanField(default=False),
        ),
    ]
