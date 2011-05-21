from sqlalchemy import Column, Integer, String, ForeignKey, Table, and_
from sqlalchemy.orm import relationship
from sqlalchemy.sql import select
from lost_tracker.database import Base, engine

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

def get_state(group_id, station_id):
    s = select(['state'], and_(
        group_station_state.c.group_id == group_id,
        group_station_state.c.station_id == station_id
        ))
    s.bind = engine
    return list(s.execute())

def advance(group_id, station_id):
    s = select(['state'], and_(
        group_station_state.c.group_id == group_id,
        group_station_state.c.station_id == station_id
        ))
    s.bind = engine
    result = list(s.execute())
    if not result:
        i = group_station_state.insert().values(
                group_id=group_id,
                station_id=station_id,
                state = STATE_ARRIVED
                )
        i.bind=engine
        i.execute()
        return STATE_ARRIVED

    try:
        the_state = result[0][0]
        if the_state == STATE_UNKNOWN:
            new_state = STATE_ARRIVED
        elif the_state == STATE_ARRIVED:
            new_state = STATE_FINISHED
        elif the_state == STATE_FINISHED:
            new_state = STATE_UNKNOWN
        upd = group_station_state.update().where(
                and_(
                    group_station_state.c.group_id == group_id,
                    group_station_state.c.station_id == station_id)
                ).values(
                        state=new_state
                        )
        upd.bind = engine
        upd.execute()
        return new_state

    except IndexError:
        pass

class Group(Base):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)

    def __init__(self, name=None):
        self.name = name

    def __repr__(self):
        return '<Group %r>' % (self.name)

class Station(Base):
    __tablename__ = 'station'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    groups = relationship('Group', secondary=group_station_state)

    def __init__(self, name=None):
        self.name = name

    def __repr__(self):
        return '<Station %r>' % (self.name)

