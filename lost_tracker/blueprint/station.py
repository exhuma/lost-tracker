from collections import namedtuple
from json import dumps

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)

from flask.ext.babel import gettext

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

    if request.args.get('confirmed', 0) == 'yes':
        loco.delete_station(id)
        flash(gettext('Station deleted!'))
        return redirect(url_for('/'))
    elif request.args.get('confirmed', 0) == 'no':
        return redirect(url_for('/'))
    else:
        return render_template('confirm.html',
                               requested_by='station.delete',
                               requestor_args={'id': id})


@STATION.route('/<station>/dashboard')
def dashboard(station):
    result = loco.get_dashboard(station)
    output = {
        'after_states': [gs.to_dict() for gs in result['after_states']],
        'before_states': [gs.to_dict() for gs in result['before_states']],
        'main_states': [gs.to_dict() for gs in result['main_states']],
        'neighbours': {
            'before': result['neighbours']['before'].to_dict(),
            'after': result['neighbours']['after'].to_dict(),
        },
        'station': result['station'].to_dict()
    }
    return jsonify(data=output)
