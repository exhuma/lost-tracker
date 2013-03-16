import os

from sqlalchemy import create_engine
from flask import Flask, render_template, abort, jsonify, g, request, flash, url_for, redirect

from lost_tracker.models import (Group, Station, get_state,
        advance as db_advance, STATE_FINISHED, STATE_UNKNOWN, STATE_ARRIVED,
        set_score, get_score)
from lost_tracker.database import Base
from sqlalchemy.exc import IntegrityError
app = Flask(__name__)
app.config.from_object('lost_tracker.default_settings')
app.secret_key='\xd8\xb1ZD\xa2\xf9j%\x0b\xbf\x11\x18\xe0$E\xa4]\xf0\x03\x7fO9\xb0\xb5'  # NOQA

if 'LOST_TRACKER_SETTINGS' in os.environ:
    app.config.from_envvar('LOST_TRACKER_SETTINGS')
else:
    app.logger.warning('Running with default settings! Specify your own '
            'config file using the LOST_TRACKER_SETTINGS environment '
            'variable!')

Base.metadata.bind = create_engine(app.config.get('DB_DSN'))


@app.before_request
def before_request():
    # This import is deferred as it triggers the DB engine constructor on
    # first import! As it may not yet be configured at global import time this
    # would fail if imported globally.
    from lost_tracker.database import db_session as session
    g.session = session


@app.route('/')
def index():
    stations = Station.query
    stations = stations.order_by(Station.order)
    stations = stations.all()
    groups = Group.query
    groups = groups.order_by(Group.order)
    groups = groups.all()
    
    print request

    state_matrix = []
    for group in groups:
        tmp = [group]
        for station in stations:
            tmp.append(get_state(group.id, station.id))
        state_matrix.append(tmp)

    sums = []
    if state_matrix:
        sums = [[0, 0, 0] for _ in state_matrix[0][1:]]
        for row in state_matrix:
            for i, state in enumerate(row[1:]):
                if not state or state == STATE_UNKNOWN:
                    sums[i][STATE_UNKNOWN] += 1
                elif state == STATE_ARRIVED:
                    sums[i][STATE_ARRIVED] += 1
                elif state == STATE_FINISHED:
                    sums[i][STATE_FINISHED] += 1

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
    qry = g.session.query(Station)
    qry = qry.filter_by( name = name )
    station = qry.first()
    if not station:
        return abort(404)

    groups = Group.query
    groups = groups.order_by(Group.order)
    groups = groups.all()
    return render_template('station.html',
            station=station,
            group_states=[(grp, get_state(grp.id, station.id))
                          for grp in groups])

def get_grps():
    groups = Group.query
    groups = groups.order_by(Group.order)
    groups = groups.all()
    return groups

def add_grp(grp_name, contact, phone, direction, start_time):
    print "Direction: " + direction
    if direction is "1":
        color = "Giel"
    else:
        color = "Roud"

    new_grp = Group(grp_name, contact, phone, direction, start_time)
    g.session.add(new_grp)
    try:
        g.session.commit()
    except IntegrityError as exc:
        g.session.rollback()
        return "SQL ERROR: {0}".format(exc)
    return "Group " + grp_name + " with Contact " + contact + " / " + phone + " was successfully added into the DB. The given start-time is " + start_time + " and the direction is " + color

def add_station(stat_name, contact, phone):
    new_station = Station(stat_name, contact, phone)
    g.session.add(new_station)
    try:
        g.session.commit()
    except IntegrityError as exc:
        g.session.rollback()
        return "SQL ERROR: {0}".format(exc)
    return "Station " + stat_name + " added. Contact: " + contact + " / " + phone

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

    message = add_grp(grp_name, grp_contact, grp_tel, grp_direction, grp_start)
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

    message = add_station(name, contact, phone)
    flash(message)
    return redirect(url_for("init_stat_form"))

@app.route('/set_score')
def init_score_form():
    message = ""
    score = get_score()
    groups = get_grps()
    return render_template('set_score.html', message=message, score=score, groups=groups)

@app.route('/set_score', methods=['POST'])
def score_form():
    grp_id = request.form['grp_id']
    stat_id = request.form['stat_id']
    q_score = request.form['q_score']
    q_id = request.form['q_id']
    p_score = request.form['p_score']
    if not grp_id or not stat_d:
        message = "You have to specify the Group AND the Station for which you want to enter the score. Nothing entered!"
        flash(message)
        return redirect(url_for("init_score_form"))
    if q_score and not q_id:
        message = "You need to specify a questionnaire id when entering questionnaire points. Nothing entered!"
        flash(message)
        return redirect(url_for("init_score_form"))
    out = set_score(grp_id, stat_id, q_score, q_id, p_score)
    if out == "insert":
        message = "Score added for Group ID" + grp_id + "for Station ID" + stat_id + "Questionnaire Nr " + q_id + " : " + q_score + " , Post score: " + p_score
        flush(message)
        return redirect(url_for("init_score_form"))
    else:
        message = "Score updated for Group ID " + grp_id + "for Station ID" + stat_id + "Questionnaire Nr " + q_id + " : " + q_score + " , Post score: " + p_score
        return redirect(url_for("init_score_form"))

if __name__ == '__main__':
    app.run(debug=True, port=7000)
