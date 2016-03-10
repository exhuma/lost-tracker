from json import dumps

from flask import make_response, Blueprint
from flask.ext.security import login_required
import io
import qrcode

import lost_tracker.models as mdl


QR = Blueprint('qr', __name__)


@QR.route('/<id>')
@login_required
def generate(id):
    group = mdl.Group.one(id=id)
    data = {
        'id': group.id,
        'name': group.name,
    }
    img = qrcode.make(dumps(data))
    blob = io.BytesIO()
    img.save(blob, format="PNG")
    output = blob.getvalue()
    response = make_response(output)
    response.content_type = "image/png"
    return response
