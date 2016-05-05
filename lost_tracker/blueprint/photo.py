from os import makedirs
from shutil import move
import io
import logging
import mimetypes
import os.path

from flask import (
    Blueprint,
    current_app,
    make_response,
    render_template,
    url_for,
)
from PIL import Image, ExifTags

from lost_tracker.localtypes import Photo
from lost_tracker.flickr import get_photos
import lost_tracker.core as core

mimetypes.init()
PHOTO = Blueprint('photo', __name__)
LOG = logging.getLogger(__name__)


def photo_url_generator(basename):
    return Photo(url_for('.thumbnail', basename=basename),
                 url_for('.show', basename=basename))


@PHOTO.route('/<basename>')
def show(basename):
    basename = os.path.basename(basename)
    root = current_app.localconf.get('app', 'photo_folder', default='')
    if not root:
        return

    fullname = os.path.join(root, basename)
    mimetype, _ = mimetypes.guess_type(fullname)
    with open(fullname, 'rb') as fptr:
        response = make_response(fptr.read())
    response.headers['Content-Type'] = mimetype
    return response


@PHOTO.route('/<basename>/thumbnail')
def thumbnail(basename):
    basename = os.path.basename(basename)
    root = current_app.localconf.get('app', 'photo_folder', default='')
    if not root:
        return

    fullname = os.path.join(root, basename)
    mimetype, _ = mimetypes.guess_type(fullname)

    try:
        im = Image.open(fullname)
    except IOError as exc:
        LOG.exception(exc)
        quarantine = os.path.join(root, 'quarantine')
        if not os.path.exists(quarantine):
            makedirs(quarantine)
        move(fullname, quarantine)
        return 'Unreadable Image :(', 500

    exif_orientation_id = None
    for tag in ExifTags.TAGS:
        if ExifTags.TAGS[tag] == 'Orientation':
            exif_orientation_id = tag
            break

    orientation = None
    if hasattr(im, '_getexif'):
        exif = im._getexif()
        if exif:
            orientation = exif.get(exif_orientation_id)

    if orientation == 3:
        im = im.rotate(180, expand=True)
    elif orientation == 6:
        im = im.rotate(270, expand=True)
    elif orientation == 8:
        im = im.rotate(90, expand=True)

    im.thumbnail((150, 150), Image.ANTIALIAS)
    blob = io.BytesIO()
    im.save(blob, 'jpeg')

    response = make_response(blob.getvalue())
    response.headers['Content-Type'] = mimetype
    return response


@PHOTO.route('/')
@PHOTO.route('/gallery')
def gallery():
    galleries = []

    local_data = core.get_local_photos(
        current_app.localconf, photo_url_generator)
    if local_data:
        galleries.append(local_data)

    flickr_data = get_photos(current_app.localconf)
    if flickr_data:
        galleries.append(flickr_data)

    return render_template('gallery.html', galleries=galleries)
