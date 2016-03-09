from collections import namedtuple

from sqlalchemy import and_, or_
from sqlalchemy import Unicode, Integer
from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
)

from flask.ext.babel import gettext
from flask.ext.security import roles_accepted

import lost_tracker.models as mdl


# This is intentionally not in the config. It's tightly bound to the code. And
# adding a table without modifying the rest of the code would not make sense.
MODIFIABLE_TABLES = ('group', 'station', 'form')
TABULAR = Blueprint('tabular', __name__)


@TABULAR.route('/table/<name>')
@roles_accepted(mdl.Role.ADMIN)
def tabularadmin(name):
    if name not in MODIFIABLE_TABLES:
        return gettext('Access Denied'), 401

    custom_order = None
    if 'order' in request.args:
        custom_order = request.args['order']

    if name == 'group':
        columns = [_ for _ in mdl.Group.__table__.columns
                   if _.name not in ('id', 'confirmation_key')]
        keys = [_ for _ in mdl.Group.__table__.columns if _.primary_key]
        data = mdl.DB.session.query(mdl.Group)
        if custom_order and custom_order in mdl.Group.__table__.columns:
            data = data.order_by(mdl.Group.__table__.columns[custom_order])
        else:
            data = data.order_by(mdl.Group.cancelled, mdl.Group.order)
    elif name == 'station':
        columns = [_ for _ in mdl.Station.__table__.columns
                   if _.name not in ('id', 'confirmation_key')]
        keys = [_ for _ in mdl.Station.__table__.columns if _.primary_key]
        data = mdl.DB.session.query(mdl.Station)
        if custom_order and custom_order in mdl.Station.__table__.columns:
            data = data.order_by(mdl.Station.__table__.columns[custom_order])
        else:
            data = data.order_by(mdl.Station.order)
    elif name == 'form':
        columns = [_ for _ in mdl.Form.__table__.columns
                   if _.name not in ('id', 'confirmation_key')]
        keys = [_ for _ in mdl.Form.__table__.columns if _.primary_key]
        data = mdl.DB.session.query(mdl.Form)
        if custom_order and custom_order in mdl.Form.__table__.columns:
            data = data.order_by(mdl.Form.__table__.columns[custom_order])
        else:
            data = data.order_by(mdl.Form.order, mdl.Form.name)
    else:
        return gettext('Table {name} not yet supported!').format(
            name=name), 400

    # prepare data for the template
    Row = namedtuple('Row', 'key, data')
    Column = namedtuple('Column', 'name, type, value')
    rows = []
    for row in data:
        pk = {_.name: getattr(row, _.name) for _ in keys}
        rowdata = [Column(_.name,
                          _.type.__class__.__name__.lower(),
                          getattr(row, _.name)) for _ in columns]
        rows.append(Row(pk, rowdata))

    return render_template('tabular.html',
                           clsname=name,
                           columns=columns,
                           data=rows)


@TABULAR.route('/cell/<cls>/<key>/<datum>', methods=['PUT'])
@roles_accepted(mdl.Role.ADMIN)
def update_cell_value(cls, key, datum):

    if cls not in MODIFIABLE_TABLES:
        return gettext('Access Denied'), 401

    data = request.json
    table = mdl.DB.metadata.tables[cls]

    if table.columns[datum].type.__class__ == Unicode:
        coerce_ = unicode.strip
    elif table.columns[datum].type.__class__ == Integer:
        coerce_ = int
    else:
        coerce_ = lambda x: x  # NOQA

    if data['oldValue'] in ('', None) and coerce_ == str.strip:
        cell_predicate = or_(table.c[datum] == '',
                             table.c[datum] == None)  # NOQA
    elif data['oldValue'] in ('', None):
        cell_predicate = table.c[datum] == None  # NOQA
    else:
        cell_predicate = table.c[datum] == data['oldValue']

    data['newValue'] = coerce_(data['newValue'])
    query = table.update().values(**{datum: data['newValue']}).where(
        and_(table.c.id == key, cell_predicate))

    try:
        result = mdl.DB.session.execute(query)
    except Exception as exc:
        TABULAR.logger.debug(exc)
        return jsonify(message='Invalid data'), 400

    if result.rowcount == 1:
        return jsonify(success=True, new_value=data['newValue'])
    else:
        current_entity = mdl.DB.session.query(table).filter_by(id=key).one()
        # If the DB value is already the same as the one we try to put, we can
        # assume it's a success.
        if getattr(current_entity, datum) == data['newValue']:
            return jsonify(success=True, new_value=data['newValue'])
        return jsonify(db_value=getattr(current_entity, datum)), 409
