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
        Column('state', Integer, default=STATE_UNKNOWN)
        )

group_station_points = Table(
        'group_station_points',
        Base.metadata,
        Column('group_id', Integer, ForeignKey('group.id')),
        Column('station_id', Integer, ForeignKey('station.id')),
        Column('questionnaire_score', Integer, default=0),
        Column('questionnaire_id', Integer),
        Column('post_score', Integer, default=0)
        )

def get_score(group_id=None, station_id=None):
    if group_id:
        if station_id:
            s = select([group_station_points],
                and_(
                group_station_points.c.group_id == group_id,
                group_station_points.c.station_id == station_id
                ))
            result = s.execute()
        else:
            s = select([group_station_points],
                and_(
                group_station_points.c.group_id == group_id
                ))
            result = s.execute()
    else:
        if station_id:
            s = select(
                and_(
                group_station_points.c.station_id == station_id
                ))
            result = s.execute()
        else:
            s = select([group_station_points])
            result = s.execute()

    return result

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
        group_station_state.c.station_id == station_id
        ))
    result = s.execute().first()

    if not result:
        return STATE_UNKNOWN

    else:
        return result[0]

def set_score(group_id, station_id, questionnaire_score=None,questionnaire_id=None, post_score=None):
    s = select(
        and_(
        group_station_points.c.group_id == group_id,
        group_station_points.c.station_id == station_id
        ))
    db_row = s.execute().first()

    if not db_row:
        i = group_station_points.insert().values(
                questionnaire_score = questionnaire_score,
                questionnaire_id = questionnaire_id,
                post_score = post_score
                )
        i.execute()
        return 'insert'
    else:
        if not questionnaire_score:
            q_score = db_row[2]
        if not questionnaire_id:
            q_id = db_row[3]
        if not post_score:
            p_score = db_row[4]

        u = group_station_points.filter_by(
            group_id=group_id,
            station_id=station_id
            ).update({
            'questionnaire_score': q_score,
            'questionnaire_id': q_id,
            'post_score': p_score
            },
            synchronize_session=False
            )
        u.execute()
        return 'update'

def advance(group_id, station_id):
    s = select(['state'], and_(
        group_station_state.c.group_id == group_id,
        group_station_state.c.station_id == station_id
        ))
    db_row = s.execute().first()

    # The first state to set - if there is nothing yet - is "ARRIVED"
    if not db_row:
        i = group_station_state.insert().values(
                group_id=group_id,
                station_id=station_id,
                state=STATE_ARRIVED
                )
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
                    state=new_state
                    )
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

    def __init__(self, name=None, contact=None, phone=None, direction=None, start_time=None):
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
