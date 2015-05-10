from functools import wraps
import logging
import re

from flask import request, Response, current_app


LOG = logging.getLogger(__name__)


def start_time_to_order(value):
    # Tries to put something sensical into the "order" field.
    # If unsuccessful, return 0. Can be edited later.
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


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def basic_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated
