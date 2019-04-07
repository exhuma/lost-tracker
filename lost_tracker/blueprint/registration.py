from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from flask.ext.babel import gettext
from flask.ext.security import (
    current_user,
    login_required,
    roles_accepted,
)

import lost_tracker.core as loco
import lost_tracker.models as mdl

REGISTRATION = Blueprint('registration', __name__)


@REGISTRATION.route('/new', methods=['GET', 'POST'])
def new():
    external_registration = current_app.localconf.get(
        'app', 'external_registration', fallback='').strip()
    if external_registration:
        return redirect(external_registration)

    if not current_user.is_authenticated:
        return current_app.login_manager.unauthorized()
    is_open = mdl.Setting.get('registration_open', default=False)
    if not is_open and not current_user.has_role(mdl.Role.ADMIN):
        return render_template('registration_closed.html')

    if request.method == 'POST':
        data = {
            "group_name": request.form.get('group_name'),
            "contact_name": request.form.get('contact_name'),
            "email": request.form.get('email'),
            "tel": request.form.get('tel'),
            "time": request.form.get('time'),
            "comments": request.form.get('comments'),
            "user_id": current_user.id,
            "num_vegetarians": request.form.get('num_vegetarians'),
            "num_participants": request.form.get('num_participants'),
        }
        try:
            key = loco.store_registration(
                current_app.mailer, mdl.DB.session, data)
        except ValueError as exc:
            return 'Error: ' + str(exc), 400

        # We'll auto-confirm the registration. This is not possible due to the
        # social login. However, this step could be removed altogether. Leaving
        # it in right now to avoid making too many changes all at once.
        loco.confirm_registration(
            current_app.mailer,
            key,
            activation_url=url_for('.accept',
                                   key=key,
                                   _external=True))

        return render_template(
            'notice.html',
            message=gettext(
                'The registration has been recorded. You will receive an '
                'e-mail once the registartion has been successfully '
                'processed! You can see all your registered groups on <a '
                'href="{}">your profile</a>.').format(url_for('root.profile')))

    return render_template('register.html',
                           stats=loco.stats(current_app.localconf))


@REGISTRATION.route('/accept/<key>')
@roles_accepted(mdl.Role.STAFF, mdl.Role.ADMIN)
def accept(key):
    group = mdl.Group.one(key=key)

    if group.accepted:
        flash(gettext('This group has already been accepted!'), 'info')

    loco.accept_registration(current_app.mailer, key, group)

    return render_template('edit_group.html',
                           group=group,
                           dir_a=mdl.DIR_A,
                           dir_b=mdl.DIR_B)
