# -*- coding: utf-8 -*-
""" Admin setup for device manager app. """
from django.contrib import admin

from devicemanager.models import (AppBuild, AppBuildChannel, Device, DeviceGroup, DeviceScreenShot,
                                  MirrorServer, )


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """ The device admin panel setup class. """
    list_display = ('name', 'device_id', 'last_ping', 'group', 'debug_mode', 'enabled', 'owner',
                    'build_version',)
    list_filter = ('last_ping', 'group', 'debug_mode', 'enabled', 'owner', 'build_version',)
    list_editable = ('debug_mode', 'enabled',)
    fields = (
        'device_id', 'name', 'group', 'last_ping',
        ('debug_mode', 'enabled',),
        'command',
        'owner', 'build_version'
    )
    readonly_fields = ('device_id', 'last_ping', 'build_version')


@admin.register(DeviceGroup)
class DeviceGroupAdmin(admin.ModelAdmin):
    """ The device group admin panel setup class. """
    list_display = ('name', 'owner', 'display_date_time', 'mirror', 'orientation')
    list_filter = ('owner', 'orientation')


@admin.register(AppBuild)
class AppBuildAdmin(admin.ModelAdmin):
    """ The AppBuild admin panel setup class. """
    list_display = ('__str__', 'version_code', 'release_channel')


@admin.register(MirrorServer)
class MirrorServerAdmin(admin.ModelAdmin):
    list_display = ('name', 'mirror_id', 'address', 'last_ping', 'owner',)
    list_filter = ('owner',)
    readonly_fields = ('mirror_id', 'last_ping',)


@admin.register(DeviceScreenShot)
class DeviceScreenShotAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'device', 'timestamp')
    list_filter = ('device', 'timestamp', 'device__owner')
    readonly_fields = ('timestamp',)


admin.site.register(AppBuildChannel)
