from flask import (
    Blueprint,
    current_app,
    flash,
    render_template,
    request,
    url_for,
)

from flask.ext.babel import gettext
from flask.ext.security import (
    current_user,
    roles_accepted,
)

import lost_tracker.core as loco
import lost_tracker.models as mdl

REGISTRATION = Blueprint('registration', __name__)


@REGISTRATION.route('/new', methods=['GET', 'POST'])
def new():
    is_open = mdl.Setting.get('registration_open', default=False)
    if not is_open:
        return render_template('registration_closed.html')

    if request.method == 'POST':
        data = {
            "group_name": request.form.get('group_name'),
            "contact_name": request.form.get('contact_name'),
            "email": request.form.get('email'),
            "tel": request.form.get('tel'),
            "time": request.form.get('time'),
            "comments": request.form.get('comments'),
        }
        confirmation_link = url_for('.confirm',
                                    _external=True)
        try:
            loco.store_registration(current_app.mailer, mdl.DB.session, data,
                                    confirmation_link)
        except ValueError as exc:
            return 'Error: ' + str(exc), 400
        return render_template(
            'notice.html',
            message=gettext(
                'The registration has been recorded. However it is not yet '
                'activated.  You will receive a confirmation e-mail any '
                'second now. You must click on the link in that e-mail to '
                'activate the registrtion! Once this step is done, the '
                'registration will be processed by the lost team, and you '
                'will receive another e-mail with the final confirmation once '
                'that is done.'))

    return render_template('register.html', stats=loco.stats())


@REGISTRATION.route('/confirm')
@REGISTRATION.route('/confirm/<key>')
def confirm(key):
    is_open = mdl.Setting.get('registration_open', default=False)
    if not is_open:
        return "Access denied", 401

    loco.confirm_registration(
        current_app.mailer,
        key,
        activation_url=url_for('.accept',
                               key=key,
                               _external=True))
    return render_template('notice.html', message=gettext(
        'Thank you. Your registration has been activated and the lost-team '
        'has been notified about your entry. Once everything is processed you '
        'will recieve another e-mail with the final details.'))


@REGISTRATION.route('/accept/<key>')
@roles_accepted('staff', 'admin')
def accept(key):
    group = mdl.Group.one(key=key)

    if group.finalized:
        flash(gettext('This group has already been accepted!'), 'info')

    return render_template('edit_group.html',
                           group=group,
                           dir_a=mdl.DIR_A,
                           dir_b=mdl.DIR_B)
