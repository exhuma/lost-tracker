from datetime import datetime
from operator import attrgetter
try:
    from urllib.parse import unquote_plus  # py3
except ImportError:
    from urllib import unquote_plus  # py2

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session as flask_session,
    url_for,
)
from flask.ext.babel import gettext, format_datetime, format_date
from flask.ext.security import (
    http_auth_required,
    login_required,
    roles_accepted,
)
from markdown import markdown
from sqlalchemy.orm.exc import NoResultFound

import lost_tracker.core as loco
import lost_tracker.models as mdl
from lost_tracker import __version__
from lost_tracker.const import TABULAR_PREFIX


ROOT = Blueprint('root', __name__)


@ROOT.before_app_first_request
def create_admin_user():
    user = current_app.user_datastore.create_user(
        email='admin@example.com',
        password='admin',
        active=True)
    admin_role = mdl.Role(name=mdl.Role.ADMIN)
    user.roles = [admin_role]
    try:
        mdl.DB.session.commit()
    except Exception as exc:
        current_app.logger.debug(str(exc))
        mdl.DB.session.rollback()


@ROOT.before_app_request
def before_request():
    # Only set this if the argument is present (which means the user wants to
    # change the language)
    if 'lang' in request.args:
        current_app.logger.debug('Changing locale to {}'.format(
            request.args['lang']))
        flask_session['lang'] = request.args['lang']


@ROOT.teardown_app_request
def teardown_request(exc):
    try:
        mdl.DB.session.commit()
    except Exception:
        mdl.DB.session.rollback()
        current_app.logger.exception(exc)


@ROOT.app_context_processor
def inject_context():
    registration_open = mdl.Setting.get('registration_open', default=False)
    event_date = mdl.Setting.get('event_date', None)
    location_display = mdl.Setting.get('event_location', '')
    coords = mdl.Setting.get('location_coords', '')
    if event_date and event_date >= datetime.now().date():
        date_display = format_date(event_date, format='long')
    else:
        date_display = ''
        location_display = ''
        coords = ''

    return dict(
        Role=mdl.Role,
        Setting=mdl.Setting,
        __version__=__version__,
        date_display=date_display,
        localconf=current_app.localconf,
        location_coords=coords,
        location_display=location_display,
        registration_open=registration_open,
        tabular_prefix=TABULAR_PREFIX,
    )


@ROOT.app_errorhandler(NoResultFound)
def error_handler(request):
    return gettext('No such entity!'), 404


@ROOT.app_template_filter('md')
def convert_markdown(value):
    return markdown(value, safe_mode='replace', enable_attributes=False)


@ROOT.app_template_filter('humantime')
def humanize_time(value):
    return format_datetime(value, format='d. MMM Y k:s')


# ------ Routes ---------------------------------------------------------------


@ROOT.route('/')
def index():
    return render_template('index.html')


@ROOT.route('/where')
def where():
    return render_template('where.html')


@ROOT.route('/misc')
def misc():
    return render_template('misc.html')


@ROOT.route('/matrix')
def matrix():
    stations = mdl.Station.all()
    groups = mdl.Group.all()
    state_matrix = loco.Matrix(stations, groups)
    return render_template('matrix.html',
                           matrix=state_matrix,
                           stations=stations)


@ROOT.route('/advance/<groupId>/<station_id>')
@login_required
def advance(groupId, station_id):
    new_state = mdl.advance(mdl.DB.session, groupId, station_id)
    return jsonify(
        group_id=groupId,
        station_id=station_id,
        new_state=new_state)


@ROOT.route('/scoreboard')
def scoreboard():
    result = sorted(mdl.score_totals(), key=attrgetter('score_sum'),
                    reverse=True)
    output = []
    pos = 1
    for row in result:
        group = mdl.Group.one(id=row.group_id)
        output.append([pos, group.name, row.score_sum, group.completed])
        pos += 1
    return render_template('scoreboard.html', scores=output)


@ROOT.route('/slot_editor')
@roles_accepted(mdl.Role.ADMIN)
def slot_editor():
    groups = mdl.Group.all()
    slots = mdl.TimeSlot.all()

    groups_a = {}
    groups_b = {}
    for group in groups:
        try:
            if group.start_time and group.direction == mdl.DIR_A:
                groups_a[mdl.TimeSlot(group.start_time)] = group
            elif group.start_time and group.direction == mdl.DIR_B:
                groups_b[mdl.TimeSlot(group.start_time)] = group
        except ValueError as exc:
            current_app.logger.warning(exc)
            group.start_time = None

    groups_none = sorted([_ for _ in groups
                          if not _.start_time or _.direction not in (
                              mdl.DIR_A, mdl.DIR_B)],
                         key=lambda x: x.name)

    return render_template('slot_editor.html',
                           slots=slots,
                           dir_a=mdl.DIR_A,
                           dir_b=mdl.DIR_B,
                           groups_a=groups_a,
                           groups_b=groups_b,
                           groups_none=groups_none,
                           stats=loco.stats())


@ROOT.route('/js-fragment/group-tooltip/<int:group_id>')
def group_tooltip(group_id):
    group = mdl.Group.one(id=group_id)
    return render_template('group-tooltip.html',
                           group=group)


@ROOT.route('/station/<int:id>', methods=['DELETE'])
@roles_accepted(mdl.Role.ADMIN)
def delete_station(id):
    loco.delete_station(id)
    return jsonify(status='ok')


@ROOT.route('/settings')
@roles_accepted(mdl.Role.ADMIN)
def settings():
    settings = {stng.key: stng.value
                for stng in mdl.Setting.all(mdl.DB.session)}
    return render_template('settings.html', settings=settings)


@ROOT.route('/settings', methods=['POST'])
@login_required
def save_settings():
    helpdesk = request.form.get('helpdesk', '')
    registration_open = request.form.get('registration_open', '') == 'on'
    shout = request.form.get('shout', '')
    event_date = request.form.get('event_date', '')
    event_date = datetime.strptime(event_date, '%Y-%m-%d').date() if event_date else None  # NOQA
    event_location = request.form.get('event_location', '')
    location_coords = request.form.get('location_coords', '')

    mdl.Setting.put(mdl.DB.session, 'helpdesk', helpdesk)
    mdl.Setting.put(mdl.DB.session, 'registration_open', registration_open)
    mdl.Setting.put(mdl.DB.session, 'shout', shout)
    mdl.Setting.put(mdl.DB.session, 'event_date', event_date)
    mdl.Setting.put(mdl.DB.session, 'event_location', event_location)
    mdl.Setting.put(mdl.DB.session, 'location_coords', location_coords)
    flash(gettext('Settings successfully saved.'), 'info')
    return redirect(url_for(".settings"))


@ROOT.route('/group_state/<group>/<station>', methods=['PUT'])
@http_auth_required('lostlu')
def update_group_station_state(group, station):
    """
    Required by the android client.
    """
    group = unquote_plus(group)
    station = unquote_plus(station)
    try:
        form_score = request.json['form']
        station_score = request.json['station']
        station_state = request.json['state']
    except LookupError:
        return jsonify({'message': 'Missing value'}), 400

    loco.set_score(mdl.DB.session, group, station, station_score, form_score,
                   station_state)

    return jsonify(
        name=group,
        form_score=form_score,
        score=station_score,
        state=station_state,
        station_name=station)


@ROOT.route('/profile', methods=['GET', 'DELETE'])
@login_required
def profile():
    social = current_app.extensions['social']
    return render_template(
        'profile.html',
        content='Profile Page',
        twitter_conn=social.twitter.get_connection() if social.twitter else None,  # NOQA
        facebook_conn=social.facebook.get_connection() if social.facebook else None,  # NOQA
        google_conn=social.google.get_connection() if social.google else None)
