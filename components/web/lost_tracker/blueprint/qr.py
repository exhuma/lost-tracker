from json import dumps
import logging

from flask import make_response, Blueprint, request
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
        'action': 'scan_at_station',
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
