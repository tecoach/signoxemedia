# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-24 11:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('devicemanager', '0013_prioritymessage'),
    ]

    operations = [
        migrations.AddField(
                model_name='devicegroup',
                name='orientation',
                field=models.CharField(choices=[('LANDSCAPE', 'Landscape'),
                                                ('REVERSE_LANDSCAPE', 'Landscape Reversed'),
                                                ('PORTRAIT', 'Portrait'),
                                                ('REVERSE_PORTRAIT', 'Portrait Reversed')],
                                       default='LANDSCAPE', max_length=20),
        ),
    ]
