from collections import namedtuple
from datetime import datetime
from json import dumps
from operator import attrgetter
from urllib import unquote_plus
import io
import mimetypes
import os.path

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
    abort,
    flash,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session as flask_session,
    url_for,
)
from PIL import Image, ExifTags
from sqlalchemy.exc import IntegrityError

from lost_tracker import __version__
from lost_tracker.blueprint.group import GROUP
from lost_tracker.blueprint.tabedit import TABULAR
from lost_tracker.database import Base
from lost_tracker.flickr import get_photos
from lost_tracker.localtypes import Photo, json_encoder
from lost_tracker.util import basic_auth
import lost_tracker.core as loco
import lost_tracker.models as mdl

# URL prefixes (needed in multiple locations for JS. Therefore in a variable)
TABULAR_PREFIX = '/manage'
GROUP_PREFIX = '/group'

mimetypes.init()
app = Flask(__name__)
app.localconf = Config('mamerwiselen', 'lost-tracker',
                       version='2.0', require_load=True)
app.secret_key = app.localconf.get('app', 'secret_key')
app.register_blueprint(TABULAR, url_prefix=TABULAR_PREFIX)
app.register_blueprint(GROUP, url_prefix=GROUP_PREFIX)

babel = Babel(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


def userbool(value):
    return value.lower()[0:1] in ('t', '1')


def photo_url_generator(basename):
    return Photo(url_for('thumbnail', basename=basename),
                 url_for('photo', basename=basename))


def _stategetter(element):
    """
    Custom sorting for group states. Make "arrived" groups come first,
    then all "unknowns". Make "finished" and "cancelled" groups come last.
    """
    if element is None or element.state is None:
        return 1
    elif element.group.cancelled:
        return 80
    elif element.state.state == mdl.STATE_ARRIVED:
        return 0
    elif element.state.state == mdl.STATE_UNKNOWN:
        return 1
    elif element.state.state == mdl.STATE_FINISHED:
        return 2
    else:
        return 99


@app.route('/photo/<basename>')
def photo(basename):
    basename = os.path.basename(basename)
    root = app.localconf.get('app', 'photo_folder', default='')
    if not root:
        return

    fullname = os.path.join(root, basename)
    mimetype, _ = mimetypes.guess_type(fullname)
    with open(fullname, 'rb') as fptr:
        response = make_response(fptr.read())
    response.headers['Content-Type'] = mimetype
    return response


@app.route('/thumbnail/<basename>')
def thumbnail(basename):
    basename = os.path.basename(basename)
    root = app.localconf.get('app', 'photo_folder', default='')
    if not root:
        return

    fullname = os.path.join(root, basename)
    mimetype, _ = mimetypes.guess_type(fullname)

    im = Image.open(fullname)

    exif_orientation_id = None
    for tag in ExifTags.TAGS:
        if ExifTags.TAGS[tag] == 'Orientation':
            exif_orientation_id = tag
            break

    orientation = None
    if hasattr(im, '_getexif'):
        exif = im._getexif()
        if exif:
            orientation = exif.get(exif_orientation_id)

    if orientation == 3:
        im = im.rotate(180, expand=True)
    elif orientation == 6:
        im = im.rotate(270, expand=True)
    elif orientation == 8:
        im = im.rotate(90, expand=True)

    im.thumbnail((150, 150), Image.ANTIALIAS)
    blob = io.BytesIO()
    im.save(blob, 'jpeg')

    response = make_response(blob.getvalue())
    response.headers['Content-Type'] = mimetype
    return response


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


@app.route('/station/<path:name>')
def station(name):
    station = mdl.Station.one(name=name)
    if not station:
        return abort(404)

    groups = mdl.Group.all()
    GroupStateRow = namedtuple('GroupStateRow', 'group, state')
    group_states = []
    for group in groups:
        group_station = mdl.GroupStation.get(group.id, station.id)
        if not group_station:
            state = None
        else:
            state = group_station
        group_states.append(
            GroupStateRow(group, state))
    group_states.sort(key=_stategetter)

    questionnaires = mdl.Form.all()

    output = dict(
        station=station,
        groups=groups,
        group_states=group_states,
        questionnaires=questionnaires,
        disable_logo=True)

    if 'application/json' in request.headers['Accept']:
        response = make_response(dumps(output, default=json_encoder))
        response.content_type = 'application/json'
        return response
    else:
        return render_template(
            'station.html',
            **output)


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


@app.route('/register', methods=['GET', 'POST'])
def register():
    is_open = mdl.Setting.get(g.session, 'registration_open', default=False)
    if not is_open:
        return render_template('registration_closed.html')

    if request.method == 'POST':
        data = {
            "group_name": request.form.get('group_name'),
            "contact_name": request.form.get('contact_name'),
            "email": request.form.get('email'),
            "tel": request.form.get('tel'),
            "time": request.form.get('time'),
            "comments": request.form.get('comments'),
        }
        confirmation_link = url_for('confirm_registration',
                                    _external=True)
        try:
            loco.store_registration(g.session, data, confirmation_link)
        except ValueError as exc:
            return 'Error: ' + str(exc), 400
        return render_template(
            'notice.html',
            message=gettext(
                'The registration has been recorded. However it is not yet '
                'activated.  You will receive a confirmation e-mail any '
                'second now. You must click on the link in that e-mail to '
                'activate the registrtion! Once this step is done, the '
                'registration will be processed by the lost team, and you '
                'will receive another e-mail with the final confirmation once '
                'that is done.'))

    return render_template('register.html', stats=loco.stats())


@app.route('/confirm')
@app.route('/confirm/<key>')
def confirm_registration(key):
    is_open = mdl.Setting.get(g.session, 'registration_open', default=False)
    if not is_open:
        return "Access denied", 401

    loco.confirm_registration(
        key,
        activation_url=url_for('accept_registration',
                               key=key,
                               _external=True))
    return render_template('notice.html', message=gettext(
        'Thank you. Your registration has been activated and the lost-team '
        'has been notified about your entry. Once everything is processed you '
        'will recieve another e-mail with the final details.'))


@app.route('/accept/<key>')
@login_required
def accept_registration(key):
    if current_user.is_anonymous() or not current_user.admin:
        return "Access denied", 401
    group = mdl.Group.one(key=key)

    if group.finalized:
        flash(gettext('This group has already been accepted!'), 'info')

    return render_template('edit_group.html',
                           group=group,
                           dir_a=mdl.DIR_A,
                           dir_b=mdl.DIR_B)


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


@app.route('/gallery')
def photo_gallery():
    galleries = []

    local_data = loco.get_local_photos(app.localconf, photo_url_generator)
    if local_data:
        galleries.append(local_data)

    flickr_data = get_photos(app.localconf)
    if flickr_data:
        galleries.append(flickr_data)

    return render_template('gallery.html', galleries=galleries)


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
