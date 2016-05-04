from collections import namedtuple
from datetime import datetime, timedelta
from os.path import exists
from stat import S_ISREG, ST_CTIME, ST_MODE
import logging
import mimetypes
import os
import os.path
try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus  # NOQA

from lost_tracker.util import start_time_to_order
from lost_tracker.models import (
    DB,
    DIR_A,
    DIR_B,
    Form,
    Group,
    GroupStation,
    Message,
    Role,
    STATE_ARRIVED,
    STATE_FINISHED,
    STATE_UNKNOWN,
    Setting,
    Station,
    TimeSlot,
    User,
    _get_unique_order,
)

from pytz import timezone
from sqlalchemy import and_, update  # TODO this module should have no SA
from sqlalchemy import func  # TODO this module should have no SA
from sqlalchemy.exc import IntegrityError  # TODO this module should have no SA

LOG = logging.getLogger(__name__)
WEB_IMAGES = {
    'image/jpeg',
    'image/png',
}

MatrixSum = namedtuple('MatrixSum', 'unknown arrived completed')


def _generate_state_list(station):
    """
    Generates a simple Python dictionary with current group "states".
    """
    if not station:
        return []
    groups = Group.all().order_by(Group.order)
    state_info = DB.session.query(GroupStation).filter(
        GroupStation.station == station)
    state_info_map = {state.group: state for state in state_info}
    output = []
    for group in groups:
        si = state_info_map.get(group)
        output.append({
            "stationId": si.station_id if si else 0,
            "groupId": group.id,
            "groupName": group.name,
            "formScore": (si.form_score or 0) if si else 0,
            "stationScore": (si.score or 0) if si else 0,
            "state": si.state if si else 0
        })
    output = sorted(output, key=lambda x: (x['state'], x['groupName']))
    return output


def _dashboard_order(element):
    """
    Given a dashboard element, this function returns a comparable value used for
    ordering the small sidebar elements in the dashboard.
    """
    if element is None or element.state is None:
        return 3
    elif element.state == STATE_FINISHED:
        return 0
    elif element.state == STATE_ARRIVED:
        return 1
    elif element.state == STATE_UNKNOWN:
        return 2
    elif element.group.cancelled:
        return 80
    else:
        return 99


def _main_dashboard_order(element):
    """
    Given a dashboard element, this function returns a comparable value used for
    ordering the main elements in the dashboard.
    """
    if element is None or element.state is None:
        return "%d%s" % (3, element.group.name)
    elif element.state == STATE_FINISHED:
        return "%d%s" % (90, element.group.name)
    elif element.state == STATE_ARRIVED:
        return "%d%s" % (1, element.group.name)
    elif element.state == STATE_UNKNOWN:
        return "%d%s" % (2, element.group.name)
    elif element.group.cancelled:
        return "%d%s" % (80, element.group.name)
    else:
        return "%d%s" % (99, element.group.name)


class Matrix(object):
    """
    Returns a 2-dimensional array containing an entry for each group.

    Each row has the group as first element, and all stations as subsequent
    elements. For example::

        [
            [group1, station1, station2, station3, ... ],
            [group2, station1, station2, station3, ... ],
            [group3, station1, station2, station3, ... ],
            ...
        ]
    """

    def __init__(self, stations, groups):
        self._stations = stations
        self._groups = groups
        self._matrix = []

        for group in groups:
            tmp = [group]
            for station in stations:
                tmp.append(GroupStation.get(group.id, station.id))
            self._matrix.append(tmp)

    def __iter__(self):
        return iter(self._matrix)

    @property
    def sums(self):
        """
        Creates a list where each element contains the sum of "unknown",
        "arrived" and "completed" states for each station.
        """
        if not self._matrix:
            return []
        sums = [[0, 0, 0] for _ in self._matrix[0][1:]]
        for row in self._matrix:
            for i, state in enumerate(row[1:]):
                if not state:
                    sums[i][STATE_UNKNOWN] += 1
                    continue

                if state.state == STATE_UNKNOWN:
                    sums[i][STATE_UNKNOWN] += 1
                elif state.state == STATE_ARRIVED:
                    sums[i][STATE_ARRIVED] += 1
                elif state.state == STATE_FINISHED:
                    sums[i][STATE_FINISHED] += 1
        # Wrap in named-tuples for readability
        return [MatrixSum(*sum) for sum in sums]


def add_group(grp_name, contact, phone, direction, start_time, session):
    """
    Creates a new group in the database.
    """

    if direction not in (DIR_A, DIR_B):
        raise ValueError('{0!r} is not among the supported values '
                         'for "direction" which are: {1!r}, {2!r}'.format(
                             direction, DIR_A, DIR_B))

    new_grp = Group(grp_name, contact, phone, direction, start_time)
    session.add(new_grp)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        LOG.exception('Error while adding the new group {0}'.format(
            grp_name))
        raise ValueError('Error while adding the new group {0}'.format(
            grp_name))

    return ("Group {0} with Contact {1} / {2} was successfully added into the "
            "DB. The given start-time is {3} and the direction is {4}".format(
                grp_name,
                contact,
                phone,
                start_time,
                direction))


def add_station(stat_name, contact, phone, order, session):
    """
    Creates a new :py:class:`Station` in the database.
    """
    order = _get_unique_order(Station, order)
    new_station = Station(stat_name, contact, phone)
    new_station.order = order
    session.add(new_station)
    return "Station {0} added. Contact: {1} / {2}".format(
        stat_name, contact, phone)


def add_form(session, name, max_score, order=0):
    """
    Adds a new Form to the database.
    """
    order = _get_unique_order(Form, order)
    new_form = Form(name, max_score, order)
    session.add(new_form)
    return new_form


def store_registration(mailer, session, data):
    """
    Stores a registration to the database.

    The *data* dictionary contains the following items (all strings):

        * group_name
        * contact_name
        * email
        * tel
        * time: The time of day that the group begins the "run".
        * comments
        * num_vegetarians
        * num_participants
        * user_id: The ID of the user that made the registration
    """
    qry = Group.query.filter_by(name=data['group_name'])
    check = qry.first()
    if check:
        raise ValueError('Group {} already registered'.format(
            data['group_name']))
    else:
        key = os.urandom(50).encode('base64').replace('/', '')[0:20]
        # Regenerate keys if needed (just in case to avoid duplicates).
        qry = Group.query.filter_by(confirmation_key=key)
        check_key = qry.first()
        while check_key:
            key = os.urandom(50).encode('base64').replace('/', '')[0:20]
            qry = Group.query.filter_by(confirmation_key=key)
            check_key = qry.first()

        new_grp = Group(data['group_name'],
                        data['contact_name'],
                        data['tel'],
                        None,
                        data['time'],
                        data['comments'],
                        key,
                        data['user_id'])
        order = start_time_to_order(data['time'])
        new_grp.order = _get_unique_order(Group, order)
        new_grp.num_vegetarians = int(data['num_vegetarians'])
        new_grp.num_participants = int(data['num_participants'])
        new_grp.email = data['email']

        session.add(new_grp)
        try:
            session.flush()
        except IntegrityError:
            session.rollback()
            LOG.exception('Error while adding the new group {0}'.format(
                data['group_name']))
            raise ValueError('Error while adding the new group {0}'.format(
                data['group_name']))

        return key


def confirm_registration(mailer, key, activation_url):
    """
    OBSOLETE: This step is obsolete since we now have social logins. This was a
              measure to prevent spam. Requireing social logins removes this
              issue. Email notifications have already been removed!

    If a user received a confirmation e-mail, this method will be called if the
    user clicks the confirmation key. The registration is put into 'pending'
    state and e-mails will be sent to the people who manage the event
    registrations. This e-mail will contain an "accept" link with the same
    key. Managers need to verify all the data (start time, available time
    slots, user comments).
    """
    query = Group.query.filter(Group.confirmation_key == key)
    grp = query.first()

    if grp:
        if grp.is_confirmed:
            # Group is already confirmed. Don't process it further (no
            # additional mails will be sent).
            LOG.debug('Duplicate confirmation ignored.')
            return True

        grp.is_confirmed = True
        admin_query = Role.query.filter(Role.name == Role.ADMIN)
        if admin_query.count():
            mails = [(user.email, user.name) for user in admin_query[0].user]
            mailer.send('registration_check',
                        to=mails,
                        data={
                            'group': grp,
                            'activation_url': activation_url
                        })

        return True

    else:
        raise ValueError('Given key not found in DB')


def accept_registration(mailer, key, group):
    """
    This method is called if a staff-member clicked the "accept" link, an e-mail
    is sent out to the reservation contact telling them all is done. The
    registration is marked as 'accepted'.
    """

    if not group:
        return False

    if group.accepted:
        return False

    group.accepted = True

    mailer.send('welcome',
                to=[(group.user.email, group.name)],
                data={
                    'group': group
                })
    return True


def update_group(mailer, id, data):
    """
    Updates an existing group.
    """
    registration_open = Setting.get('registration_open', False)

    group = Group.one(id=id)
    group.name = data['name']
    group.phone = data['phone']
    group.comments = data['comments']
    group.contact = data['contact']
    group.email = data['email']

    # Only allow the number of participants to change as long as the
    # registration is open!
    if data['user_is_admin'] or registration_open:
        group.num_vegetarians = data['num_vegetarians']
        group.num_participants = data['num_participants']

    if 'direction' in data:
        group.direction = data['direction']

    if 'start_time' in data:
        group.start_time = data['start_time']

    if 'cancelled' in data:
        group.cancelled = data['cancelled']

    if 'completed' in data:
        group.completed = data['completed']

    send_email = data.get('send_email', True)
    if data['notification_recipient'] == 'admins':
        admin_query = Role.query.filter(Role.name == Role.ADMIN)
        if admin_query.count():
            recipients = [(user.email, user.name)
                          for user in admin_query[0].user]
        else:
            recipients = []
    elif data['notification_recipient'] == 'owner':
        recipients = [(group.user.email, data['contact'])]
    else:
        LOG.warning('Got an unexpected mail recipient hint: %r',
                    data['notification_recipient'])

    if send_email and recipients:
        mailer.send('registration_update',
                    to=recipients,
                    data={
                        'group': group
                    })
    else:
        LOG.debug('No mail sent: vars=%r', locals())


def auth(login, password):
    """
    Verify login/password pair. Returns True on match, False otherwise.
    """
    query = User.query.filter(and_(
        User.login == login,
        User.password == password))
    user = query.first()
    if user:
        return True
    else:
        return False


def get_user(login):
    """
    Returns a "User" instance (can be anything). It should never raise an
    exception. If the user-id is invalid/not know it should return ``None``.

    The returnes User instance needs to only follow the prerequisites mentioned
    at https://flask-login.readthedocs.org/en/latest/#your-user-class
    """
    query = User.query.filter(
        User.login == login)
    user = query.first()
    if user:
        return user
    else:
        return None


def delete_group(id):
    Group.query.filter(Group.id == id).delete()


def delete_station(id):
    Station.query.filter(Station.id == id).delete()


def delete_form(id):
    Form.query.filter(Form.id == id).delete()


def stats(conf):
    """
    Fetch some basic stats from the system.
    """
    num_groups = Group.all().count()
    num_slots = len(TimeSlot.all(conf)) * 2  # DIR_A and DIR_B
    return {
        'groups': num_groups,
        'slots': num_slots,
        'free_slots': num_slots - num_groups,
        'load': float(num_groups) / num_slots
    }


def get_local_photos(conf, url_generator):
    """
    Return a collection of photos from the local files. Return a dictionary with
    two keys: *title* and *photos*.

    *photos* contains URLs to the photos.
    """
    path = conf.get('app', 'photo_folder', default='')
    if not path or not exists(path):
        return {}

    if not mimetypes.inited:
        mimetypes.init()

    entries = (os.path.join(path, fn) for fn in os.listdir(path))
    entries = ((os.stat(path), path) for path in entries)
    entries = ((stat[ST_CTIME], path)
               for stat, path in entries if S_ISREG(stat[ST_MODE]))

    photos = []
    for cdate, filename in sorted(entries, reverse=True):
        mtype, mtype_encoding = mimetypes.guess_type(filename)
        if mtype in WEB_IMAGES:
            photos.append(url_generator(os.path.basename(filename)))

    return {
        'title': 'Photos',
        'photos': photos
    }


def set_score(session, group_id, station_id, station_score, form_score,
              state=None):
    GroupStation.set_score(session, group_id, station_id, station_score,
                           form_score, state)
    return 'OK'


def get_dashboard(station):
    """
    Retrieves dashboard information for a given station. The dashboard contains
    the states for each group at that station, and incoming groups from
    neighbouring stations.
    """
    station = Station.by_name_or_id(station)

    neighbours = station.neighbours
    main_states = GroupStation.by_station(station)

    # Add missing groups to the main states because the UI should list them all.
    # Even if no scores have been reported yet.
    missing_groups = Group.query.filter(~Group.id.in_([
        row.group_id for row in main_states]))
    main_states.extend([GroupStation(group.id, station.id)
                        for group in missing_groups])

    # remove states from cancelled/abandoned groups
    main_states = [state for state in main_states
                   if state.group and not state.group.cancelled]

    time_threshold = datetime.now(
        timezone('Europe/Luxembourg')) - timedelta(minutes=45)
    before_states = sorted(
        GroupStation.by_station(neighbours['before']),
        key=_dashboard_order)
    before_states = [state for state in before_states
                     if state.updated > time_threshold]
    after_states = sorted(
        GroupStation.by_station(neighbours['after']),
        key=_dashboard_order)
    after_states = [state for state in after_states
                    if state.updated > time_threshold]
    main_states = sorted(main_states, key=_main_dashboard_order)
    finished_groups = {value.group_id for value in main_states
                       if value.state == STATE_FINISHED}
    before_states = [value for value in before_states
                     if value.group_id not in finished_groups]
    after_states = [value for value in after_states
                    if value.group_id not in finished_groups]
    output = dict(
        station=station,
        neighbours=neighbours,
        main_states=main_states,
        before_states=before_states,
        after_states=after_states,
    )
    return output


def delete_message(message):
    DB.session.delete(message)
    DB.session.commit()


def store_message(session, mailer, group, user, content, url):
    """
    Stores a new message in the group's message stream.
    """
    msg = Message(
        content=content,
        user=user,
        group=group,
    )
    session.add(msg)
    session.commit()

    # Send out mail notifications
    admins = set(User.by_role(Role.ADMIN))
    recipients = admins | set([group.user])
    mailer.send('new_message',
                to=recipients,
                data={
                    'author': user,
                    'content': content,
                    'group': group,
                    'url': url,
                })
    return msg


def set_group_state(session, group_id, station_id, new_state):
    """
    Updates the group state for a given station
    """
    station = session.query(Station).filter_by(id=station_id).first()
    if not station:
        LOG.debug('No station found with ID %r', station_id)
        return False

    group = session.query(Group).filter_by(id=group_id).first()
    if not group:
        LOG.debug('No group found with ID %r', group_id)
        return False

    if not group.departure_time and station.is_start and new_state == STATE_FINISHED:
        group.departure_time = func.now()

    state = GroupStation(
        group_id=group_id,
        station_id=station_id,
        state=new_state)
    state = session.merge(state)
    session.flush()
    return state


def get_stations(session):
    return session.query(Station).order_by(Station.order)


def save_station(session, data):
    """
    Add or update a station in the DB.
    """
    # If this station is set to "start", we must remove that flag from all other
    # stations. We'll just set them all to False, then update the given station
    # with True. This ensures that we only have one starting station.
    if data.get('is_start'):
        session.execute(update(Station).values(is_start=False))

    # Ensure we don't have duplicate values for the "order" field
    same_order = session.query(Station).filter(and_(
        Station.order == data['order'],
        Station.id != data['id'])).first()
    while same_order:  # As long as we have a matching entry, increment by 1
        data['order'] += 1
        same_order = session.query(Station).filter(and_(
            Station.order == data['order'],
            Station.id != data['id'])).first()

    station = Station(
        name=data['name'],
        contact=data['contact'],
        phone=data['phone'],
    )
    station.id = data.get('id')
    station.order = data['order']
    station.is_start = data['is_start']
    merged = session.merge(station)
    DB.session.commit()
    return merged
