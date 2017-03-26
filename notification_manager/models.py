# -*- coding: utf-8 -*-
from pathlib import PurePath

import mistune
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from storages.backends.s3boto import S3BotoStorage

User = get_user_model()
markdown = mistune.Markdown()


def post_topic_icon_location(instance, filename):
    return 'media/post-topic-icons/{upload_name}{extension}'.format(
            upload_name=instance.name,
            extension=PurePath(filename).suffix
    )


class PostTopic(models.Model):
    name = models.CharField(max_length=24)
    image = models.ImageField(storage=S3BotoStorage(), upload_to=post_topic_icon_location)

    def __str__(self):
        return self.name


class Post(models.Model):
    title = models.CharField(
            max_length=255,
            help_text='A title for this post. '
                      'The title should be short, and to the point.')
    topic = models.ForeignKey(
            PostTopic,
            help_text='Topics let you organise posts.')
    body = models.TextField(
            help_text='The main body of the text in Markdown format. '
                      'It will be rendered to HTML before being displayed to users.')
    posted_on = models.DateTimeField(auto_now_add=True)

    @property
    def content(self):
        return markdown(self.body)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-posted_on']


class UserPostStatus(models.Model):
    user = models.ForeignKey(User)
    post = models.ForeignKey(Post)
    read_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'post')


# noinspection PyUnusedLocal
@receiver(signal=post_save, sender=Post)
def add_post_user_status_for_post(sender, instance, **kwargs):
    for user in User.objects.all():
        UserPostStatus.objects.get_or_create(user=user, post=instance)


# noinspection PyUnusedLocal
@receiver(signal=post_save, sender=User)
def add_post_user_status_for_user(sender, instance, **kwargs):
    one_month_ago = timezone.now() - timezone.timedelta(days=31)
    # Only create a status for posts in the past month
    for post in Post.objects.filter(posted_on__gte=one_month_ago):
        UserPostStatus.objects.get_or_create(user=instance, post=post)
