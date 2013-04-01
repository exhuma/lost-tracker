from sqlalchemy import (Column, Integer, Unicode, ForeignKey, Table, and_,
                        Boolean)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import select
from lost_tracker.database import Base

STATE_UNKNOWN = 0
STATE_ARRIVED = 1
STATE_FINISHED = 2

group_station_state = Table(
    'group_station_state',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('group.id')),
    Column('station_id', Integer, ForeignKey('station.id')),
    Column('state', Integer, default=STATE_UNKNOWN))

station_scores = Table(
    'station_scores',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('group.id')),
    Column('station_id', Integer, ForeignKey('station.id')),
    Column('score', Integer, default=0))

form_scores = Table(
    'form_scores',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('group.id')),
    Column('form_id', Integer),
    Column('score', Integer, default=0))


def get_station_score(group_id, station_id):
    s = select([score],
               and_(
                   station_scores.c.group_id == group_id,
                   station_scores.c.station_id == station_id))
    return s.execute().first()


def get_station_score_by_station(station_id):
    s = select(
        [group_id, score],
        and_(
            station_scores.c.station_id == station_id
        )).order_by(station_scores.c.group_id)
    return s.execute()


def get_station_score_by_group(group_id):
    s = select(
        [station_id, score],
        and_(
            station_scores.c.group_id == group_id
        )).order_by(station_scores.c.station_id)
    return s.execute()


def get_station_score_full():
    s = select([station_scores]).order_by(station_scores.c.station_id)
    return s.execute()


def get_form_score(group_id, form_id):
    s = select(
        [score],
        and_(
            form_scores.c.group_id == group_id,
            form_scores.c.form_id == form_id
        ))
    return s.execute().first()


def get_form_score_by_group(group_id):
    s = select(
        [form_id, score],
        and_(
            form_scores.c.group_id == group_id,
        )).order_by(form_scores.c.form_id)
    return s.execute()


def get_form_score_by_form(form_id):
    s = select(
        [group_id, score],
        and_(
            form_scores.c.form_id == form_id
        )).order_by(form_scores.c.group_id)
    return s.execute()


def get_form_score_full():
    s = select([form_scores]).order_by(form_scores.c.form_id)
    return s.execute()


def get_state(group_id, station_id):
    """
    Given a group and station ID this will return the  state of the given
    group at the given station. If no the group does not have a state at that
    station, the default state (STATE_UNKNOWN) is returned.

    :param group_id: The group ID
    :type group_id: int
    :param station_id: The station ID
    :type station_id: int
    :return: The state
    :rtype: int
    """
    s = select(['state'], and_(
        group_station_state.c.group_id == group_id,
        group_station_state.c.station_id == station_id))
    result = s.execute().first()

    if not result:
        return STATE_UNKNOWN

    else:
        return result[0]


def set_station_score(group_id, station_id, score):
    s = select(
        [station_scores],
        and_(
            station_scores.c.group_id == group_id,
            station_scores.c.station_id == station_id
        ))
    row = s.execute().first()

    if not row:
        i = insert_station_score(group_id, station_id, score)
        i.execute()
    else:
        u = update_station_score(group_id, station_id, score)
        u.execute()


def insert_station_score(group_id, station_id, score):
    i = station_scores.inster().values(
        group_id=group_id,
        station_id=station_id,
        score=score)
    return i


def update_station_score(group_id, station_id, score):
    u = station_scores.filter_by(
        group_id=group_id,
        station_id=station_id
    ).update({
        'score': score
    }, synchronize_session=False)
    return u


def set_form_score(group_id, form_id, score):
    s = select(
        [form_scores],
        and_(
            form_scores.c.group_id == group_id,
            form_scores.c.form_id == form_id
        ))
    row = s.execute().first()

    if not row:
        i = insert_form_score(group_id, form_id, score)
        i.execute()
    else:
        u = update_form_score(group_id, form_id, score)
        u.execute()


def insert_form_score(group_id, form_id, score):
    i = form_scores.insert().values(
        group_id=group_id,
        form_id=form_id,
        score=score)
    return i


def update_form_score(group_id, form_id, score):
    u = form_scores.filter_by(
        group_id=group_id,
        form_id=form_id
    ).update({
        'score': score
    }, synchronize_session=False)
    return u


def advance(group_id, station_id):
    s = select(
        ['state'],
        and_(
            group_station_state.c.group_id == group_id,
            group_station_state.c.station_id == station_id
        ))
    db_row = s.execute().first()

    # The first state to set - if there is nothing yet - is "ARRIVED"
    if not db_row:
        i = group_station_state.insert().values(
            group_id=group_id,
            station_id=station_id,
            state=STATE_ARRIVED)
        i.execute()
        return STATE_ARRIVED

    the_state = db_row[0]
    if the_state == STATE_UNKNOWN:
        new_state = STATE_ARRIVED
    elif the_state == STATE_ARRIVED:
        new_state = STATE_FINISHED
    elif the_state == STATE_FINISHED:
        new_state = STATE_UNKNOWN
    else:
        raise ValueError('%r is not a valid state!' % the_state)
    upd = group_station_state.update().where(
        and_(
            group_station_state.c.group_id == group_id,
            group_station_state.c.station_id == station_id)
    ).values(
        state=new_state)
    upd.execute()
    return new_state


class Group(Base):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    order = Column(Integer)
    cancelled = Column(Boolean)
    contact = Column(Unicode(50))
    phone = Column(Unicode(20))
    direction = Column(Boolean)
    start_time = Column(Unicode(5))

    def __init__(self, name=None, contact=None,
                 phone=None, direction=None, start_time=None):
        self.name = name
        self.contact = contact
        self.phone = phone
        self.direction = direction
        self.start_time = start_time

    def __repr__(self):
        return '<Group %r>' % (self.name)


class Station(Base):
    __tablename__ = 'station'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    groups = relationship('Group', secondary=group_station_state)
    order = Column(Integer)
    contact = Column(Unicode(50))
    phone = Column(Unicode(20))

    def __init__(self, name=None, contact=None, phone=None):
        self.name = name
        self.contact = contact
        self.phone = phone

    def __repr__(self):
        return '<Station %r>' % (self.name)
