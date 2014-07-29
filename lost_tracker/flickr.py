import logging
from json import loads

import requests

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
    data = loads(response.content[14:-1])
    try:
        return {
            'title': data['photoset']['title'],
            'photos': data['photoset']['photo']
        }
    except Exception as exc:
        LOG.error(exc)
        return {
            'title': 'Something went wrong when fetching photos from flickr!',
            'photos': []
        }
