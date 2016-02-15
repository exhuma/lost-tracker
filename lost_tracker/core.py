from stat import S_ISREG, ST_CTIME, ST_MODE

from lost_tracker.emails import send
from lost_tracker.util import start_time_to_order
from lost_tracker.models import (
    DIR_A,
    DIR_B,
    Form,
    Group,
    GroupStation,
    STATE_ARRIVED,
    STATE_FINISHED,
    STATE_UNKNOWN,
    Station,
    TimeSlot,
    User,
)

from sqlalchemy import and_
from os.path import exists
from sqlalchemy.exc import IntegrityError
import logging
import mimetypes
import os
import os.path
import urllib.request, urllib.parse, urllib.error

LOG = logging.getLogger(__name__)
WEB_IMAGES = {
    'image/jpeg',
    'image/png',
}


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
    # TODO: make this a list of dicts or a list of namedtuples!

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
        "arrived" and "finished" states for each station.
        """
        # TODO: make this a list of namedtuples!
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
        return sums


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
    new_station = Station(stat_name, contact, phone)
    new_station.order = order
    session.add(new_station)
    return "Station {0} added. Contact: {1} / {2}".format(
        stat_name, contact, phone)


def add_form(session, name, max_score, order=0):
    new_form = Form(name, max_score, order)
    session.add(new_form)
    return new_form


def store_registration(session, data, url, needs_confirmation=True):
    """
    Stores a registration to the database.

    The *data* dictionary contains the following items (all strings):

        * group_name
        * contact_name
        * email
        * tel
        * time
        * comments

    If *needs_confirmation* is true (the default), this method will store the
    reservation as "not yet confirmed". An e-mail will be sent out to the
    address specified in the *email* field. The e-mail will contain a link to
    ``/confirm/<key>`` where ``<key`` is a randomly generated string.

    @franky: implement
    @franky: urllib.quote_plus(os.urandom(50).encode('base64')[0:30])
    @franky: See ``_external`` at
             http://flask.pocoo.org/docs/api/#flask.url_for
    @franky: The "key" should be unique in the DB. Generate new keys as long as
             duplicates are found in the DB.
    mailing with python: https://pypi.python.org/pypi/Envelopes/0.4
    """
    qry = Group.query.filter_by(name=data['group_name'])
    check = qry.first()
    if check:
        raise ValueError('Group {} already registered'.format(
            data['group_name']))
    else:
        key = os.urandom(50).encode('base64').replace('/', '')[0:20]
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
                        data['email'],
                        data['comments'],
                        key
                        )
        new_grp.order = start_time_to_order(data['time'])

        session.add(new_grp)
        try:
            session.flush()
        except IntegrityError:
            session.rollback()
            LOG.exception('Error while adding the new group {0}'.format(
                data['group_name']))
            raise ValueError('Error while adding the new group {0}'.format(
                data['group_name']))

        if needs_confirmation:
            confirm_link = '{}/{}'.format(url, urllib.parse.quote_plus(key))
            send('confirm',
                 to=(data['email'], data['contact_name']),
                 data={
                     'confirmation_link': confirm_link
                 })
        return True


def confirm_registration(key, activation_url):
    """
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

        query = User.query
        user = query.all()
        mails = []
        for line in user:
            mails.append(line.email)

        send('registration_check',
             to=mails,
             data={
                 'group': grp,
                 'activation_url': activation_url
             })
        return True

    else:
        raise ValueError('Given key not found in DB')


def accept_registration(key, data):
    """
    This method is called if a manager clicked the "accept" link, an e-mail is
    sent out to the reservation contact telling them all is done. The
    registration is marked as 'finalized'.

    @franky: implement
    """
    query = Group.query.filter(Group.confirmation_key == key)
    grp = query.first()

    if grp:
        if grp.finalized:
            raise ValueError('Registration already finalized')
        else:
            grp.finalized = True
            grp.direction = data['direction']
            grp.name = data['name']
            grp.phone = data['phone']
            grp.start_time = data['start_time']
            grp.comments = data['comments']
            grp.contact = data['contact']
            grp.email = data['email']
            send('welcome',
                 to=(grp.email, grp.name),
                 data={
                     'group': grp
                 })
            return True
    else:
        raise ValueError('Given key not found in DB')


def update_group(id, data, send_email=True):
    """
    Updates an existing group.
    """
    group = Group.one(id=id)
    group.direction = data['direction']
    group.name = data['name']
    group.phone = data['phone']
    group.start_time = data['start_time']
    group.comments = data['comments']
    group.contact = data['contact']
    group.email = data['email']

    if send_email:
        send('registration_update',
             to=(data['email'], data['contact']),
             data={
                 'group': group
             })


def auth(login, password):
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


def stats():
    num_groups = Group.all().count()
    num_slots = len(TimeSlot.all()) * 2  # DIR_A and DIR_B
    return {
        'groups': num_groups,
        'slots': num_slots,
        'free_slots': num_slots - num_groups,
        'load': float(num_groups) / num_slots
    }


def get_local_photos(conf, url_generator):
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
