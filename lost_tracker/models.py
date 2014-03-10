from collections import namedtuple

from sqlalchemy import (Column, Integer, Unicode, ForeignKey, Table, and_,
                        Boolean, PrimaryKeyConstraint)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import select
from lost_tracker.database import Base

STATE_UNKNOWN = 0
STATE_ARRIVED = 1
STATE_FINISHED = 2

DIR_A = u'Giel'
DIR_B = u'Roud'


form_scores = Table(
    'form_scores',
    Base.metadata,
    Column('group_id', Integer, ForeignKey('group.id')),
    Column('form_id', Integer, ForeignKey('form.id')),
    Column('score', Integer, default=0),
    PrimaryKeyConstraint('group_id', 'form_id'))


def score_totals():
    score_result = namedtuple('ScoreResult',
                              'group_id, score_sum')

    station_select = select([
        GroupStation.__table__.c.group_id,
        GroupStation.__table__.c.score])

    form_select = select([
        form_scores.c.group_id,
        form_scores.c.score])

    group_scores = {}
    for gid, score in form_select.execute():
        if score is None:
            continue
        group_scores.setdefault(gid, 0)
        group_scores[gid] += score

    for gid, score in station_select.execute():
        if score is None:
            continue
        group_scores.setdefault(gid, 0)
        group_scores[gid] += score

    output = []
    for gid in group_scores:
        output.append(score_result(gid, group_scores[gid]))

    return output


def get_form_score_full():
    s = select([form_scores]).order_by(form_scores.c.form_id)
    return s.execute()


def get_form_score(group_id, form_id):
    s = select([form_scores])
    s = s.where(form_scores.c.group_id == group_id)
    s = s.where(form_scores.c.form_id == form_id)
    result = s.execute().fetchone()
    if not result:
        return 0
    return result.score


def get_form_score_by_group(group_id):
    s = select([form_scores])
    s = s.where(form_scores.c.group_id == group_id)
    result = s.execute()
    if not result:
        return 0
    return result.score


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
    u = form_scores.update().where(
        and_(
            form_scores.c.group_id == group_id,
            form_scores.c.form_id == form_id)
    ).values(
        score=score)
    return u


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
    q = GroupStation.query.filter(and_(
        GroupStation.group_id == group_id,
        GroupStation.station_id == station_id))
    return q.first()


def advance(session, group_id, station_id):
    state = GroupStation.get(group_id, station_id)

    # The first state to set - if there is nothing yet - is "ARRIVED"
    if not state:
        state = GroupStation(group_id, station_id)
        state.state = STATE_ARRIVED
        session.add(state)
        return STATE_ARRIVED

    if state.state == STATE_UNKNOWN:
        state.state = STATE_ARRIVED
    elif state.state == STATE_ARRIVED:
        state.state = STATE_FINISHED
    elif state.state == STATE_FINISHED:
        state.state = STATE_UNKNOWN
    else:
        raise ValueError('%r is not a valid state!' % state.state)

    return state.state


class Group(Base):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True)
    order = Column(Integer)
    cancelled = Column(Boolean)
    contact = Column(Unicode(50))
    phone = Column(Unicode(20))
    direction = Column(Unicode)
    start_time = Column(Unicode(5))
    stations = relationship('GroupStation')

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
    order = Column(Integer)
    contact = Column(Unicode(50))
    phone = Column(Unicode(20))
    groups = relationship('GroupStation')

    def __init__(self, name=None, contact=None, phone=None):
        self.name = name
        self.contact = contact
        self.phone = phone

    def __repr__(self):
        return '<Station %r>' % (self.name)


class Form(Base):
    __tablename__ = 'form'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(20))
    max_score = Column(Integer)

    def __init__(self, id, name=None, max_score=100):
        self.id = id
        self.name = name
        self.max_score = max_score

    def __repr__(self):
        return '<Form %r>' % (self.name)


class GroupStation(Base):
    __tablename__ = 'group_station_state'

    group_id = Column(Integer, ForeignKey('group.id'), primary_key=True)
    station_id = Column(Integer, ForeignKey('station.id'), primary_key=True)
    state = Column(Integer, default=STATE_UNKNOWN)
    score = Column(Integer, nullable=True, default=None)
    group = relationship("Group")
    station = relationship("Station")

    def __init__(self, group_id, station_id):
        self.group_id = group_id
        self.station_id = station_id

    @staticmethod
    def get(group_id, station_id):
        return GroupStation.query.filter(and_(
            GroupStation.group_id == group_id,
            GroupStation.station_id == station_id)).first()

    @staticmethod
    def set_score(session, group_id, station_id, score):
        query = GroupStation.query.filter(and_(
            GroupStation.group_id == group_id,
            GroupStation.station_id == station_id))
        row = query.first()
        if not row:
            gs = GroupStation(group_id, station_id)
            gs.score = score
            session.add(gs)
        else:
            row.score = score


# station_select = select([
#     GroupStation.__table__.c.group_id,
#     GroupStation.__table__.c.score])
#
# form_select = select([
#     form_scores.c.group_id,
#     form_scores.c.score])
#
# big_from = station_select.union(form_select).alias('subs')
# union_select = select([big_from.c.group_id,
#     func.sum(big_from.c.score)],
#     from_obj=big_from)
# union_select = union_select.group_by(union_select.c.group_id).alias("resultq")
#
#
# class Results(Base):
#     __table__ = union_select
#
#     def __repr__(self):
#         return "<Results group_id={0}, score={1}>".format(
#                 self.group_id, 10)
