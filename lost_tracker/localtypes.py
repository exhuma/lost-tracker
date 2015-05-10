from collections import namedtuple

from sqlalchemy.orm.query import Query


Photo = namedtuple('Photo', 'thumbnail_url, fullsize_url')


def json_encoder(value):
    if hasattr(value, 'to_dict'):
        return value.to_dict()
    elif isinstance(value, Query):
        return list(value)
    raise TypeError('%s is not JSON encodable' % value.__class__.__name__)
