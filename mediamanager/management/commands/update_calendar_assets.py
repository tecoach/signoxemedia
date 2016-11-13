# -*- coding: utf-8 -*-
""" Contains the command for update calendar assets. """
from channels import Channel
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Command to update calendar assets."""
    help = 'Updates all calendar assets'

    def handle(self, *args, **options):
        Channel('update-calendar-assets').send({})
