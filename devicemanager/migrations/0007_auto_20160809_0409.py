# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-08-08 22:39
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('devicemanager', '0006_auto_20160803_0423'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='device',
            name='location',
        ),
        migrations.DeleteModel(
            name='DeviceLocation',
        ),
    ]
