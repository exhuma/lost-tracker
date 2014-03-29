import re
import logging

LOG = logging.getLogger(__name__)


def start_time_to_order(value):
    # Tries to put something sensical into the "order" field.
    # If unsuccessful, return 0. Can be edited later.
    try:
        return int(re.sub(r'[^0-9]', '', value))
    except ValueError as exc:
        LOG.warning('Unable to parse {!r} into a number ({})'.format(
            value, exc))
        return 0
