# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto import S3BotoStorage

from utils.files import DedupedMediaStorage, DedupedS3MediaStorage

if settings.USE_S3_STORAGE:
    DedupedStorage = DedupedS3MediaStorage
    NormalStorage = S3BotoStorage
else:
    DedupedStorage = DedupedMediaStorage
    NormalStorage = FileSystemStorage

__all__ = ['DedupedStorage', 'NormalStorage']
