import logging
from datetime import datetime
from sqlalchemy.orm.exc import NoResultFound

from config_resolver import Config
from flask.ext.babel import Babel
from flask.ext.social import (
    SQLAlchemyConnectionDatastore,
    Social,
    login_failed,
)
from flask.ext.social.views import connect_handler
from flask.ext.social.utils import get_connection_values_from_oauth_response
from flask.ext.security import (
    SQLAlchemyUserDatastore,
    Security,
    login_user,
)
from flask import (
    Flask,
    current_app,
    redirect,
    session as flask_session,
    url_for,
)

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


def make_app():

    babel = Babel()
    security = Security()
    social = Social()
    user_datastore = SQLAlchemyUserDatastore(mdl.DB, mdl.User, mdl.Role)

    def auto_add_user(sender, provider, oauth_response):
        connection_values = get_connection_values_from_oauth_response(
            provider, oauth_response)
        email = connection_values['email']
        if not email or not email.strip():
            email = ''

        if provider.name.lower() == 'facebook':
            fname = connection_values['full_name']
            email = get_facebook_email(oauth_response)
        elif provider.name.lower() == 'twitter':
            fname = connection_values['display_name'][1:]  # cut off leading @
        else:
            fname = connection_values['display_name']

        user = user_datastore.create_user(
            email=email,
            name=fname,
            active=True,
            confirmed_at=datetime.now(),
        )

        role_query = mdl.DB.session.query(mdl.Role).filter_by(
            name='authenticated')
        try:
            role = role_query.one()
        except NoResultFound:
            role = mdl.Role(name='authenticated')

        user.roles.append(role)
        user_datastore.commit()
        connection_values['user_id'] = user.id
        connect_handler(connection_values, provider)
        login_user(user)
        mdl.DB.session.commit()
        return redirect(url_for('root.profile'))

    app = Flask(__name__)
    app.user_datastore = user_datastore
    app.localconf = Config('mamerwiselen', 'lost-tracker',
                           version='2.0', require_load=True)
    app.config['SECRET_KEY'] = app.localconf.get('app', 'secret_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = app.localconf.get('db', 'dsn')
    mdl.DB.init_app(app)

    # Social connections
    social_connections = {}
    if 'facebook' in app.localconf.sections():
        social_connections['SOCIAL_FACEBOOK'] = {
            'consumer_key': app.localconf.get('facebook', 'consumer_key'),
            'consumer_secret': app.localconf.get('facebook', 'consumer_secret')
        }
    if 'twitter' in app.localconf.sections():
        social_connections['SOCIAL_TWITTER'] = {
            'consumer_key': app.localconf.get('twitter', 'consumer_key'),
            'consumer_secret': app.localconf.get('twitter', 'consumer_secret')
        }
    if 'google' in app.localconf.sections():
        social_connections['SOCIAL_GOOGLE'] = {
            'consumer_key': app.localconf.get('google', 'consumer_key'),
            'consumer_secret': app.localconf.get('google', 'consumer_secret'),
            'request_token_params': {
                'scope': ('https://www.googleapis.com/auth/userinfo.profile '
                          'https://www.googleapis.com/auth/plus.me '
                          'https://www.googleapis.com/auth/userinfo.email')
            }
        }

    if len(social_connections) < 1:
        raise Exception('Must at least configure one social provider '
                        '(facebook, google or twitter) in the config file!')

    app.config.update(social_connections)

    social.init_app(app, SQLAlchemyConnectionDatastore(mdl.DB, mdl.Connection))
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
    login_failed.connect(auto_add_user, app)
    return app


def get_facebook_email(oauth_response):
    from facebook import GraphAPI
    api = GraphAPI(access_token=oauth_response['access_token'], version='2.5')
    response = api.request('/me', args={'fields': 'email'})
    return response['email']


def userbool(value):
    return value.lower()[0:1] in ('t', '1')


def get_locale():
    locale = flask_session.get('lang', 'lb')
    current_app.logger.debug('Using locale {}'.format(locale))
    return locale


if __name__ == '__main__':
    myapp = make_app()
    DEBUG = userbool(myapp.localconf.get('devserver', 'debug',
                                         default=False))
    if DEBUG:
        myapp.mailer = DummyMailer()
    else:
        myapp.mailer = Mailer()
    myapp.run(debug=DEBUG,
              host=myapp.localconf.get('devserver', 'listen'),
              port=int(myapp.localconf.get('devserver', 'port')))
