# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-22 19:25
from __future__ import unicode_literals

import taggit.managers
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('mediamanager', '0012_auto_20171106_2208'),
    ]

    operations = [
        migrations.AddField(
                model_name='asset',
                name='tags',
                field=taggit.managers.TaggableManager(
                        help_text='A comma-separated list of tags.',
                        through='taggit.TaggedItem', to='taggit.Tag',
                        verbose_name='Tags'),
        ),
        migrations.AddField(
                model_name='webassettemplate',
                name='help_text',
                field=models.TextField(
                        default='This template allows you to quickly create an asset '
                                'by filling in a few parameters.\n\n'
                                'Fill in the placeholders and save the asset '
                                'to use it in a playlist.',
                        help_text='Some helpful text to describe how to use this template '
                                  'and it\'s variables.'),
                preserve_default=False,
        ),
    ]
