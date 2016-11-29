# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-14 12:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('client_manager', '0002_client_display_device_logo'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='device_logo',
            field=models.ImageField(blank=True,
                                    help_text='A logo of the client for use on the device.',
                                    null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='client',
            name='display_device_logo',
            field=models.BooleanField(default=True,
                                      help_text='Whether a logo should be shown on the device or '
                                                'not. '),
        ),
        migrations.AlterField(
            model_name='client',
            name='logo',
            field=models.ImageField(help_text='A logo of the client for use in the frontend.',
                                    upload_to=''),
        ),
        migrations.AlterField(
            model_name='client',
            name='name',
            field=models.CharField(help_text='Name of client', max_length=100),
        ),
    ]