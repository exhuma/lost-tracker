from datetime import datetime
import logging

from config_resolver import Config
from flask.ext.babel import Babel, gettext
from flask.ext.security import (
    SQLAlchemyUserDatastore,
    Security,
    login_user,
)
from flask import (
    Flask,
    current_app,
    flash,
    redirect,
    session as flask_session,
    url_for,
)
from sqlalchemy.orm.exc import NoResultFound

from lost_tracker.blueprint.comment import COMMENT
from lost_tracker.blueprint.group import GROUP
from lost_tracker.blueprint.photo import PHOTO
from lost_tracker.blueprint.qr import QR
from lost_tracker.blueprint.registration import REGISTRATION
from lost_tracker.blueprint.root import ROOT
from lost_tracker.blueprint.station import STATION
from lost_tracker.blueprint.tabedit import TABULAR
from lost_tracker.blueprint.user import USER
from lost_tracker.emails import Mailer, DummyMailer

import lost_tracker.models as mdl
import lost_tracker.fbhelper as fb

from lost_tracker.const import (
    COMMENT_PREFIX,
    GROUP_PREFIX,
    PHOTO_PREFIX,
    QR_PREFIX,
    REGISTRATION_PREFIX,
    STATION_PREFIX,
    TABULAR_PREFIX,
    USER_PREFIX,
)


LOG = logging.getLogger(__name__)


def _add_social_params(connections, identifier, conf):
    """
    Adds an oauth provider to the social connections dictionary, but only if
    values are properly set (non-empty).
    """
    key = conf.get(identifier, 'consumer_key', default='').strip()
    secret = conf.get(identifier, 'consumer_secret', default='').strip()
    conf_key = 'SOCIAL_%s' % identifier.upper()

    if key and secret:
        connections[conf_key] = {
            'consumer_key': key,
            'consumer_secret': secret
        }
        if identifier == 'google':
            connections[conf_key]['request_token_params'] = {
                'scope': ('https://www.googleapis.com/auth/userinfo.profile '
                          'https://www.googleapis.com/auth/plus.me '
                          'https://www.googleapis.com/auth/userinfo.email')
            }


def make_app():

    babel = Babel()
    security = Security()
    user_datastore = SQLAlchemyUserDatastore(mdl.DB, mdl.User, mdl.Role)

    app = Flask(__name__)

    app.user_datastore = user_datastore
    app.localconf = lconf = Config('mamerwiselen', 'lost-tracker',
                                   version='2.0', require_load=True)
    app.config['SECRET_KEY'] = lconf.get('app', 'secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = lconf.get('db', 'dsn')
    mdl.DB.init_app(app)

    # Social connections
    social_connections = {}
    _add_social_params(social_connections, 'facebook', app.localconf)
    _add_social_params(social_connections, 'twitter', app.localconf)
    _add_social_params(social_connections, 'google', app.localconf)

    if len(social_connections) < 1:
        LOG.error('No Social/OAuth providers defined! Users will not be '
                  'able to log-in!')

    app.config.update(social_connections)

    security.init_app(app, user_datastore)

    app.register_blueprint(COMMENT, url_prefix=COMMENT_PREFIX)
    app.register_blueprint(GROUP, url_prefix=GROUP_PREFIX)
    app.register_blueprint(PHOTO, url_prefix=PHOTO_PREFIX)
    app.register_blueprint(QR, url_prefix=QR_PREFIX)
    app.register_blueprint(REGISTRATION, url_prefix=REGISTRATION_PREFIX)
    app.register_blueprint(ROOT)
    app.register_blueprint(STATION, url_prefix=STATION_PREFIX)
    app.register_blueprint(TABULAR, url_prefix=TABULAR_PREFIX)
    app.register_blueprint(USER, url_prefix=USER_PREFIX)
    babel.init_app(app)
    babel.localeselector(get_locale)
    return app


def userbool(value):
    return value.lower()[0:1] in ('t', '1')


def get_locale():
    locale = flask_session.get('lang', 'lb')
    current_app.logger.debug('Using locale {}'.format(locale))
    return locale


def fake_login():
    """
    Dummy login function. Logs in any user without password.

    This should only made available during development! This currently is only
    added to the URL rules if the application is started manually. When running
    as a WSGI app (f.ex.: behind Apache), this route is unavailable for obvious
    reasons.
    """
    from flask.ext.security import login_user
    from flask import request
    if not current_app.debug:
        return 'Access Denied!', 500

    usermail = request.args.get('email', 'admin@example.com')

    user_query = mdl.DB.session.query(mdl.User).filter_by(email=usermail)
    user = user_query.first()
    if not user:
        user = current_app.user_datastore.create_user(
            email=usermail,
            name='Fake User',
            active=True,
            confirmed_at=datetime.now(),
        )
    else:
        mdl.DB.session.add(user)

    if 'admin' in usermail:
        role_query = mdl.DB.session.query(mdl.Role).filter_by(
            name=mdl.Role.ADMIN)
        try:
            role = role_query.one()
        except NoResultFound:
            role = mdl.Role(name=mdl.Role.ADMIN)
        user.roles.append(role)
    elif 'staff' in usermail:
        role_query = mdl.DB.session.query(mdl.Role).filter_by(name='staff')
        try:
            role = role_query.one()
        except NoResultFound:
            role = mdl.Role(name=mdl.Role.STAFF)
        user.roles.append(role)

    current_app.user_datastore.commit()
    login_user(user)
    mdl.DB.session.commit()
    return redirect(url_for('root.profile'))


if __name__ == '__main__':
    from lost_tracker.colorize import colorize_werkzeug
    colorize_werkzeug()
    myapp = make_app()
    myapp.add_url_rule('/fake_login', 'fake_login', fake_login)
    DEBUG = userbool(myapp.localconf.get('devserver', 'debug',
                                         default=False))
    if DEBUG:
        myapp.mailer = DummyMailer()
    else:
        myapp.mailer = Mailer()
    myapp.run(debug=DEBUG,
              host=myapp.localconf.get('devserver', 'listen'),
              port=int(myapp.localconf.get('devserver', 'port')))
