import logging
from datetime import datetime
from operator import attrgetter
try:
    from urllib.parse import unquote_plus  # py3
except ImportError:
    from urllib import unquote_plus  # py2

from sqlalchemy.orm.exc import NoResultFound

from config_resolver import Config
from flask.ext.babel import gettext, Babel, format_datetime
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
    http_auth_required,
    login_required,
    login_user,
    roles_accepted,
)
from babel.dates import format_date
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session as flask_session,
    url_for,
)
from markdown import markdown

from lost_tracker import __version__
from lost_tracker.blueprint.comment import COMMENT
from lost_tracker.blueprint.group import GROUP
from lost_tracker.blueprint.photo import PHOTO
from lost_tracker.blueprint.registration import REGISTRATION
from lost_tracker.blueprint.station import STATION
from lost_tracker.blueprint.tabedit import TABULAR
from lost_tracker.blueprint.user import USER
from lost_tracker.emails import Mailer

import lost_tracker.core as loco
import lost_tracker.models as mdl

# URL prefixes (needed in multiple locations for JS. Therefore in a variable)
COMMENT_PREFIX = '/comment'
GROUP_PREFIX = '/group'
PHOTO_PREFIX = '/photo'
REGISTRATION_PREFIX = '/registration'
STATION_PREFIX = '/station'
TABULAR_PREFIX = '/tabedit'
USER_PREFIX = '/user'


user_datastore = SQLAlchemyUserDatastore(mdl.DB, mdl.User, mdl.Role)
app = Flask(__name__)
app.localconf = Config('mamerwiselen', 'lost-tracker',
                       version='2.0', require_load=True)
app.config['SECRET_KEY'] = app.localconf.get('app', 'secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = app.localconf.get('db', 'dsn')
mdl.DB.init_app(app)
app.config['SOCIAL_FACEBOOK'] = {
    'consumer_key': app.localconf.get('facebook', 'consumer_key'),
    'consumer_secret': app.localconf.get('facebook', 'consumer_secret')
}
app.config['SOCIAL_TWITTER'] = {
    'consumer_key': app.localconf.get('twitter', 'consumer_key'),
    'consumer_secret': app.localconf.get('twitter', 'consumer_secret')
}
app.config['SOCIAL_GOOGLE'] = {
    'consumer_key': app.localconf.get('google', 'consumer_key'),
    'consumer_secret': app.localconf.get('google', 'consumer_secret'),
    'request_token_params': {
        'scope': ('https://www.googleapis.com/auth/userinfo.profile '
                  'https://www.googleapis.com/auth/plus.me '
                  'https://www.googleapis.com/auth/userinfo.email')
    }
}
security = Security(app, user_datastore)
social = Social(app, SQLAlchemyConnectionDatastore(mdl.DB, mdl.Connection))

app.register_blueprint(COMMENT, url_prefix=COMMENT_PREFIX)
app.register_blueprint(GROUP, url_prefix=GROUP_PREFIX)
app.register_blueprint(PHOTO, url_prefix=PHOTO_PREFIX)
app.register_blueprint(REGISTRATION, url_prefix=REGISTRATION_PREFIX)
app.register_blueprint(STATION, url_prefix=STATION_PREFIX)
app.register_blueprint(TABULAR, url_prefix=TABULAR_PREFIX)
app.register_blueprint(USER, url_prefix=USER_PREFIX)

babel = Babel(app)


class DummyMailer(object):
    """
    A mailer class for testing. Does not actually send any e-mails.
    """
    LOG = logging.getLogger('%s.DummyMailer' % __name__)

    def send(self, *args, **kwargs):
        self.LOG.info("DummyMailer.send called with %r %r" % (args, kwargs))


def get_facebook_email(oauth_response):
    from facebook import GraphAPI
    api = GraphAPI(access_token=oauth_response['access_token'], version='2.5')
    response = api.request('/me', args={'fields': 'email'})
    return response['email']


@app.template_filter('md')
def convert_markdown(value):
    return markdown(value)


@app.template_filter('humantime')
def humanize_time(value):
    return format_datetime(value, format='long')


@login_failed.connect_via(app)
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

    role_query = mdl.DB.session.query(mdl.Role).filter_by(name='authenticated')
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
    return redirect(url_for('profile'))


def userbool(value):
    return value.lower()[0:1] in ('t', '1')


@babel.localeselector
def get_locale():
    locale = flask_session.get('lang', 'lu')
    app.logger.debug('Using locale {}'.format(locale))
    return locale


@app.context_processor
def inject_context():
    registration_open = mdl.Setting.get('registration_open', default=False)
    event_date = mdl.Setting.get('event_date', None)
    location_display = mdl.Setting.get('event_location', '')
    coords = mdl.Setting.get('location_coords', '')
    if event_date and event_date >= datetime.now().date():
        date_locale = get_locale()
        if date_locale == 'lu':  # bugfix?
            date_locale = 'de'
        date_display = format_date(event_date,
                                   format='long',
                                   locale=date_locale)
    else:
        date_display = ''
        location_display = ''
        coords = ''

    return dict(
        Role=mdl.Role,
        Setting=mdl.Setting,
        __version__=__version__,
        date_display=date_display,
        localconf=app.localconf,
        location_coords=coords,
        location_display=location_display,
        registration_open=registration_open,
        tabular_prefix=TABULAR_PREFIX,
    )


@app.errorhandler(NoResultFound)
def error_handler(request):
    return gettext('No such entity!'), 404


@app.before_first_request
def create_admin_user():
    user = user_datastore.create_user(
        email='admin@example.com',
        password='admin',
        active=True)
    admin_role = mdl.Role(name=mdl.Role.ADMIN)
    user.roles = [admin_role]
    try:
        mdl.DB.session.commit()
    except Exception as exc:
        app.logger.debug(str(exc))
        mdl.DB.session.rollback()


@app.before_request
def before_request():
    # Only set this if the argument is present (which means the user wants to
    # change the language)
    if 'lang' in request.args:
        app.logger.debug('Changing locale to {}'.format(request.args['lang']))
        flask_session['lang'] = request.args['lang']


@app.teardown_request
def teardown_request(exc):
    try:
        mdl.DB.session.commit()
    except Exception:
        mdl.DB.session.rollback()
        app.logger.exception(exc)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/where')
def where():
    return render_template('where.html')


@app.route('/misc')
def misc():
    return render_template('misc.html')


@app.route('/matrix')
def matrix():
    stations = mdl.Station.all()
    groups = mdl.Group.all()
    state_matrix = loco.Matrix(stations, groups)
    return render_template('matrix.html',
                           matrix=state_matrix,
                           stations=stations)


@app.route('/advance/<groupId>/<station_id>')
@login_required
def advance(groupId, station_id):
    new_state = mdl.advance(mdl.DB.session, groupId, station_id)
    return jsonify(
        group_id=groupId,
        station_id=station_id,
        new_state=new_state)


@app.route('/scoreboard')
def scoreboard():
    result = sorted(mdl.score_totals(), key=attrgetter('score_sum'),
                    reverse=True)
    output = []
    pos = 1
    for row in result:
        group = mdl.Group.one(id=row.group_id)
        output.append([pos, group.name, row.score_sum, group.completed])
        pos += 1
    return render_template('scoreboard.html', scores=output)


@app.route('/slot_editor')
@roles_accepted(mdl.Role.ADMIN)
def slot_editor():
    groups = mdl.Group.all()
    slots = mdl.TimeSlot.all()

    groups_a = {}
    groups_b = {}
    for group in groups:
        try:
            if group.start_time and group.direction == mdl.DIR_A:
                groups_a[mdl.TimeSlot(group.start_time)] = group
            elif group.start_time and group.direction == mdl.DIR_B:
                groups_b[mdl.TimeSlot(group.start_time)] = group
        except ValueError as exc:
            app.logger.warning(exc)
            group.start_time = None

    groups_none = sorted([_ for _ in groups
                          if not _.start_time or _.direction not in (
                              mdl.DIR_A, mdl.DIR_B)],
                         key=lambda x: x.name)

    return render_template('slot_editor.html',
                           slots=slots,
                           dir_a=mdl.DIR_A,
                           dir_b=mdl.DIR_B,
                           groups_a=groups_a,
                           groups_b=groups_b,
                           groups_none=groups_none,
                           stats=loco.stats())


@app.route('/js-fragment/group-tooltip/<int:group_id>')
def group_tooltip(group_id):
    group = mdl.Group.one(id=group_id)
    return render_template('group-tooltip.html',
                           group=group)


@app.route('/station/<int:id>', methods=['DELETE'])
@roles_accepted(mdl.Role.ADMIN)
def delete_station(id):
    loco.delete_station(id)
    return jsonify(status='ok')


@app.route('/settings')
@roles_accepted(mdl.Role.ADMIN)
def settings():
    settings = {stng.key: stng.value
                for stng in mdl.Setting.all(mdl.DB.session)}
    return render_template('settings.html', settings=settings)


@app.route('/settings', methods=['POST'])
@login_required
def save_settings():
    helpdesk = request.form.get('helpdesk', '')
    registration_open = request.form.get('registration_open', '') == 'on'
    shout = request.form.get('shout', '')
    event_date = request.form.get('event_date', '')
    event_location = request.form.get('event_location', '')
    location_coords = request.form.get('location_coords', '')

    mdl.Setting.put(mdl.DB.session, 'helpdesk', helpdesk)
    mdl.Setting.put(mdl.DB.session, 'registration_open', registration_open)
    mdl.Setting.put(mdl.DB.session, 'shout', shout)
    mdl.Setting.put(mdl.DB.session, 'event_date', event_date)
    mdl.Setting.put(mdl.DB.session, 'event_location', event_location)
    mdl.Setting.put(mdl.DB.session, 'location_coords', location_coords)
    flash(gettext('Settings successfully saved.'), 'info')
    return redirect(url_for("settings"))


@app.route('/group_state/<group>/<station>', methods=['PUT'])
@http_auth_required('lostlu')
def update_group_station_state(group, station):
    """
    Required by the android client.
    """
    group = unquote_plus(group)
    station = unquote_plus(station)
    try:
        form_score = request.json['form']
        station_score = request.json['station']
        station_state = request.json['state']
    except LookupError:
        return jsonify({'message': 'Missing value'}), 400

    loco.set_score(mdl.DB.session, group, station, station_score, form_score,
                   station_state)

    return jsonify(
        name=group,
        form_score=form_score,
        score=station_score,
        state=station_state,
        station_name=station)


@app.route('/profile', methods=['GET', 'DELETE'])
@login_required
def profile():
    return render_template(
        'profile.html',
        content='Profile Page',
        twitter_conn=social.twitter.get_connection() if social.twitter else None,  # NOQA
        facebook_conn=social.facebook.get_connection() if social.facebook else None,  # NOQA
        google_conn=social.google.get_connection() if social.google else None)


if __name__ == '__main__':
    DEBUG = userbool(app.localconf.get('devserver', 'debug',
                                       default=False))
    if DEBUG:
        app.mailer = DummyMailer()
    else:
        app.mailer = Mailer()
    app.run(debug=DEBUG,
            host=app.localconf.get('devserver', 'listen'),
            port=int(app.localconf.get('devserver', 'port')))
