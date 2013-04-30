import os
from collections import namedtuple

from sqlalchemy import create_engine
from lost_tracker.core import (get_matrix, get_state_sum, get_grps, add_grp,
                               get_stations, add_station, get_stat_by_name,
                               add_form_db, get_forms)
from flask import (Flask, render_template, abort, jsonify, g, request, flash,
                   url_for, redirect)

from lost_tracker.models import (get_state, advance as db_advance,
                                 get_form_score_full, set_form_score,
                                 GroupStation, get_form_score)
from lost_tracker.database import Base
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config.from_object('lost_tracker.default_settings')
app.secret_key='\xd8\xb1ZD\xa2\xf9j%\x0b\xbf\x11\x18\xe0$E\xa4]\xf0\x03\x7fO9\xb0\xb5'  # NOQA

if 'LOST_TRACKER_SETTINGS' in os.environ:
    app.config.from_envvar('LOST_TRACKER_SETTINGS')
else:
    app.logger.warning('Running with default settings! Specify your own '
                       'config file using the LOST_TRACKER_SETTINGS '
                       'environment variable!')

Base.metadata.bind = create_engine(app.config.get('DB_DSN'))


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
        message = "SQL ERROR: {0}".format(exc)
        flash(message)


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
    new_state = db_advance(groupId, station_id)
    return jsonify(
        group_id=groupId,
        station_id=station_id,
        new_state=new_state)


@app.route('/station/<path:name>')
def station(name):
    station = get_stat_by_name(name)
    if not station:
        return abort(404)

    groups = get_grps()
    GroupStateRow = namedtuple('GroupStateRow',
                               'group, '
                               'state')
    group_states = []
    for grp in groups:
        state = get_state(grp.id, station.id)
        group_states.append(
            GroupStateRow(grp, state))

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
    return render_template('add_group.html', message=message, groups=grps)


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
    station_score = request.form['station_score']
    form_id = int(request.form['form_id'])
    form_score = request.form['form_score']

    if station_score:
        GroupStation.set_score(g.session,
                               group_id,
                               station_id,
                               int(station_score))

    if form_score:
        set_form_score(group_id, form_id, int(form_score))

    if request.is_xhr:
        return jsonify(status='ok')

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


if __name__ == '__main__':
    app.run(debug=app.config.get('DEBUG', False),
            host=app.config.get('LISTEN'),
            port=app.config.get('PORT'))
