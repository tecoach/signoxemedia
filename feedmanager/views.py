# -*- coding: utf-8 -*-
""" View for feed manager. """
from pathlib import Path

import re
import yaml
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic.base import View

from feedmanager.models import (Category, ImageFeed, ImageSnippet, VideoFeed, VideoSnippet,
                                WebFeed, WebSnippet, )
from utils import files


@xframe_options_exempt
def web_feed_view(request, slug):
    """ View to display web feed. """
    try:
        feed = WebFeed.objects.get(slug=slug)
    except WebFeed.DoesNotExist:
        raise Http404()

    try:
        return HttpResponse(feed.rendered_content())
    except WebSnippet.DoesNotExist:
        raise Http404('No snippets available for this feed')


@xframe_options_exempt
def image_feed_view(request, slug):
    """ View to display image feed. """
    try:
        feed = ImageFeed.objects.get(slug=slug)
    except ImageFeed.DoesNotExist:
        raise Http404()

    try:
        snip = feed.get_snippet_for_today()  # type: ImageSnippet
    except ImageSnippet.DoesNotExist:
        raise Http404('No snippets available for this feed')

    return HttpResponse(snip.media, content_type='image')


@xframe_options_exempt
def video_feed_view(request, slug):
    """ View to display video feed. """
    try:
        feed = VideoFeed.objects.get(slug=slug)
    except VideoFeed.DoesNotExist:
        raise Http404()

    try:
        snip = feed.get_snippet_for_today()  # type: VideoSnippet
    except VideoSnippet.DoesNotExist:
        raise Http404('No snippets available for this feed')

    return HttpResponse(snip.media, content_type='video')


@method_decorator(staff_member_required, name='dispatch')
class BulkUploadSnippetsView(View):
    """ View to enable bulk uploading of snippets. """

    template_name = 'bulk_upload.html'
    categories = Category.objects.all()

    def _render_page(self, request, error=None, message=None):
        categories = Category.objects.all()
        return render(request, self.template_name, {
            'categories': categories,
            'error': error,
            'message': message
        })

    @staticmethod
    def _file_name_to_title(file_name):
        return re.sub(r'[-_]', ' ', file_name)

    def get(self, request):
        return self._render_page(request)

    def post(self, request):
        category_id = request.POST.get('category')
        category = Category.objects.get(pk=category_id)
        snippet_files = request.FILES.getlist('snippets')

        error = None
        message = ''

        if snippet_files is None or len(snippet_files) == 0:
            error = 'No files uploaded'

        if category is None:
            error = 'Invalid category selection'

        file_errors = {}

        for snippet_file in snippet_files:
            if (snippet_file.content_type.find('yaml') >= 0 or
                    snippet_file.name.endswith('yml') or
                    snippet_file.name.endswith('yaml')):
                error = self._create_web_snippets(snippet_file, category)
                if error is not None:
                    file_errors[snippet_file.name] = error
                continue

            date, title = self._process_file_name(snippet_file.name,
                                                  has_date=category.type == Category.DATED_TYPE)
            if snippet_file.content_type in files.IMAGE_MIMES:
                ImageSnippet.objects.create(title=title, date=date, category=category,
                                            media=snippet_file)
            elif snippet_file.content_type in files.VIDEO_MIMES:
                VideoSnippet.objects.create(title=title, date=date, category=category,
                                            media=snippet_file)
            else:
                file_errors[snippet_file.name] = 'Invalid file format'

        if error is None:
            error = self._build_error_message(file_errors)

        return self._render_page(request, error=error, message=message)

    @staticmethod
    def _build_error_message(errors):
        messages = []
        for file_name, error, in errors.items():
            messages.append('{file_name}: {error}'.format(file_name=file_name,
                                                          error=error))
        return '\n'.join(messages)

    @staticmethod
    def _process_file_name(file_name, has_date):
        date = None
        title = file_name

        if has_date:
            date, title = title.split('_', maxsplit=1)

        title = Path(title).stem  # Remove the extension
        title = re.sub(r'[-_]', ' ', title)  # Replace underscores and dashes with a space

        return date, title

    @staticmethod
    def _create_web_snippets(snippet_file, category):
        try:
            data = yaml.safe_load(snippet_file.read())
        except yaml.YAMLError:
            return 'Invalid file format'
        for item in data:
            snippet = WebSnippet(**item)
            snippet.category = category
            snippet.save()
