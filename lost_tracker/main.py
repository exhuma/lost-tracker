from collections import namedtuple
from datetime import datetime
from operator import attrgetter
import io
import mimetypes
import os.path

from sqlalchemy import Unicode, Integer
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
from sqlalchemy import create_engine, and_, or_
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
from PIL import Image

from lost_tracker import __version__
from lost_tracker.flickr import get_photos
from lost_tracker.database import Base
from lost_tracker.localtypes import Photo
from sqlalchemy.exc import IntegrityError
import lost_tracker.core as loco
import lost_tracker.models as mdl

mimetypes.init()
app = Flask(__name__)
app.localconf = Config('mamerwiselen', 'lost-tracker',
                       version='1.2', require_load=True)
app.secret_key='\xd8\xb1ZD\xa2\xf9j%\x0b\xbf\x11\x18\xe0$E\xa4]\xf0\x03\x7fO9\xb0\xb5'  # NOQA

babel = Babel(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# This is intentionally not in the config. It's tightly bound to the code. And
# adding a table without modifying the rest of the code would not make sense.
MODIFIABLE_TABLES = ('group', 'station', 'form')


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
        localconf=app.localconf,
        registration_open=registration_open,
        Setting=mdl.Setting,
        date_display=date_display,
        __version__=__version__)


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


@app.route('/matrix')
def matrix():
    stations = loco.get_stations()
    groups = loco.get_grps()

    state_matrix = loco.get_matrix(stations, groups)
    sums = loco.get_state_sum(state_matrix)

    return render_template('matrix.html',
                           matrix=state_matrix,
                           stations=stations,
                           sums=sums)


@app.route('/advance/<groupId>/<station_id>')
@login_required
def advance(groupId, station_id):
    new_state = mdl.advance(g.session, groupId, station_id)
    return jsonify(
        group_id=groupId,
        station_id=station_id,
        new_state=new_state)


@app.route('/station/<path:name>')
@login_required
def station(name):
    station = loco.get_stat_by_name(name)  # TODO: rename function
    if not station:
        return abort(404)

    groups = loco.get_grps()  # TODO: rename function
    GroupStateRow = namedtuple('GroupStateRow', 'group, state')
    group_states = []
    for grp in groups:  # TODO: rename variable
        group_station = mdl.get_state(grp.id, station.id)
        if not group_station:
            state = None
        else:
            state = group_station
        group_states.append(
            GroupStateRow(grp, state))
    group_states.sort(key=_stategetter)

    questionnaires = loco.get_forms()

    return render_template(
        'station.html',
        station=station,
        groups=groups,
        group_states=group_states,
        questionnaires=questionnaires,
        disable_logo=True)


@app.route('/scoreboard')
def scoreboard():
    result = sorted(mdl.score_totals(), key=attrgetter('score_sum'),
                    reverse=True)
    output = []
    pos = 1
    for row in result:
        group = loco.get_grps_by_id(row.group_id)
        output.append([pos, group.name, row.score_sum, group.completed])
        pos += 1
    return render_template('scoreboard.html', scores=output)


@app.route('/group/<int:group_id>/score/<int:station_id>', methods=['PUT'])
def set_group_score(group_id, station_id):
    try:
        form_score = request.json['form']
        station_score = request.json['station']
    except LookupError:
        return jsonify({'message': 'Missing value'}), 400
    loco.set_score(g.session, group_id, station_id, station_score, form_score)
    return jsonify({
        'form_score': form_score,
        'station_score': station_score
    })


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
    group = loco.get_grp_by_registration_key(key)

    if group.finalized:
        flash(gettext('This group has already been accepted!'), 'info')

    return render_template('edit_group.html',
                           group=group,
                           dir_a=mdl.DIR_A,
                           dir_b=mdl.DIR_B)


@app.route('/group/<id>', methods=['POST'])
@login_required
def save_group_info(id):
    if current_user.is_anonymous() or not current_user.admin:
        return "Access denied", 401
    group = loco.get_grps_by_id(id)
    if not group.finalized:
        loco.accept_registration(group.confirmation_key, request.form)
        flash(gettext('Accepted registration for group {}').format(group.name),
              'info')
        return redirect(url_for('index'))
    else:
        loco.update_group(id,
                          request.form,
                          request.form['send_email'] == 'true')
        flash(gettext('Group {name} successfully updated!').format(
            name=request.form['name']), 'info')
        if request.form['send_email'] == 'true':
            flash(gettext('E-Mail sent successfully!'), 'info')
            return redirect(url_for('tabularadmin', table='group'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        authed = loco.auth(request.form['login'], request.form['password'])
        user = loco.get_user(request.form['login'])
        if authed:
            login_user(user, remember=True)
            flash(gettext('Logged in successfully'), 'info')
            return redirect(request.values.get('next') or url_for('index'))
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


@app.route('/manage')
@login_required
def manage():
    if current_user.is_anonymous() or not current_user.admin:
        return "Access denied", 401
    groups = loco.get_grps()
    slots = loco.slots()

    groups_a = {mdl.TimeSlot(_.start_time): _ for _ in groups
                if _.start_time and _.direction == mdl.DIR_A}
    groups_b = {mdl.TimeSlot(_.start_time): _ for _ in groups
                if _.start_time and _.direction == mdl.DIR_B}
    groups_none = sorted([_ for _ in groups
                          if not _.start_time or _.direction not in (
                              mdl.DIR_A, mdl.DIR_B)],
                         key=lambda x: x.name)

    return render_template('manage.html',
                           slots=slots,
                           dir_a=mdl.DIR_A,
                           dir_b=mdl.DIR_B,
                           groups_a=groups_a,
                           groups_b=groups_b,
                           groups_none=groups_none,
                           stats=loco.stats())


@app.route('/manage/table/<table>')
@login_required
def tabularadmin(table):
    if current_user.is_anonymous() or not current_user.admin:
        return "Access denied", 401

    if table not in MODIFIABLE_TABLES:
        return gettext('Access Denied'), 401

    custom_order = None
    if 'order' in request.args:
        custom_order = request.args['order']

    if table == 'group':
        columns = [_ for _ in mdl.Group.__table__.columns
                   if _.name not in ('id', 'confirmation_key')]
        keys = [_ for _ in mdl.Group.__table__.columns if _.primary_key]
        data = g.session.query(mdl.Group)
        if custom_order and custom_order in mdl.Group.__table__.columns:
            data = data.order_by(mdl.Group.__table__.columns[custom_order])
        else:
            data = data.order_by(mdl.Group.cancelled, mdl.Group.order)
    elif table == 'station':
        columns = [_ for _ in mdl.Station.__table__.columns
                   if _.name not in ('id', 'confirmation_key')]
        keys = [_ for _ in mdl.Station.__table__.columns if _.primary_key]
        data = g.session.query(mdl.Station)
        if custom_order and custom_order in mdl.Station.__table__.columns:
            data = data.order_by(mdl.Station.__table__.columns[custom_order])
        else:
            data = data.order_by(mdl.Station.order)
    elif table == 'form':
        columns = [_ for _ in mdl.Form.__table__.columns
                   if _.name not in ('id', 'confirmation_key')]
        keys = [_ for _ in mdl.Form.__table__.columns if _.primary_key]
        data = g.session.query(mdl.Form)
        if custom_order and custom_order in mdl.Form.__table__.columns:
            data = data.order_by(mdl.Form.__table__.columns[custom_order])
        else:
            data = data.order_by(mdl.Form.order, mdl.Form.name)
    else:
        return gettext('Table {name} not yet supported!').format(
            name=table), 400

    # prepare data for the template
    Row = namedtuple('Row', 'key, data')
    Column = namedtuple('Column', 'name, type, value')
    rows = []
    for row in data:
        pk = {_.name: getattr(row, _.name) for _ in keys}
        rowdata = [Column(_.name,
                          _.type.__class__.__name__.lower(),
                          getattr(row, _.name)) for _ in columns]
        rows.append(Row(pk, rowdata))

    return render_template('tabular.html',
                           clsname=table,
                           columns=columns,
                           data=rows)


@app.route('/cell/<cls>/<key>/<datum>', methods=['PUT'])
@login_required
def update_cell_value(cls, key, datum):
    if current_user.is_anonymous() or not current_user.admin:
        return "Access denied", 401

    if cls not in MODIFIABLE_TABLES:
        return gettext('Access Denied'), 401

    data = request.json
    table = mdl.Base.metadata.tables[cls]

    if table.columns[datum].type.__class__ == Unicode:
        coerce_ = unicode.strip
    elif table.columns[datum].type.__class__ == Integer:
        coerce_ = int
    else:
        coerce_ = lambda x: x  # NOQA

    if data['oldValue'] in ('', None) and coerce_ == unicode.strip:
        cell_predicate = or_(table.c[datum] == '',
                             table.c[datum] == None)  # NOQA
    elif data['oldValue'] in ('', None):
        cell_predicate = table.c[datum] == None  # NOQA
    else:
        cell_predicate = table.c[datum] == data['oldValue']

    data['newValue'] = coerce_(data['newValue'])
    query = table.update().values(**{datum: data['newValue']}).where(
        and_(table.c.id == key, cell_predicate))

    try:
        result = g.session.execute(query)
    except Exception as exc:
        app.logger.debug(exc)
        return jsonify(message='Invalid data'), 400

    if result.rowcount == 1:
        return jsonify(success=True, new_value=data['newValue'])
    else:
        current_entity = g.session.query(table).filter_by(id=key).one()
        # If the DB value is already the same as the one we try to put, we can
        # assume it's a success.
        if getattr(current_entity, datum) == data['newValue']:
            return jsonify(success=True, new_value=data['newValue'])
        return jsonify(db_value=getattr(current_entity, datum)), 409


@app.route('/group/<group_name>/timeslot', methods=['PUT'])
@login_required
def set_time_slot(group_name):
    if current_user.is_anonymous() or not current_user.admin:
        return "Access denied", 401
    data = request.json
    if data['direction'] not in (mdl.DIR_A, mdl.DIR_B):
        return jsonify(
            message=gettext('Incorrect value for direction: {!r}').format(
                data['direction'])), 400
    group = loco.get_grp_by_name(group_name)
    if not group:
        group = mdl.Group(name=group_name, start_time=data['new_slot'])
        g.session.add(group)
    group.start_time = data['new_slot']
    group.direction = data['direction']
    return '{{"is_success": true, "group_id": {}}}'.format(group.id)


@app.route('/js-fragment/group-tooltip/<int:group_id>')
def group_tooltip(group_id):
    group = loco.get_grps_by_id(group_id)
    return render_template('group-tooltip.html',
                           group=group)


@app.route('/group', methods=['POST'])
@login_required
def add_new_group():
    if current_user.is_anonymous() or not current_user.admin:
        return "Access denied", 401
    data = request.json
    grp_name = data['name']
    grp_contact = data['contact']
    grp_tel = data['phone']
    grp_direction = data['direction']
    grp_start = data['start_time']

    message = loco.add_grp(
        grp_name,
        grp_contact,
        grp_tel,
        grp_direction,
        grp_start,
        g.session)
    return jsonify(message=message)


@app.route('/group/<int:id>', methods=['DELETE'])
@login_required
def delete_group(id):
    if current_user.is_anonymous() or not current_user.admin:
        return "Access denied", 401
    loco.delete_group(id)
    return jsonify(status='ok')


@app.route('/station/<int:id>', methods=['DELETE'])
@login_required
def delete_station(id):
    if current_user.is_anonymous() or not current_user.admin:
        return "Access denied", 401
    loco.delete_station(id)
    return jsonify(status='ok')


@app.route('/form/<int:id>', methods=['DELETE'])
@login_required
def delete_form(id):
    if current_user.is_anonymous() or not current_user.admin:
        return "Access denied", 401
    loco.delete_form(id)
    return jsonify(status='ok')


@app.route('/group_list')
@login_required
def group_list():
    groups = loco.get_grps()
    groups = groups.order_by(None)
    groups = groups.order_by(mdl.Group.inserted)
    return render_template('group_list.html', groups=groups)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/where')
def where():
    return render_template('where.html')


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


@app.route('/misc')
def misc():
    return render_template('misc.html')


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


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=userbool(app.localconf.get('devserver', 'debug',
                                             default=False)),
            host=app.localconf.get('devserver', 'listen'),
            port=int(app.localconf.get('devserver', 'port')))
