import logging

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from flask.ext.babel import gettext
from flask.ext.security import roles_accepted, current_user, login_required

import lost_tracker.core as loco
import lost_tracker.models as mdl

GROUP = Blueprint('group', __name__)
LOG = logging.getLogger(__name__)


@GROUP.route('/<int:group_id>/score/<int:station_id>', methods=['PUT'])
@roles_accepted(mdl.Role.STAFF, mdl.Role.ADMIN)
def set_score(group_id, station_id):
    try:
        form_score = request.json['form']
        station_score = request.json['station']
    except LookupError:
        return jsonify({'message': 'Missing value'}), 400
    loco.set_score(mdl.DB.session, group_id, station_id, station_score,
                   form_score)
    return jsonify({
        'form_score': form_score,
        'station_score': station_score
    })


@GROUP.route('/<id>', methods=['POST'])
@login_required
def save_info(id):
    intent = request.form.get('intent', 'accept')
    group = mdl.Group.one(id=id)

    if not current_user.has_role(mdl.Role.ADMIN):
        if intent != 'update' or group.user.id != current_user.id:
            # For non-admins we only allow "update" permission on owned goups.
            return gettext("Access Denied!"), 403

    # attributes that don't require admin permissions.
    data = {
        'name': request.form['name'],
        'phone': request.form['phone'],
        'comments': request.form['comments'],
        'contact': request.form['contact'],
        'send_email': True,
        'notification_recipient': 'admins',
    }

    # ... next, if we are allowed, add admin-only attributes
    if current_user.has_role(mdl.Role.ADMIN):
        data['direction'] = request.form['direction']
        data['start_time'] = request.form['start_time']
        data['send_email'] = request.form.get('send_email') == 'true'
        data['cancelled'] = request.form.get('cancelled') == 'true'
        data['completed'] = request.form.get('completed') == 'true'
        if intent == 'accept' and not group.accepted:
            loco.accept_registration(current_app.mailer,
                                     group.confirmation_key,
                                     group)
            flash(gettext('Accepted registration for group {}').format(
                group.name), 'info')
        else:
            data['accepted'] = request.form.get('accepted') == 'true'
        data['notification_recipient'] = 'owner'

    loco.update_group(current_app.mailer, id, data)

    flash(gettext('Group {name} successfully updated!').format(
        name=data['name']), 'info')

    if data['send_email']:
        flash(gettext('E-Mail sent successfully!'), 'info')

    if current_user.has_role(mdl.Role.ADMIN):
        return redirect(url_for('group.edit', name=data['name']))
    else:
        return redirect(url_for('profile'))


@GROUP.route('/<group_name>/timeslot', methods=['PUT'])
@roles_accepted(mdl.Role.STAFF, mdl.Role.ADMIN)
def set_time_slot(group_name):
    data = request.json
    if data['direction'] not in (mdl.DIR_A, mdl.DIR_B):
        return jsonify(
            message=gettext('Incorrect value for direction: {!r}').format(
                data['direction'])), 400
    group = mdl.Group.one(name=group_name)
    if not group:
        group = mdl.Group(name=group_name, start_time=data['new_slot'])
        mdl.DB.session.add(group)
    group.start_time = data['new_slot']
    group.direction = data['direction']
    return '{{"is_success": true, "group_id": {}}}'.format(group.id)


@GROUP.route('/<int:id>/comments')
@login_required
def show_comments(id):
    group = mdl.Group.one(id=id)
    if not group:
        return gettext('No such entity!'), 404
    if group not in current_user.groups:
        return gettext('Access Denied!'), 403

    return render_template('messages.html', group=group)


@GROUP.route('/')
@roles_accepted(mdl.Role.STAFF, mdl.Role.ADMIN)
def list():
    groups = mdl.Group.all()
    groups = groups.order_by(None)
    groups = groups.order_by(mdl.Group.inserted)
    return render_template('group_list.html', groups=groups)


@GROUP.route('/<name>')
def edit(name):
    group = mdl.Group.one(name=name)
    if not group:
        return gettext('Not found!'), 404

    if group.user.id != current_user.id and not current_user.has_role(
            mdl.Role.ADMIN):
        return gettext('Access Denied!'), 403

    return render_template('edit_group.html',
                           group=group,
                           dir_a=mdl.DIR_A,
                           dir_b=mdl.DIR_B,
                           intent='edit')
