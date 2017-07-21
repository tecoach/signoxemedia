# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-02 11:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('devicemanager', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='device',
            name='group',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=django.db.models.deletion.CASCADE,
                                    to='devicemanager.DeviceGroup'),
        ),
        migrations.AlterField(
            model_name='device',
            name='location',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=django.db.models.deletion.CASCADE,
                                    to='devicemanager.DeviceLocation'),
        ),
    ]
