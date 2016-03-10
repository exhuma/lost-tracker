import logging
import re

from flask import current_app


LOG = logging.getLogger(__name__)


def start_time_to_order(value):
    """
    Convert a time-string to a numeric value which can be used in the "order"
    field.

    It simply removes all non-numeric characters and casts it to int. This is
    done so the value remains somewhat human-readable.
    """
    if not value:
        return 0

    try:
        return int(re.sub(r'[^0-9]', '', value))
    except ValueError as exc:
        LOG.warning('Unable to parse {!r} into a number ({})'.format(
            value, exc))
        return 0


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    app_login = current_app.localconf.get('app', 'login')
    app_password = current_app.localconf.get('app', 'password')

    return username == app_login and password == app_password
