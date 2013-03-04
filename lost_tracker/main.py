import os

from sqlalchemy import create_engine
from flask import Flask, render_template, abort, jsonify, g

from lost_tracker.models import (Group, Station, get_state,
        advance as db_advance, STATE_FINISHED, STATE_UNKNOWN, STATE_ARRIVED)
from lost_tracker.database import Base

app = Flask(__name__)
app.config.from_object('lost_tracker.default_settings')

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

if __name__ == '__main__':
    app.run(debug=True)
