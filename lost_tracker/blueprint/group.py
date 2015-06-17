from flask import (
    Blueprint,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from flask.ext.babel import gettext
from flask.ext.login import (
    current_user,
    login_required,
)

import lost_tracker.core as loco
import lost_tracker.models as mdl

GROUP = Blueprint('group', __name__)


@GROUP.route('/<int:group_id>/score/<int:station_id>', methods=['PUT'])
@login_required
def set_score(group_id, station_id):
    try:
        form_score = request.json['form']
        station_score = request.json['station']
    except LookupError:
        return jsonify({'message': 'Missing value'}), 400
    loco.set_score(g.session, group_id, station_id, station_score, form_score)
    return jsonify({
        'form_score': form_score,
        'station_score': station_score
    })


@GROUP.route('/<id>', methods=['POST'])
@login_required
def save_info(id):
    if current_user.is_anonymous() or not current_user.admin:
        return "Access denied", 401
    group = mdl.Group.one(id=id)
    if not group.finalized:
        loco.accept_registration(group.confirmation_key, request.form)
        flash(gettext('Accepted registration for group {}').format(group.name),
              'info')
        return redirect(url_for('matrix'))
    else:
        loco.update_group(id,
                          request.form,
                          request.form['send_email'] == 'true')
        flash(gettext('Group {name} successfully updated!').format(
            name=request.form['name']), 'info')
        if request.form['send_email'] == 'true':
            flash(gettext('E-Mail sent successfully!'), 'info')
            return redirect(url_for('tabular.tabularadmin', table='group'))


@GROUP.route('/<group_name>/timeslot', methods=['PUT'])
@login_required
def set_time_slot(group_name):
    if current_user.is_anonymous() or not current_user.admin:
        return "Access denied", 401
    data = request.json
    if data['direction'] not in (mdl.DIR_A, mdl.DIR_B):
        return jsonify(
            message=gettext('Incorrect value for direction: {!r}').format(
                data['direction'])), 400
    group = mdl.Group.one(id=group_name)
    if not group:
        group = mdl.Group(name=group_name, start_time=data['new_slot'])
        g.session.add(group)
    group.start_time = data['new_slot']
    group.direction = data['direction']
    return '{{"is_success": true, "group_id": {}}}'.format(group.id)


@GROUP.route('/list')
@login_required
def list():
    groups = mdl.Group.all()
    groups = groups.order_by(None)
    groups = groups.order_by(mdl.Group.inserted)
    return render_template('group_list.html', groups=groups)
