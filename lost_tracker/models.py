from collections import namedtuple
from datetime import datetime
from json import loads, dumps
import logging

from flask.ext.security import UserMixin, RoleMixin
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    Unicode,
    and_,
    func,
)
from sqlalchemy.orm import relationship, backref
from lost_tracker.util import start_time_to_order

STATE_UNKNOWN = 0
STATE_ARRIVED = 1
STATE_FINISHED = 2

DIR_A = 'Giel'
DIR_B = 'Roud'

DATE_FORMAT = '%Y-%m-%d'


DB = SQLAlchemy()
LOG = logging.getLogger(__name__)


form_scores = DB.Table(
    'form_scores',
    Column('group_id', Integer, ForeignKey('group.id')),
    Column('form_id', Integer, ForeignKey('form.id')),
    Column('score', Integer, default=0),
    PrimaryKeyConstraint('group_id', 'form_id'))


def _get_unique_order(cls, current_value):
    """
    Retrieves a unique "order" value for an entity. If the given value exists,
    it repeatedly augments the value by ``1`` until an unused value is found.

    We must ensure that the order is uniqe because of the recent addition to the
    "dashboard" which contains pointers from one station to the next and
    previous station. If "order" is not unique, that query becomes
    non-deterministic!
    """
    existing_slot = cls.one(order=current_value)
    order = current_value
    while existing_slot:
        order = order + 1
        existing_slot = cls.one(order=order)
    return order


def custom_json_serializer(value):
    if isinstance(value, datetime):
        return value.strftime(DATE_FORMAT)
    else:
        raise TypeError('Cannot serialize {!r} to JSON'.format(value))


def score_totals():
    score_result = namedtuple('ScoreResult',
                              'group_id, score_sum, ppm')

    query = GroupStation.query
    group_scores = {}
    for row in query:
        station_score = row.score or 0
        form_score = row.form_score or 0
        group_scores.setdefault(row.group, 0)
        group_scores[row.group] += (station_score + form_score)

    output = []
    for group in group_scores:
        if group.departure_time:
            interval = datetime.now() - group.departure_time
            minutes_since_start = interval.total_seconds() / 60
            ppm = group_scores[group] / minutes_since_start
        else:
            ppm = 0
        output.append(score_result(group.id, group_scores[group], ppm))

    return output


def advance(session, group_id, station_id):
    state = GroupStation.get(group_id, station_id)

    # The first state to set - if there is nothing yet - is "ARRIVED"
    if not state:
        group = Group.one(id=group_id)
        station = Station.one(id=station_id)
        if not group.departure_time and station.is_start:
            group.departure_time = func.now()
        state = GroupStation(group_id, station_id)
        state.state = STATE_ARRIVED
        session.add(state)
        return STATE_ARRIVED

    group = state.group
    station = state.station

    if state.state == STATE_UNKNOWN:
        if not group.departure_time and station.is_start:
            group.departure_time = func.now()
        state.state = STATE_ARRIVED
    elif state.state == STATE_ARRIVED:
        state.state = STATE_FINISHED
    elif state.state == STATE_FINISHED:
        state.state = STATE_UNKNOWN
    else:
        raise ValueError('%r is not a valid state!' % state.state)

    return state.state


class Group(DB.Model):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    order = Column(Integer, unique=True)
    cancelled = Column(Boolean, default=False, server_default='false')
    contact = Column(Unicode(50))
    phone = Column(Unicode(20))
    direction = Column(Unicode)
    _start_time = Column(Unicode(5), name="start_time")
    comments = Column(Unicode)
    user_id = Column(Integer, ForeignKey('user.id'))
    is_confirmed = Column(Boolean, server_default='false', default=False)
    confirmation_key = Column(Unicode(20), unique=True)
    accepted = Column(Boolean, server_default='false', default=False)
    completed = Column(Boolean, server_default='false', default=False)
    inserted = Column(DateTime, server_default=func.now(), default=func.now())
    updated = Column(DateTime)
    departure_time = Column(DateTime, server_default=None, default=None)

    user = relationship('User', backref="groups")
    stations = relationship('GroupStation')
    messages = relationship('Message', backref="group",
                            order_by='Message.inserted')

    def __init__(self,
                 name=None,
                 contact=None,
                 phone=None,
                 direction=None,
                 start_time=None,
                 comments=None,
                 confirmation_key=None,
                 user_id=None):
        self.name = name
        self.contact = contact
        self.phone = phone
        self.direction = direction
        self.start_time = start_time
        self.comments = comments
        self.confirmation_key = confirmation_key
        self.user_id = user_id

    def __repr__(self):
        return '<Group %r>' % (self.name)

    def __str__(self):
        return self.name

    @staticmethod
    def all():
        groups = Group.query
        groups = groups.order_by(Group.order)
        return groups

    @staticmethod
    def one(**filters):
        """
        Returns a group from the database as :py:class:`Group` instance.

        Currently the following filters are supported:

        ``id``
            The primary key.

        ``name``
            Another unique key.

        ``key``
            The registration confirmation key
        """
        group = Group.query
        if 'id' in filters:
            group = group.filter_by(id=filters['id'])
        elif 'name' in filters:
            group = group.filter_by(name=filters['name'])
        elif 'key' in filters:
            group = group.filter_by(confirmation_key=filters['key'])
        elif 'order' in filters:
            group = group.filter_by(order=filters['order'])
        else:
            raise ValueError('Unsupported Unique Field!')
        group = group.first()
        return group

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, value):
        self._start_time = value
        if value:
            self.order = _get_unique_order(Group, start_time_to_order(value))
        else:
            self.order = _get_unique_order(Group, 0)

    def to_dict(self):
        return {
            '__class__': 'Group',
            'id': self.id,
            'name': self.name,
            'order': self.order,
            'cancelled': self.cancelled,
            'contact': self.contact,
            'phone': self.phone,
            'direction': self.direction,
            'start_time': self._start_time,
            'comments': self.comments,
            'is_confirmed': self.is_confirmed,
            'accepted': self.accepted,
            'completed': self.completed,
        }


class Station(DB.Model):
    __tablename__ = 'station'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    order = Column(Integer, unique=True)
    contact = Column(Unicode(50))
    phone = Column(Unicode(20))
    is_start = Column(Boolean, default=False)

    groups = relationship('GroupStation')

    def __init__(self, name=None, contact=None, phone=None):
        self.name = name
        self.contact = contact
        self.phone = phone

    def __repr__(self):
        return '<Station %r>' % (self.name)

    @staticmethod
    def all():
        """
        Returns all stations from the database as :py:class:`Station` instances.
        """
        stations = Station.query
        stations = stations.order_by(Station.order)
        return stations

    @staticmethod
    def one(**filters):
        """
        Returns a :py:class:`Station` by class name. Can be ``None`` if no
        matching station is found.
        """
        qry = Station.query
        if 'id' in filters:
            qry = qry.filter_by(id=filters['id'])
        elif 'name' in filters:
            qry = qry.filter_by(name=filters['name'])
        qry = qry.first()
        return qry

    def to_dict(self):
        return {
            '__class__': 'Station',
            'id': self.id,
            'name': self.name
        }

    @property
    def before(self):
        """
        Returns the station immediately before this one (using the "order"
        field).

        Note that the "order" field should be unique for this to be
        deterministic!
        """
        query = Station.query
        query = query.order_by(Station.order)
        query = query.filter(Station.order < self.order)
        query = query.limit(1)
        return query.first()

    @property
    def after(self):
        """
        Returns the station immediately after this one (using the "order" field)

        Note that the "order" field should be unique for this to be
        deterministic!
        """
        query = Station.query
        query = query.order_by(Station.order)
        query = query.filter(Station.order > self.order)
        query = query.limit(1)
        return query.first()


class Form(DB.Model):
    __tablename__ = 'form'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(20))
    max_score = Column(Integer)
    order = Column(Integer, nullable=False, unique=True, default=0)

    def __init__(self, name=None, max_score=100, order=0):
        self.name = name
        self.max_score = max_score
        self.order = _get_unique_order(Form, order)

    def __repr__(self):
        return '<Form %r>' % (self.name)

    @staticmethod
    def all():
        """
        Returns all forms from the database as :py:class`Form` instances.
        """
        forms = Form.query
        forms = forms.order_by(Form.order)
        return forms

    def to_dict(self):
        return {
            '__class__': 'Form',
            'id': self.id
        }


class Setting(DB.Model):
    __tablename__ = 'settings'
    key = Column(Unicode(20), primary_key=True)
    value_ = Column('value', Unicode())
    description = Column('description', Unicode())

    # Allow simple conversions for saved values.
    TYPECONVERSION = {
        'event_date': (
            lambda val: datetime.strptime(val, '%Y-%m-%d').date() if val else None,  # NOQA
            lambda val: val.strftime('%Y-%m-%d') if val else ''
        )
    }

    def __init__(self, key, value):
        self.key = key
        self.value_ = dumps(value, default=custom_json_serializer)
        self.description = ''

    def __repr__(self):
        return 'Setting({!r}, {!r})'.format(self.key, self.value)

    @property
    def value(self):
        value = loads(self.value_)
        if isinstance(value, str) and '-' in value:
            try:
                value = datetime.strptime(loads(self.value_), DATE_FORMAT)
            except ValueError:
                value = 'Unknown Value'
        return value

    @value.setter
    def value(self, new_value):
        self.value_ = dumps(new_value, default=custom_json_serializer)

    @staticmethod
    def get(key, default=None):
        query = Setting.query.filter(Setting.key == key)
        row = query.first()
        if not row:
            new_row = Setting.put(DB.session, key, default)
            output = new_row.value
        else:
            output = row.value

        convert_outof_db, _ = Setting.TYPECONVERSION.get(
            key, (lambda x: x, None))
        return convert_outof_db(output)

    @staticmethod
    def put(session, key, value):
        _, convert_into_db = Setting.TYPECONVERSION.get(
            key, (None, lambda x: x))
        row = Setting(key, convert_into_db(value))
        new_row = session.merge(row)
        session.add(new_row)
        return new_row

    @staticmethod
    def all(session):
        return session.query(Setting)


class GroupStation(DB.Model):
    __tablename__ = 'group_station_state'

    group_id = Column(Integer, ForeignKey('group.id'), primary_key=True)
    station_id = Column(Integer, ForeignKey('station.id'), primary_key=True)
    state = Column(Integer, default=STATE_UNKNOWN)
    score = Column(Integer, nullable=True, default=None)
    form_score = Column(Integer, nullable=True, default=None)

    group = relationship("Group")
    station = relationship("Station")

    def __init__(self, group_id, station_id, state=STATE_UNKNOWN):
        self.group_id = group_id
        self.station_id = station_id
        self.state = state

    @staticmethod
    def get(group_id, station_id):
        """
        Given a group and station ID this will return the  state of the given
        group at the given station. If no the group does not have a state at
        that station, the default state (STATE_UNKNOWN) is returned.

        :param group_id: The group ID
        :type group_id: int
        :param station_id: The station ID
        :type station_id: int
        :return: The state
        :rtype: int
        """
        query = GroupStation.query.filter(and_(
            GroupStation.group_id == group_id,
            GroupStation.station_id == station_id))
        return query.first()

    @staticmethod
    def set_score(session, group_id, station_id, station_score, form_score,
                  state=None):

        if isinstance(group_id, (str, unicode)):
            group = Group.query.filter_by(name=group_id).one()
        else:
            group = Group.query.filter_by(id=group_id).one()

        if isinstance(station_id, (str, unicode)):
            station = Station.query.filter_by(name=station_id).one()
        else:
            station = Station.query.filter_by(id=station_id).one()

        query = GroupStation.query.filter(and_(
            GroupStation.group_id == group.id,
            GroupStation.station_id == station.id))

        if not group.departure_time and station.is_start and state == STATE_ARRIVED:
            group.departure_time = func.now()

        row = query.first()
        if not row:
            gs = GroupStation(group.id, station.id)
            gs.score = station_score
            gs.form_score = form_score
            if state:
                gs.state = state
            session.add(gs)
        else:
            row.score = station_score
            row.form_score = form_score
            if state:
                row.state = state

    def to_dict(self):
        return {
            '__class__': 'GroupStation',
            'group_id': self.group_id,
            'station_id': self.station_id,
            'state': self.state,
            'score': self.score,
            'form_score': self.form_score,
        }


class TimeSlot(object):

    def __init__(self, time):
        supported_formats = ['%Hh%M', '%H:%M']
        self.time = None
        if not time or time == 'None':
            return

        for fmt in supported_formats:
            try:
                self.time = datetime.strptime(time, fmt)
            except:
                pass

        if time and not self.time:
            raise ValueError('time data {!r} does not match any known '
                             'formats {!r}'.format(time, supported_formats))

    def __eq__(self, other):
        return isinstance(other, TimeSlot) and other.time == self.time

    def __hash__(self):
        return hash(self.time)

    @staticmethod
    def all(conf):
        slots_raw = conf.get('app', 'time_slots', default='')
        slots = slots_raw.splitlines()
        if slots:
            return [TimeSlot(line.strip()) for line in slots if line.strip()]
        else:
            return [
                TimeSlot('18h50'),
                TimeSlot('19h00'),
                TimeSlot('19h10'),
                TimeSlot('19h20'),
                TimeSlot('19h30'),
                TimeSlot('19h40'),
                TimeSlot('19h50'),
                TimeSlot('20h00'),
                TimeSlot('20h10'),
                TimeSlot('20h20'),
                TimeSlot('20h30'),
                TimeSlot('20h40'),
                TimeSlot('20h50'),
                TimeSlot('21h00'),
                TimeSlot('21h10'),
                TimeSlot('21h20'),
                TimeSlot('21h30'),
                TimeSlot('21h40'),
                TimeSlot('21h50'),
                TimeSlot('22h00'),
            ]


class Message(DB.Model):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    content = Column(Unicode)
    user_id = Column(Integer, ForeignKey('user.id'))
    group_id = Column(Integer, ForeignKey('group.id'))
    inserted = Column(DateTime, server_default=func.now(), default=func.now())
    updated = Column(DateTime)

    @staticmethod
    def get(id):
        return Message.query.get(id)


roles_users = DB.Table(
    'roles_users',
    Column('user', Integer(), ForeignKey('user.id')),
    Column('role', Integer(), ForeignKey('role.id')))


class Role(DB.Model, RoleMixin):
    __tablename__ = 'role'

    ADMIN = 'admin'
    STAFF = 'staff'

    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(80), unique=True)
    description = Column(Unicode(255))


class User(DB.Model, UserMixin):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    email = Column(Unicode(100), unique=True)
    name = Column(Unicode(100))
    password = Column(Unicode(100))
    locale = Column(Unicode(2))
    active = Column(Boolean())
    confirmed_at = Column(DateTime())
    roles = relationship('Role', secondary=roles_users,
                         backref=backref('user', lazy='dynamic'))
    messages = relationship('Message', backref="user",
                            order_by='Message.inserted')

    @staticmethod
    def by_role(role_name):
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            LOG.debug('Unknown role name: %r', role_name)
            return []

        query = DB.session.query(User).outerjoin(roles_users)
        query = query.filter(roles_users.c.role == role.id)
        return query

    def __repr__(self):
        return "<User #%d email=%r>" % (self.id, self.email)


class Connection(DB.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    provider_id = Column(Unicode(255))
    provider_user_id = Column(Unicode(255))
    access_token = Column(Unicode(255))
    secret = Column(Unicode(255))
    display_name = Column(Unicode(255))
    profile_url = Column(Unicode(512))
    image_url = Column(Unicode(512))
    rank = Column(Integer)

    user = relationship('User', backref='social_connections')

    def __init__(self, *args, **kwargs):
        self.user_id = kwargs['user_id']
        self.provider_id = kwargs['provider_id']
        self.provider_user_id = kwargs['provider_user_id']
        self.access_token = kwargs['access_token']
        self.secret = kwargs['secret']
        self.display_name = kwargs['display_name']
        self.profile_url = kwargs['profile_url']
        self.image_url = kwargs['image_url']
        self.rank = kwargs.get('rank')
