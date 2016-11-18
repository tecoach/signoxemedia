# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-02 00:46
from __future__ import unicode_literals

import storages.backends.s3boto
from django.conf import settings
from django.db import migrations, models

import notification_manager.models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notification_manager', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
                model_name='posttopic',
                name='image',
                field=models.ImageField(storage=storages.backends.s3boto.S3BotoStorage(),
                                        upload_to=notification_manager.models.post_topic_icon_location),
        ),
        migrations.AlterUniqueTogether(
                name='userpoststatus',
                unique_together=set([('user', 'post')]),
        ),
    ]
