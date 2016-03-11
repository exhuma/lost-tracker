import logging

from flask import (
    Blueprint,
    flash,
    redirect,
    request,
    url_for,
)

from flask.ext.babel import gettext
from flask.ext.security import current_user, login_required

import lost_tracker.core as loco
import lost_tracker.models as mdl

COMMENT = Blueprint('comment', __name__)
LOG = logging.getLogger(__name__)


@COMMENT.route('/', methods=['POST'])
@login_required
def add():
    group_id = request.form.get('group_id', None)
    group_id = int(group_id) if group_id else None
    if not group_id:
        return gettext('Invalid Request!'), 400

    group = mdl.Group.one(id=group_id)

    if group not in current_user.groups:
        return gettext('Access denied!'), 403

    content = request.form.get('content', '').strip()
    if content:
        loco.store_message(mdl.DB.session, group, current_user, content)

    flash(gettext("Message saved!"))
    return redirect(url_for('group.show_comments', id=group_id))
