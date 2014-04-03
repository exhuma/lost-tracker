import logging
from json import loads

import requests

LOG = logging.getLogger(__name__)


def get_photos(conf):
    key = conf.get('flickr', 'api_key')
    response = requests.get(
        'https://api.flickr.com/services/rest/?'
        'method=flickr.photoSets.getPhotos&'
        'api_key={key}&format=json&'
        'photoset_id=72157642905812775'.format(key=key))
    data = loads(response.content[14:-1])
    try:
        return data['photoset']['photo']
    except Exception as exc:
        LOG.error(exc)
        return []
