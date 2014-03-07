from lost_tracker.models import (
    Group,
    Station,
    Form,
    get_state,
    GroupStation,
    get_form_score_by_group,
    STATE_FINISHED,
    STATE_UNKNOWN,
    STATE_ARRIVED,
    DIR_A,
    DIR_B)


def get_matrix(stations, groups):
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

    state_matrix = []
    for group in groups:
        tmp = [group]
        for station in stations:
            tmp.append(get_state(group.id, station.id))
        state_matrix.append(tmp)
    return state_matrix


def get_state_sum(state_matrix):
    """
    Creates a list where each element contains the sum of "unknown", "arrived"
    and "finished" states for each station.
    """
    # TODO: make this a list of namedtuples!
    sums = []
    if state_matrix:
        sums = [[0, 0, 0] for _ in state_matrix[0][1:]]
        for row in state_matrix:
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


def get_grps():
    """
    Returns all groups from the database as :py:class:`Group` instances.
    """
    groups = Group.query
    groups = groups.order_by(Group.order)
    groups = groups.all()
    return groups

def get_grps_by_id(group_id):
    """
    Returns a group from the database as :py:class:`Group` instance by his id.
    """
    group = Group.query
    group = group.filter_by(id=group_id)
    group = group.first()
    return group

def add_grp(grp_name, contact, phone, direction, start_time, session):
    """
    Creates a new group in the database.
    """

    if direction not in (DIR_A, DIR_B):
        raise ValueError('{0!r} is not among the supported values '
                         'for "direction" which are: {1!r}, {2!r}'.format(
                             DIR_A, DIR_B))

    new_grp = Group(grp_name, contact, phone, direction, start_time)
    session.add(new_grp)
    return ("Group {0} with Contact {1} / {2} was successfully added into the "
            "DB. The given start-time is {3} and the direction is {4}".format(
                grp_name,
                contact,
                phone,
                start_time,
                direction))


def get_stations():
    """
    Returns all stations from the database as :py:class:`Station` instances.
    """
    stations = Station.query
    stations = stations.order_by(Station.order)
    stations = stations.all()
    return stations


def get_stat_by_name(name):
    """
    Returns a :py:class:`Station` by class name. Can be ``None`` if no
    matching station is found.
    """
    qry = Station.query
    qry = qry.filter_by(name=name)
    qry = qry.first()
    return qry


def add_station(stat_name, contact, phone, session):
    """
    Creates a new :py:class:`Station` in the database.
    """
    new_station = Station(stat_name, contact, phone)
    session.add(new_station)
    return "Station {0} added. Contact: {1} / {2}".format(
        stat_name, contact, phone)


def add_form_db(form_id, name, max_score, session):
    tmp_form = get_form_by_id(form_id)
    if tmp_form:
        tmp_form.name = name
        tmp_form.max_score = max_score
        return "Form {0} updated: {1} - max: {2}".format(
            form_id, name, max_score)
    else:
        new_form = Form(form_id, name, max_score)
        session.add(new_form)
        return "Form added: {0} - {1} - max: {2}".format(
            form_id, name, max_score)


def get_forms():
    """
    Returns all forms from the database as :py:class`Form` instances.
    """
    forms = Form.query
    forms = forms.order_by(Form.id)
    forms = forms.all()
    return forms


def get_form_by_id(id):
    """
    Returns a :py:class:`Form` by class id.
    """
    qry = Form.query
    qry = qry.filter_by(id=id)
    qry = qry.first()
    return qry

def get_score_by_group(group_id):
    """
    Returns the actual score for a group.
    """
    qry = GroupStation.query
    qry = qry.filter_by(group_id=group_id)
    station_score = qry.all()

    form_score = get_form_score_by_group(group_id)

def store_registration(data):
    raise NotImplementedError

def confirm_registration(key):
    raise NotImplementedError
