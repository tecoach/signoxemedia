# -*- coding: utf-8 -*-
"""
Contains the AceEditorWidget
"""
from django import forms


class AceEditorWidget(forms.Textarea):
    """
    Custom TextArea widget that renders Ace Editor to edit the content.
    """
    template_name = 'widgets/ace_editor.html'

    class Media:
        """ Includes media files for ace editor from CDN. """
        css = {
            'all': ('/static/ace_editor_widget/acestyle.css',)
        }
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/ace/1.2.6/ace.js',
            'https://cdnjs.cloudflare.com/ajax/libs/ace/1.2.6/theme-github.js',
            'https://cdnjs.cloudflare.com/ajax/libs/ace/1.2.6/ext-language_tools.js',
            'https://cdnjs.cloudflare.com/ajax/libs/ace/1.2.6/worker-html.js',
            'https://cdnjs.cloudflare.com/ajax/libs/ace/1.2.6/ext-beautify.js',
            'https://cdnjs.cloudflare.com/ajax/libs/ace/1.2.6/mode-html.js',
            '/static/ace_editor_widget/initace.js',
        )
