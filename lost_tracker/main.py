from collections import namedtuple
from operator import attrgetter

from config_resolver import Config
from flask.ext.login import (
    LoginManager,
    login_required,
    login_user,
    logout_user,
)
from sqlalchemy import create_engine, and_, or_
from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from lost_tracker import __version__
from lost_tracker.database import Base
from sqlalchemy.exc import IntegrityError
import lost_tracker.core as loco
import lost_tracker.models as mdl

app = Flask(__name__)
app.localconf = Config('mamerwiselen', 'lost-tracker',
                       version='1.0', require_load=True)
app.secret_key='\xd8\xb1ZD\xa2\xf9j%\x0b\xbf\x11\x18\xe0$E\xa4]\xf0\x03\x7fO9\xb0\xb5'  # NOQA

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# This is intentionally not in the config. It's tightly bound to the code. And
# adding a table without modifying the rest of the code would not make sense.
MODIFIABLE_TABLES = ('group', 'station', 'form')


@login_manager.user_loader
def load_user(userid):
    return loco.get_user(userid)


@app.context_processor
def inject_context():
    return dict(
        localconf=app.localconf,
        __version__=__version__)


@app.before_first_request
def bind_metadata():
    Base.metadata.bind = create_engine(app.localconf.get('db', 'dsn'))


@app.before_request
def before_request():
    # This import is deferred as it triggers the DB engine constructor on
    # first import! As it may not yet be configured at global import time this
    # would fail if imported globally.
    from lost_tracker.database import db_session as session
    g.session = session


@app.teardown_request
def teardown_request(exc):
    try:
        g.session.commit()
    except IntegrityError:
        g.session.rollback()
        app.logger.exception(exc)


@app.route('/')
def index():
    stations = loco.get_stations()
    groups = loco.get_grps()

    state_matrix = loco.get_matrix(stations, groups)
    sums = loco.get_state_sum(state_matrix)

    return render_template('matrix.html',
                           matrix=state_matrix,
                           stations=stations,
                           sums=sums)


@app.route('/advance/<groupId>/<station_id>')
def advance(groupId, station_id):
    new_state = mdl.advance(g.session, groupId, station_id)
    return jsonify(
        group_id=groupId,
        station_id=station_id,
        new_state=new_state)


@app.route('/station/<path:name>')
def station(name):
    station = loco.get_stat_by_name(name)
    if not station:
        return abort(404)

    def stategetter(element):
        """
        Custom sorting for group states. Make "arrived" groups come first,
        then all "unknowns". Make "finished" groups come last.
        """
        if element is None or element.state is None:
            return mdl.STATE_UNKNOWN
        elif element.state.state == mdl.STATE_ARRIVED:
            return 0
        elif element.state.state == mdl.STATE_UNKNOWN:
            return 1
        elif element.state.state == mdl.STATE_FINISHED:
            return 2
        else:
            return 99

    groups = loco.get_grps()
    GroupStateRow = namedtuple('GroupStateRow',
                               'group, '
                               'state')
    group_states = []
    for grp in groups:
        group_station = mdl.get_state(grp.id, station.id)
        if not group_station:
            state = None
        else:
            state = group_station
        group_states.append(
            GroupStateRow(grp, state))
    group_states.sort(key=stategetter)

    questionnaires = loco.get_forms()

    return render_template(
        'station.html',
        station=station,
        groups=groups,
        group_states=group_states,
        questionnaires=questionnaires)


@app.route('/group')
def init_grp_form():
    message = ""
    grps = loco.get_grps()
    return render_template('add_group.html',
                           message=message,
                           groups=grps,
                           DIR_A=mdl.DIR_A,
                           DIR_B=mdl.DIR_B)


@app.route('/group', methods=['POST'])
def grp_form():
    grp_name = request.form['grp_name']
    grp_contact = request.form['grp_contact']
    grp_tel = request.form['grp_tel']
    grp_direction = request.form['grp_direction']
    grp_start = request.form['grp_start']

    try:
        message = loco.add_grp(
            grp_name,
            grp_contact,
            grp_tel,
            grp_direction,
            grp_start,
            g.session)
        flash(message, 'info')
    except ValueError as exc:
        message = exc
        flash(message, 'error')

    return redirect(url_for("init_grp_form"))


@app.route('/add_station')
def init_stat_form():
    message = ""
    return render_template('add_station.html', message=message)


@app.route('/add_station', methods=['POST'])
def stat_form():
    name = request.form['stat_name']
    contact = request.form['stat_contact']
    phone = request.form['stat_phone']

    message = loco.add_station(name, contact, phone, g.session)
    flash(message, 'info')
    return redirect(url_for("init_stat_form"))


@app.route('/form_score')
def init_form_score():
    grps = loco.get_grps()
    form_scores = mdl.get_form_score_full()
    return render_template(
        'form_score.html',
        form_scores=form_scores,
        groups=grps)


@app.route('/score/<int:group_id>/<int:form_id>')
def group_form_score(group_id, form_id):
    return jsonify(
        score=mdl.get_form_score(group_id, form_id))


@app.route('/score/<int:group_id>', methods=['POST'])
def score(group_id):
    station_id = int(request.form['station_id'])

    try:
        station_score = int(request.form['station_score'])
    except ValueError as exc:
        app.logger.exception(exc)
        station_score = None

    try:
        form_id = int(request.form['form_id'])
        form_score = int(request.form['form_score'])
    except:
        form_id = None
        form_score = 0

    if station_score is not None:
        group_station = mdl.GroupStation.get(
            group_id,
            station_id)
        if not group_station:
            group_station = mdl.GroupStation(
                group_id,
                station_id)
            g.session.add(group_station)
        group_station.score = int(station_score)

    if form_id is not None:
        mdl.set_form_score(group_id, form_id, int(form_score))

    if request.is_xhr:
        return jsonify(
            station_score=station_score,
            form_score=form_score,
            status='ok')

    return redirect(url_for("/"))  # TODO: redirect to station page


@app.route('/station_score', methods=['POST'])
def set_station_score():
    group_id = request.form['group_id']
    station_id = request.form['station_id']
    score = request.form['score']

    if group_id:
        mdl.GroupStation.set_score(group_id, station_id, score)

    if request.is_xhr:
        return jsonify(status='ok')

    return redirect(url_for("/"))  # TODO: redirect to station page


@app.route('/form_score', methods=['POST'])
def form_score():
    """
    Saves the score for one questionnaire into the database.  It takes the
    following POST parameters:

    :param group_id: The group ID
    :param form_id: The form/questionnaire ID
    :param score: The score.
    """

    try:
        group_id = int(request.form['group_id'])
        form_id = int(request.form['form_id'])
        score = int(request.form['score'])
    except ValueError as exc:
        abort(409, str(exc))

    if group_id:
        mdl.set_form_score(group_id, form_id, score)

    if request.is_xhr:
        return jsonify(status='ok')

    return redirect(url_for("init_form_score"))


@app.route('/add_form')
@login_required
def init_add_form():
    message = ""
    forms = loco.get_forms()
    return render_template('add_form.html', message=message, forms=forms)


@app.route('/add_form', methods=['POST'])
@login_required
def add_form():
    form_id = int(request.form['form_id'])
    name = request.form['name']
    max_score = int(request.form['max_score'])
    message = loco.add_form_db(form_id, name, max_score, g.session)
    flash(message, 'info')
    return redirect(url_for("init_add_form"))


@app.route('/scoreboard')
def scoreboard():
    result = sorted(mdl.score_totals(), key=attrgetter('score_sum'),
                    reverse=True)
    output = []
    pos = 1
    for row in result:
        group = loco.get_grps_by_id(row.group_id)
        output.append([pos, group.name, row.score_sum])
        pos+=1
    return render_template('scoreboard.html', scores=output)


@app.route('/guide')
def guide():
    return render_template('guide.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
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
        return "Thank you!"  # TODO!!

    return render_template('register.html')


@app.route('/confirm')
@app.route('/confirm/<key>')
def confirm_registration(key):
    status = loco.confirm_registration(
        key,
        activation_url=url_for('accept_registration',
                               key=key,
                               _external=True))
    return "Your registration has been confirmed: {}!".format(status)  # TODO!!


@app.route('/accept/<key>')
@login_required
def accept_registration(key):
    try:
        loco.accept_registration(key)
        flash('Accepted registration with key {}'.format(key), 'info')
    except ValueError as exc:
        flash('Registration was already accepted!', 'info')
        app.logger.debug(exc)
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        authed = loco.auth(request.form['login'], request.form['password'])
        user = loco.get_user(request.form['login'])
        if authed:
            login_user(user, remember=True)
            flash('Logged in successfully', 'info')
            return redirect(request.values.get('next') or url_for('index'))
        else:
            flash("Invalid credentials!", 'error')
            return render_template('login.html')
    else:
        return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/manage')
@login_required
def manage():
    groups = loco.get_grps()
    slots = loco.slots()

    groups_a = {mdl.TimeSlot(_.start_time): _ for _ in groups
                if _.start_time and _.direction == mdl.DIR_A}
    groups_b = {mdl.TimeSlot(_.start_time): _ for _ in groups
                if _.start_time and _.direction == mdl.DIR_B}
    groups_none = sorted([_ for _ in groups if not _.start_time],
                         key=lambda x: x.name)

    return render_template('manage.html',
                           slots=slots,
                           groups_a=groups_a,
                           groups_b=groups_b,
                           groups_none=groups_none)


@app.route('/manage/table/<table>')
@login_required
def tabularadmin(table):

    if table not in MODIFIABLE_TABLES:
        return 'Access Denied', 401

    if table == 'group':
        columns = [_ for _ in mdl.Group.__table__.columns
                   if _.name not in ('id', 'confirmation_key')]
        keys = [_ for _ in mdl.Group.__table__.columns if _.primary_key]
        data = g.session.query(mdl.Group)
        data = data.order_by(mdl.Group.cancelled, mdl.Group.order)
    elif table == 'station':
        columns = [_ for _ in mdl.Station.__table__.columns
                   if _.name not in ('id', 'confirmation_key')]
        keys = [_ for _ in mdl.Station.__table__.columns if _.primary_key]
        data = g.session.query(mdl.Station)
        data = data.order_by(mdl.Station.order)
    elif table == 'form':
        columns = [_ for _ in mdl.Form.__table__.columns
                   if _.name not in ('id', 'confirmation_key')]
        keys = [_ for _ in mdl.Form.__table__.columns if _.primary_key]
        data = g.session.query(mdl.Form)
        data = data.order_by(mdl.Form.name)
    else:
        return 'Table {} not yet supported!'.format(table), 400

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

    if cls not in MODIFIABLE_TABLES:
        return 'Access Denied', 401

    data = request.json
    table = mdl.Base.metadata.tables[cls]
    if data['oldValue'] in ('', None):
        cell_predicate = or_(table.c[datum] == '', table.c[datum] == None)
    else:
        cell_predicate = table.c[datum]==data['oldValue']

    query = table.update().values(
        **{datum: data['newValue']}).where(and_(
            table.c.id==key,
            cell_predicate))
    try:
        result = g.session.execute(query)
    except Exception as exc:
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
def set_time_slot(group_name):
    data = request.json
    print(data)  # TODO: data is not yet handled!
    group = loco.get_grp_by_name(group_name)
    if not group:
        # TODO: If the group is not found, add it to the DB.
        return '"Group not found"', 404
    return '{{"is_success": true, "group_id": {}}}'.format(group.id)  # TODO


@app.route('/js-fragment/group-tooltip/<int:group_id>')
def group_tooltip(group_id):
    group = loco.get_grps_by_id(group_id)
    return render_template('group-tooltip.html',
                           group=group)


if __name__ == '__main__':
    app.run(debug=app.localconf.get('devserver', 'debug', default=False),
            host=app.localconf.get('devserver', 'listen'),
            port=int(app.localconf.get('devserver', 'port')))
