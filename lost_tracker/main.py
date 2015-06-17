from datetime import datetime
from operator import attrgetter
from urllib import unquote_plus

from sqlalchemy.orm.exc import NoResultFound

from config_resolver import Config
from flask.ext.login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask.ext.babel import gettext, Babel
from babel.dates import format_date
from sqlalchemy import create_engine
from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session as flask_session,
    url_for,
)
from sqlalchemy.exc import IntegrityError

from lost_tracker import __version__
from lost_tracker.blueprint.group import GROUP
from lost_tracker.blueprint.photo import PHOTO
from lost_tracker.blueprint.registration import REGISTRATION
from lost_tracker.blueprint.station import STATION
from lost_tracker.blueprint.tabedit import TABULAR
from lost_tracker.database import Base
from lost_tracker.util import basic_auth
import lost_tracker.core as loco
import lost_tracker.models as mdl

# URL prefixes (needed in multiple locations for JS. Therefore in a variable)
TABULAR_PREFIX = '/manage'
GROUP_PREFIX = '/group'
STATION_PREFIX = '/station'
PHOTO_PREFIX = '/photo'
REGISTRATION_PREFIX = '/registration'

app = Flask(__name__)
app.localconf = Config('mamerwiselen', 'lost-tracker',
                       version='2.0', require_load=True)
app.secret_key = app.localconf.get('app', 'secret_key')
app.register_blueprint(GROUP, url_prefix=GROUP_PREFIX)
app.register_blueprint(PHOTO, url_prefix=PHOTO_PREFIX)
app.register_blueprint(REGISTRATION, url_prefix=REGISTRATION_PREFIX)
app.register_blueprint(STATION, url_prefix=STATION_PREFIX)
app.register_blueprint(TABULAR, url_prefix=TABULAR_PREFIX)

babel = Babel(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


def userbool(value):
    return value.lower()[0:1] in ('t', '1')


@babel.localeselector
def get_locale():
    locale = flask_session.get('lang', 'lu')
    app.logger.debug('Using locale {}'.format(locale))
    return locale


@login_manager.user_loader
def load_user(userid):
    return loco.get_user(userid)


@app.context_processor
def inject_context():
    registration_open = mdl.Setting.get(g.session, 'registration_open',
                                        default=False)
    event_date = mdl.Setting.get(g.session, 'event_date', None)
    if event_date and event_date >= datetime.now():
        date_locale = get_locale()
        if date_locale == 'lu':  # bugfix?
            date_locale = 'de'
        date_display = format_date(event_date,
                                   format='long',
                                   locale=date_locale)
    else:
        date_display = ''

    return dict(
        Setting=mdl.Setting,
        __version__=__version__,
        date_display=date_display,
        localconf=app.localconf,
        registration_open=registration_open,
        tabular_prefix=TABULAR_PREFIX,
    )


@app.before_first_request
def bind_metadata():
    Base.metadata.bind = create_engine(app.localconf.get('db', 'dsn'))


@app.errorhandler(NoResultFound)
def error_handler(request):
    return gettext('No such entity!'), 404


@app.before_request
def before_request():
    # This import is deferred as it triggers the DB engine constructor on
    # first import! As it may not yet be configured at global import time this
    # would fail if imported globally.
    from lost_tracker.database import db_session as session

    # Only set this if the argument is present (which means the user wants to
    # change the language)
    if 'lang' in request.args:
        app.logger.debug('Changing locale to {}'.format(request.args['lang']))
        flask_session['lang'] = request.args['lang']

    g.session = session


@app.teardown_request
def teardown_request(exc):
    try:
        g.session.commit()
    except IntegrityError:
        g.session.rollback()
        app.logger.exception(exc)


@app.route('/')
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
    new_state = mdl.advance(g.session, groupId, station_id)
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


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        authed = loco.auth(request.form['login'], request.form['password'])
        user = loco.get_user(request.form['login'])
        if authed:
            login_user(user, remember=True)
            flash(gettext('Logged in successfully'), 'info')
            return redirect(request.values.get('next') or url_for('matrix'))
        else:
            flash(gettext('Invalid credentials!'), 'error')
            return render_template('login.html')
    else:
        return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('matrix'))


@app.route('/slot_editor')
@login_required
def slot_editor():
    if current_user.is_anonymous() or not current_user.admin:
        return "Access denied", 401
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
@login_required
def delete_station(id):
    if current_user.is_anonymous() or not current_user.admin:
        return "Access denied", 401
    loco.delete_station(id)
    return jsonify(status='ok')


@app.route('/settings')
@login_required
def settings():
    settings = {stng.key: stng.value for stng in mdl.Setting.all(g.session)}
    if 'event_date' in settings and settings['event_date']:
        settings['event_date'] = settings['event_date'].strftime(
            mdl.DATE_FORMAT)
    return render_template('settings.html', settings=settings)


@app.route('/settings', methods=['POST'])
@login_required
def save_settings():
    helpdesk = request.form.get('helpdesk', '')
    registration_open = request.form.get('registration_open', '') == u'on'
    shout = request.form.get('shout', '')
    event_date = request.form.get('event_date', '')
    if event_date:
        event_date = datetime.strptime(event_date, '%Y-%m-%d')
    mdl.Setting.put(g.session, 'helpdesk', helpdesk)
    mdl.Setting.put(g.session, 'registration_open', registration_open)
    mdl.Setting.put(g.session, 'shout', shout)
    mdl.Setting.put(g.session, 'event_date', event_date)
    flash(gettext('Settings successfully saved.'), 'info')
    return redirect(url_for("settings"))


@app.route('/group_state/<group>/<station>', methods=['PUT'])
@basic_auth
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

    loco.set_score(g.session, group, station, station_score, form_score,
                   station_state)

    return jsonify(
        name=group,
        form_score=form_score,
        score=station_score,
        state=station_state,
        station_name=station)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=userbool(app.localconf.get('devserver', 'debug',
                                             default=False)),
            host=app.localconf.get('devserver', 'listen'),
            port=int(app.localconf.get('devserver', 'port')))
