from lost_tracker.models import (Group, Station, get_state,
        advance as db_advance, STATE_FINISHED, STATE_UNKNOWN, STATE_ARRIVED)

def get_matrix(stations, groups):

    state_matrix = []
    for group in groups:
        tmp = [group]
        for station in stations:
            tmp.append(get_state(group.id, station.id))
        state_matrix.append(tmp)
    return state_matrix

def get_state_sum(state_matrix):
    sums = []
    if state_matrix:
        sums = [[0, 0, 0] for _ in state_matrix[0][1:]]
        for row in state_matrix:
            for i, state in enumerate(row[1:]):
                if not state or state == STATE_UNKNOWN:
                    sums[i][STATE_UNKNOWN] += 1
                elif state == STATE_ARRIVED:
                    sums[i][STATE_ARRIVED] += 1
                elif state == STATE_FINISHED:
                    sums[i][STATE_FINISHED] += 1

    return sums

def get_grps():
    groups = Group.query
    groups = groups.order_by(Group.order)
    groups = groups.all()
    return groups

def add_grp(grp_name, contact, phone, direction, start_time, session):
    if direction is "1":
        color = "Giel"
    else:
        color = "Roud"

    new_grp = Group(grp_name, contact, phone, direction, start_time)
    session.add(new_grp)
    return "Group {0} with Contact {1} / {2} was successfully added into the DB. The given start-time is {3} and the direction is {4}".format(grp_name, contact, phone, start_time, color)

def get_stations():
    stations = Station.query
    stations = stations.order_by(Station.order)
    stations = stations.all()
    return stations

def get_stat_by_name(name):
    qry = Station.query
    qry = qry.filter_by( name = name )
    qry = qry.first()
    return qry

def add_station(stat_name, contact, phone, session):
    new_station = Station(stat_name, contact, phone)
    session.add(new_station)
    return "Station " + stat_name + " added. Contact: " + contact + " / " + phone

