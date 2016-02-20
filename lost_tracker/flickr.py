import logging
from json import loads

import requests

from lost_tracker.localtypes import Photo

LOG = logging.getLogger(__name__)


def get_photos(conf):
    key = conf.get('flickr', 'api_key', default=None)
    photoset_id = conf.get('flickr', 'photoset_id', default=None)

    if not key or not photoset_id:
        LOG.debug('No key or photoset ID given. Not loading any photos!')
        return {
            'title': 'Nothing here yet',
            'photos': []
        }

    response = requests.get(
        'https://api.flickr.com/services/rest/?'
        'method=flickr.photoSets.getPhotos&'
        'api_key={key}&format=json&'
        'photoset_id={photoset_id}'.format(
            key=key,
            photoset_id=photoset_id))
    data = loads(response.text[14:-1])

    url_template = ('http://farm{0[farm]}.staticflickr.com/{0[server]}/'
                    '{0[id]}_{0[secret]}_{1}.jpg')
    try:
        urls = [Photo(url_template.format(photo, 'q'),
                      url_template.format(photo, 'b'))
                for photo in data['photoset']['photo']]
        return {
            'title': data['photoset']['title'],
            'photos': urls
        }
    except Exception as exc:
        LOG.error(exc)
        return {
            'title': 'Something went wrong when fetching photos from flickr!',
            'photos': []
        }
