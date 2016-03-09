from collections import namedtuple
from json import dumps

from flask import (
    Blueprint,
    abort,
    jsonify,
    make_response,
    render_template,
    request,
)

from flask.ext.security import (
    roles_accepted,
)

from lost_tracker.localtypes import json_encoder
import lost_tracker.core as loco
import lost_tracker.models as mdl

STATION = Blueprint('station', __name__)


def _stategetter(element):
    """
    Custom sorting for group states. Make "arrived" groups come first,
    then all "unknowns". Make "completed" and "cancelled" groups come last.
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


@STATION.route('/<path:name>')
def details(name):
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


@STATION.route('/<int:id>', methods=['DELETE'])
@roles_accepted(mdl.Role.ADMIN)
def delete(id):
    loco.delete_station(id)
    return jsonify(status='ok')


@STATION.route('/<station_name>/dashboard')
@roles_accepted(mdl.Role.ADMIN)
def dashboard(name):
    # TODO implement
    raise NotImplementedError('Not yet implemented')
