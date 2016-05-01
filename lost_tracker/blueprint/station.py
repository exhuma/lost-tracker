from collections import namedtuple
from json import dumps
import logging

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
LOG = logging.getLogger(__name__)


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


@STATION.route('/<int:key>')
def details(key):
    station = mdl.Station.by_name_or_id(key)
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


@STATION.route('/edit/<int:key>')
def edit(key):
    station = mdl.Station.by_name_or_id(key)
    if not station:
        return abort(404)

    return render_template(
        'edit_station.html',
        station=station)


@STATION.route('/new')
def new():
    return render_template('edit_station.html', station=None)


@STATION.route('/save', methods=['POST'])
def save():
    try:
        id = request.form.get('id', 0)
        id = int(id) if id else None
        data = {
            'id': id,
            'name': request.form['name'].strip(),
            'order': int(request.form['order']),
            'contact': request.form['contact'].strip(),
            'phone': request.form['phone'].strip(),
            'is_start': bool(request.form.get('is_start', False)),
        }
    except (KeyError, ValueError):
        LOG.debug('Invalid request with data: %r', request.form, exc_info=True)
        return '<h1>Bad Request</h1>Invalid variables specified!', 400
    loco.save_station(mdl.DB.session, data)
    flash(gettext('Station {} saved!').format(data['name']))
    return redirect(url_for('.list'))


@STATION.route('/<int:id>', methods=['DELETE'])
@STATION.route('/<int:id>/delete')
@roles_accepted(mdl.Role.ADMIN)
def delete(id):

    if request.args.get('confirmed', 0) == 'yes':
        loco.delete_station(id)
        flash(gettext('Station deleted!'))
        return redirect(url_for('.list'))
    elif request.args.get('confirmed', 0) == 'no':
        return redirect(url_for('.list'))
    else:
        return render_template('confirm.html',
                               requested_by='station.delete',
                               requestor_args={'id': id})


@STATION.route('/<station>/dashboard')
def dashboard(station):
    result = loco.get_dashboard(station)
    before = result['neighbours']['before']
    after = result['neighbours']['after']
    output = {
        'after_states': [gs.to_dict() for gs in result['after_states']],
        'before_states': [gs.to_dict() for gs in result['before_states']],
        'main_states': [gs.to_dict() for gs in result['main_states']],
        'neighbours': {
            'before': before.to_dict() if before else None,
            'after': after.to_dict() if after else None,
        },
        'station': result['station'].to_dict()
    }
    return jsonify(data=output)


@STATION.route('/')
def list():
    result = loco.get_stations(mdl.DB.session)
    return render_template('list_stations.html',
                           stations=result)
