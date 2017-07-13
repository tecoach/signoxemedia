# -*- coding: utf-8 -*-
""" This module contains miscellaneous file-related utility functions and classes. """
import json
import subprocess

import hashlib
import io
import magic
import os
import tempfile
from PIL import Image
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from pilkit.processors import ResizeToFit
from storages.backends.s3boto import S3BotoStorage

FFMPEG_PATH = 'ffmpeg'
FFPROBE_PATH = 'ffprobe'
EXIFTOOL_PATH = 'exiftool'
SCREENSHOT_PATH = os.path.join(settings.BASE_DIR, 'utils', 'screenshot.js')


def generate_web_thumbnail_phantomjs(source, width, height, image_format='JPEG'):
    """
    Uses phantomjs and the included screenshot.js script to generate a thumbnail image for a
    web page.
    """
    # create a temporary file with the .png extension
    (_, temp_output) = tempfile.mkstemp(suffix='.png')
    try:
        # We use phantomjs and screenshot.js to generate a full-sized PNG
        # capture of the web page which is then resized to the specified
        # dimensions using the generate_image_thumbnail function.
        # The command runs in check mode so if there is any error running the
        # command, an error will be raised which sentry will then capture.
        subprocess.check_call([
            'phantomjs',
            SCREENSHOT_PATH,
            source,  # web page url
            temp_output  # save to output
        ], )
        return generate_image_thumbnail(temp_output, width, height, image_format)
    finally:
        os.remove(temp_output)


def generate_web_thumbnail_chromium(source, width, height, image_format='JPEG'):
    """Uses chromium headless to generate a thumbnail image for a web page."""
    # create a temporary directory to store the screenshot
    temp_output_dir = tempfile.mkdtemp()
    output_file = None
    try:
        # We use chromium in headless mode to generate a full-sized PNG capture
        # of the web page which is then resized to the specified dimensions
        # using the generate_image_thumbnail function.
        # The command runs in check mode so if there is any error running the
        # command, an error will be raised which sentry will then capture.
        subprocess.check_call([
            'chromium',
            '--headless',
            '--disable-gpu',
            '--screenshot',
            '--window-size=1152,648',
            source,  # web page url
        ], cwd=temp_output_dir)
        output_file = os.path.join(temp_output_dir, 'screenshot.png')
        return generate_image_thumbnail(output_file, width, height, image_format)
    finally:
        if output_file:
            os.remove(output_file)
        os.rmdir(temp_output_dir)


generate_web_thumbnail = generate_web_thumbnail_chromium


def generate_video_thumbnail(source, width, height, image_format='JPEG'):
    """
    Uses FFMPEG via the subprocess module to generate a thumbnail image for a video.
    """
    # create a temporary file with the .png extension
    (_, temp_output) = tempfile.mkstemp(suffix='.png')
    try:
        # We use ffmpeg to generate a full-sized PNG capture, which is then
        # resized to the specified dimensions using the generate_image_thumbnail
        # function.
        # The command runs in check mode so if there is any error running the
        # command, an error will be raised which sentry will then capture.
        subprocess.check_call([
            FFMPEG_PATH,
            '-y',  # overwrite without asking since it's writing to a new temp file.
            '-i', source,  # input video file
            # The following parameters will apply a filter that will create a
            # 3x3 tile of frames that have a width of 316 and proportional
            # height. There will be a 3 pixel border around the image and 3
            # pixel padding between frames. The frames themselves will be
            # selected when ffmpeg detects a scene change with a threshold of 0.1
            '-vf', "select='gt(scene\,0.1)',scale=316:-1,tile=3x3:margin=3:padding=3",
            '-frames:v', '1',  # capture a single frame
            temp_output  # save to output
        ], )
        return generate_image_thumbnail(temp_output, width, height, image_format)
    finally:
        os.remove(temp_output)


def generate_image_thumbnail(source, width, height, image_format='JPEG'):
    """
    Generates a thumbnail of the provided image that has the specified maximum dimensions.
    """
    image = Image.open(source)
    processor = ResizeToFit(width=width, height=height)
    resized = processor.process(image).convert('RGB')
    resized_image = io.BytesIO()
    resized.save(resized_image, format=image_format)
    return resized_image


def md5_file_name(instance, filename):
    # type: (FileAsset, str) -> str
    """This function is used to generate checksum-based file names for uploaded files."""
    h = instance.checksum
    basename, ext = os.path.splitext(filename)
    return os.path.join(h[1:2], h + ext.lower())


class DedupedMediaStorage(FileSystemStorage):
    """
    A storage class designed for deduplicated storage. It multiple references
    to the same file name, and if a file already exists, it returns a reference
    to the exising file.

    :note:
    It is designed to work with files that are hashes of their content so two
    file with a duplicate name are essentially the same file.
    """

    def get_available_name(self, name, max_length=None):
        """ Since this storage is deduplicated, a name is available even if it's already used. """
        return name

    def _save(self, name, content):
        """ Returns the file name if it already exists without saving the content. """
        if self.exists(name):
            return name
        return super(DedupedMediaStorage, self)._save(name, content)


class DedupedS3MediaStorage(S3BotoStorage):
    """
    A storage class designed for deduplicated storage on Amazon S3. It multiple references to the
    same file name, and if a file already exists, it returns a reference to the exising file.

    :note:
    It is designed to work with files that are hashes of their content so two file with a duplicate
    name are essentially the same file.
    """

    file_overwrite = True

    def _save(self, name, content):
        """ Returns the file name if it already exists without saving the content. """
        if self.exists(name):
            return name
        return super()._save(name, content)


def verify_mime(file, supported_types):
    """
    Checks if the provided file-like object has a mime-type that is in the provided list of
    supported MIME types.
    :param file: file-like object
    :param supported_types: list of supported MIME types
    :return: Whether file is of one of the supported types.
    """
    file_mine = magic.from_buffer(file.read(1024), mime=True)
    return file_mine in supported_types


def calculate_checksum(file_upload):
    """ Calculates md5 checksum of provided file upload. """
    md5 = hashlib.md5()
    for chunk in file_upload.chunks():
        md5.update(chunk)
    return md5.hexdigest()


IMAGE_MIMES = ['image/png', 'image/jpeg', 'image/pjpeg']
VIDEO_MIMES = ['video/mp4', 'video/webm']


def get_video_metadata(video_file):
    ffprobe_command = (
        FFPROBE_PATH,
        '-v', 'error',  # Output only the data we need and nothing else
        '-show_streams',
        '-show_format',
        '-unit', '-prefix', '-sexagesimal',  # Output units with SI prefixes
        # and use a sexagesimal timecode
        '-of', 'json',  # Output in JSON format
        video_file.url
    )
    try:
        output = subprocess.check_output(ffprobe_command)
        metadata = json.loads(output.decode('utf-8'))
    except subprocess.CalledProcessError:
        return None
    return metadata


def get_image_metadata(image_file):
    exiftool_command = (
        EXIFTOOL_PATH,
        '-json',  # Output in JSOn
        '-g',  # Output information in groups
        '--ThumbnailImage',  # Don't include ThumbnailImage
        '-',  # Take input from stdin
    )
    try:
        exiftool_process = subprocess.Popen(exiftool_command,
                                            stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
        stdout, stderr = exiftool_process.communicate(image_file.read())
        metadata = json.loads(stdout.decode('utf-8'), encoding='utf-8')[0]

        # Remove SourceFile and ExifTool keys from metadata they convey
        # no information
        if 'SourceFile' in metadata:
            del metadata['SourceFile']
        if 'ExifTool' in metadata:
            del metadata['ExifTool']

        return metadata
    except subprocess.CalledProcessError:
        return None


VIDEO_STREAM_MAP = (
    ('index', 'Stream Index'),
    ('codec_long_name', 'Codec'),
    ('width', 'Width'),
    ('height', 'Height'),
    ('display_aspect_ratio', 'Aspect Ratio'),
    ('r_frame_rate', 'Frame Rate'),
    ('avg_frame_rate', 'Frame Rate'),
    ('duration', 'Duration'),
    ('bit_rate', 'Bit Rate'),
)

AUDIO_STREAM_MAP = (
    ('index', 'Stream Index'),
    ('codec_long_name', 'Codec'),
    ('profile', 'Profile'),
    ('sample_rate', 'Sample Rate'),
    ('channels', 'Channels'),
    ('channel_layout', 'Channel Layout'),
    ('duration', 'Duration'),
    ('bit_rate', 'Bit Rate'),
)

SUBTITLE_STREAM_MAP = (
    ('index', 'Stream Index'),
    ('codec_long_name', 'Codec'),
    ('duration', 'Duration'),
)

VIDEO_FORMAT_MAP = (
    ('format_long_name', 'Format'),
    ('duration', 'Duration'),
    ('nb_streams', 'Stream count'),
    ('size', 'Size'),
    ('bit_rate', 'Bit Rate'),
)


def _clean_stream(stream, stream_map):
    data = {}
    for key, new_key in stream_map:
        if key in stream:
            data[new_key] = stream[key]
    return data


def clean_video_metadata(raw_metadata):
    if raw_metadata is None:
        return None
    metadata = {}

    format_data = raw_metadata.get('format')
    if format_data is not None:
        for key, new_key in VIDEO_FORMAT_MAP:
            if key in format_data:
                metadata.setdefault('format', {})[new_key] = format_data[key]

    for stream in raw_metadata.get('streams', []):
        codec_type = stream.get('codec_type')
        if codec_type == 'audio':
            clean_stream = _clean_stream(stream, AUDIO_STREAM_MAP)
            metadata.setdefault('audio_streams', []).append(clean_stream)
        elif codec_type == 'video':
            clean_stream = _clean_stream(stream, VIDEO_STREAM_MAP)
            metadata.setdefault('video_streams', []).append(clean_stream)
        elif codec_type == 'subtitle':
            clean_stream = _clean_stream(stream, SUBTITLE_STREAM_MAP)
            metadata.setdefault('subtitle_streams', []).append(clean_stream)

    return json.dumps(metadata)


IMAGE_METADATA_KEY_FIELDS = {
    'File': (('FileType', 'File Type'),
             ('ImageWidth', 'Width'),
             ('ImageHeight', 'Height')),
    'EXIF': (('CreateDate', 'Creation Date'),
             ('UserComment', 'Comment')),
    'Composite': (('Megapixels', 'Megapixels'),
                  ('GPSPosition', 'GPS Position'),
                  ('GPSAltitude', 'GPS Altitude'))
}


def clean_image_metadata(raw_metadata):
    if raw_metadata is None:
        return None

    metadata = {}

    for group, tags in IMAGE_METADATA_KEY_FIELDS.items():
        group_data = raw_metadata.get(group)
        if group_data is not None:
            for key, new_key in tags:
                group_value = group_data.get(key)
                if group_value is not None:
                    metadata.setdefault(group, {})[new_key] = group_value

    print(json.dumps(metadata))
    return json.dumps(metadata)
