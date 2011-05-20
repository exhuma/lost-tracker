from flask import Flask, render_template, abort
from lost_tracker.models import Group, Station, get_state
from lost_tracker.database import db_session as session
app = Flask(__name__)

@app.route('/')
def index():
    stations = Station.query.all()
    groups = Group.query.all()

    state_matrix = []
    for group in groups:
        tmp = [group]
        for station in stations:
            tmp.append((group.id, station.id))
        state_matrix.append(tmp)
    return render_template('matrix.html', matrix=state_matrix, stations=stations)

@app.route('/station/<base64key>')
def station(base64key):
    qry = session.query(Station)
    qry = qry.filter_by( name = base64key.decode('base64') )
    station = qry.first()
    if not station:
        return abort(404)

    groups = Group.query.all()
    return render_template('station.html',
            station=station,
            group_states=[ (grp, get_state(grp, station)) for grp in groups ])

if __name__ == '__main__':
    app.run(debug=True)
