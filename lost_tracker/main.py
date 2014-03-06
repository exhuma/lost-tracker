from collections import namedtuple
from operator import attrgetter

from config_resolver import Config
from sqlalchemy import create_engine
from lost_tracker.core import (get_matrix, get_state_sum, get_grps, add_grp,
                               get_stations, add_station, get_stat_by_name,
                               add_form_db, get_forms, get_grps_by_id)
from flask import (Flask, render_template, abort, jsonify, g, request, flash,
                   url_for, redirect)

from lost_tracker.models import (get_state, advance as db_advance,
                                 get_form_score_full, set_form_score,
                                 GroupStation, get_form_score,
                                 DIR_A, DIR_B, score_totals, STATE_UNKNOWN,
                                 STATE_FINISHED, STATE_ARRIVED)
from lost_tracker.database import Base
from lost_tracker import __version__
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.localconf = Config('mamerwiselen', 'lost-tracker',
                       version='1.0', require_load=True)
app.secret_key='\xd8\xb1ZD\xa2\xf9j%\x0b\xbf\x11\x18\xe0$E\xa4]\xf0\x03\x7fO9\xb0\xb5'  # NOQA


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
    stations = get_stations()
    groups = get_grps()

    state_matrix = get_matrix(stations, groups)
    sums = get_state_sum(state_matrix)

    return render_template('matrix.html',
                           matrix=state_matrix,
                           stations=stations,
                           sums=sums)


@app.route('/advance/<groupId>/<station_id>')
def advance(groupId, station_id):
    new_state = db_advance(g.session, groupId, station_id)
    return jsonify(
        group_id=groupId,
        station_id=station_id,
        new_state=new_state)


@app.route('/station/<path:name>')
def station(name):
    station = get_stat_by_name(name)
    if not station:
        return abort(404)

    def stategetter(element):
        """
        Custom sorting for group states. Make "arrived" groups come first,
        then all "unknowns". Make "finished" groups come last.
        """
        if element is None or element.state is None:
            return STATE_UNKNOWN
        elif element.state.state == STATE_ARRIVED:
            return 0
        elif element.state.state == STATE_UNKNOWN:
            return 1
        elif element.state.state == STATE_FINISHED:
            return 2
        else:
            return 99

    groups = get_grps()
    GroupStateRow = namedtuple('GroupStateRow',
                               'group, '
                               'state')
    group_states = []
    for grp in groups:
        group_station = get_state(grp.id, station.id)
        if not group_station:
            state = None
        else:
            state = group_station
        group_states.append(
            GroupStateRow(grp, state))
    group_states.sort(key=stategetter)

    questionnaires = get_forms()

    return render_template(
        'station.html',
        station=station,
        groups=groups,
        group_states=group_states,
        questionnaires=questionnaires)


@app.route('/group')
def init_grp_form():
    message = ""
    grps = get_grps()
    return render_template('add_group.html',
                           message=message,
                           groups=grps,
                           DIR_A=DIR_A,
                           DIR_B=DIR_B)


@app.route('/group', methods=['POST'])
def grp_form():
    grp_name = request.form['grp_name']
    grp_contact = request.form['grp_contact']
    grp_tel = request.form['grp_tel']
    grp_direction = request.form['grp_direction']
    grp_start = request.form['grp_start']

    message = add_grp(
        grp_name,
        grp_contact,
        grp_tel,
        grp_direction,
        grp_start,
        g.session)

    flash(message)
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

    message = add_station(name, contact, phone, g.session)
    flash(message)
    return redirect(url_for("init_stat_form"))


@app.route('/form_score')
def init_form_score():
    grps = get_grps()
    form_scores = get_form_score_full()
    return render_template(
        'form_score.html',
        form_scores=form_scores,
        groups=grps)


@app.route('/score/<int:group_id>/<int:form_id>')
def group_form_score(group_id, form_id):
    return jsonify(
        score=get_form_score(group_id, form_id))


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
        group_station = GroupStation.get(
            group_id,
            station_id)
        if not group_station:
            group_station = GroupStation(
                group_id,
                station_id)
            g.session.add(group_station)
        group_station.score = int(station_score)

    if form_id is not None:
        set_form_score(group_id, form_id, int(form_score))

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
        GroupStation.set_score(group_id, station_id, score)

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
        set_form_score(group_id, form_id, score)

    if request.is_xhr:
        return jsonify(status='ok')

    return redirect(url_for("init_form_score"))


@app.route('/add_form')
def init_add_form():
    message = ""
    forms = get_forms()
    return render_template('add_form.html', message=message, forms=forms)


@app.route('/add_form', methods=['POST'])
def add_form():
    form_id = int(request.form['form_id'])
    name = request.form['name']
    max_score = int(request.form['max_score'])
    message = add_form_db(form_id, name, max_score, g.session)
    flash(message)
    return redirect(url_for("init_add_form"))


@app.route('/scoreboard')
def scoreboard():
    result = sorted(score_totals(), key=attrgetter('score_sum'), reverse=True)
    output = []
    pos = 1
    for row in result:
        group = get_grps_by_id(row.group_id)
        output.append([pos, group.name, row.score_sum])
        pos+=1
    return render_template('scoreboard.html', scores=output)


@app.route('/guide')
def guide():
    return render_template('guide.html')


@app.route('/register')
def register():
    return render_template('register.html')


if __name__ == '__main__':
    app.run(debug=app.localconf.get('devserver', 'debug', default=False),
            host=app.localconf.get('devserver', 'listen'),
            port=int(app.localconf.get('devserver', 'port')))
