from flask import (
    Blueprint,
    flash,
    redirect,
    request,
    url_for,
)

from flask.ext.babel import gettext
from flask.ext.security import current_user
from flask.ext.security import roles_accepted

USER = Blueprint('user', __name__)


@USER.route('/save_profile', methods=['POST'])
@roles_accepted('authenticated')
def save_profile():
    current_user.email = request.form['email']
    flash(gettext('E-Mail successfully updated to {}').format(
        request.form['email']))
    return redirect(url_for('root.profile'))
