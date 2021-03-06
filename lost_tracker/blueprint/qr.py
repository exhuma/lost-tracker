from json import dumps
import logging

from flask import (
    Blueprint,
    current_app,
    make_response,
    render_template,
    request,
    url_for,
)
from flask.ext.babel import gettext
from flask.ext.security import login_required
import io
import qrcode

from lost_tracker.util import basic_auth
import lost_tracker.core as loco
import lost_tracker.models as mdl


QR = Blueprint('qr', __name__)
LOG = logging.getLogger(__name__)


@QR.route('/<id>')
@login_required
def generate(id):
    group = mdl.Group.one(id=id)
    data = {
        'action': 'scan_station',
        'group_id': group.id,
        'group_name': group.name,
    }
    img = qrcode.make(dumps(data))
    blob = io.BytesIO()
    img.save(blob, format="PNG")
    output = blob.getvalue()
    response = make_response(output)
    response.content_type = "image/png"
    return response


@QR.route('/config/<int:station>')
@basic_auth
def config(station):
    station = mdl.Station.one(id=station)
    base_url = url_for('root.index', _external=True)
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    data = {
        'action': 'app_settings',
        'baseUrl': base_url,
        'stationName': station.name,
        'login': current_app.localconf.get('app', 'login'),
        'password': current_app.localconf.get('app', 'password'),
    }
    img = qrcode.make(dumps(data))
    blob = io.BytesIO()
    img.save(blob, format="PNG")
    output = blob.getvalue()
    response = make_response(output)
    response.content_type = "image/png"
    return response


@QR.route('/submit/<station_name>', methods=['POST'])
@basic_auth
def submit_qr(station_name):
    station = mdl.Station.one(name=station_name)
    if not station:
        return gettext('No such entity!'), 404

    new_state = request.json.get('new_state', None)
    group_id = request.json.get('group_id', None)

    if not group_id or not new_state:
        LOG.debug('Need both IDs for group and status. Got: '
                  'group=%r, new_state=%r', group_id, new_state)
        return gettext('Invalid Request!'), 400

    if new_state not in (mdl.STATE_ARRIVED, mdl.STATE_UNKNOWN,
                         mdl.STATE_FINISHED):
        LOG.debug('Invalid value for state: %r', new_state)
        return gettext('Invalid Request!'), 400

    obj = loco.set_group_state(mdl.DB.session, group_id, station.id, new_state)
    if not obj:
        mdl.DB.session.rollback()
        return '"Something went wrong!"'
    else:
        mdl.DB.session.commit()
        return '"OK"'


@QR.route('/display')
def display():
    all_args = request.args.to_dict()
    endpoint = all_args.pop('type')
    title = all_args.pop('title')
    if not title or not endpoint:
        return 'Unsupported QR display', 400
    image_url = url_for(endpoint, **all_args)
    return render_template('qr_display.html',
                           image_url=image_url,
                           title=title)
