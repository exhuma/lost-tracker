from io import StringIO
from textwrap import dedent


def reseed_db(cursor):
    cursor.execute(dedent('''
        TRUNCATE
            alembic_version,
            form,
            "group",
            form_scores,
            station,
            group_station_state,
            page,
            settings,
            "user";'''))

    data = StringIO(dedent(
        '''\
        11\tform 1\t100\t0
        15\tform 2\t13\t12
        16\tform 3\t12\t0
        17\tform 4\t23\t1
        '''))
    cursor.copy_from(data, 'form', columns=('id', 'name', 'max_score', '"order"'))
    cursor.execute('''SELECT pg_catalog.setval('form_id_seq', 21, true);''')

    data = StringIO(dedent(
        '''\
        144\tGroup 1\t2010\tf\tJohn Doe 1\t12345\tGiel\t20h10\tcomment\tt\tPe5lja2rPH0LJYiUqUXi\tjohn@doe.com\tf\t2015-04-15 19:50:51.130196\t2016-02-13 15:16:32.306056\tf
        142\tGroup 2\t2020\tf\tJohn Doe 2\t12345\tGiel\t20h20\tcomment\tt\tOJVV9lZV+lc3baoOoJhG\tjohn@doe.com\tf\t2015-04-15 16:58:02.834033\t2016-02-13 15:16:32.306056\tf
        137\tGroup 3\t1920\tf\tJohn Doe 3\t12345\tGiel\t19h20\tcomment\tt\tGPPb483QlsuUte4kTZ7V\tjohn@doe.com\tf\t2015-04-14 22:36:45.507761\t2016-02-13 15:16:32.306056\tf
        135\tGroup 4\t1920\tf\tJohn Doe 4\t12345\tRoud\t19h20\tcomment\tt\tyYqCxGWgSprXxvB5xJP9\tjohn@doe.com\tf\t2015-04-14 22:28:19.736845\t2016-02-13 15:16:32.306056\tf
        '''))
    cursor.copy_from(data, '"group"', columns=('id', 'name', '"order"', 'cancelled', 'contact', 'phone', 'direction', 'start_time', 'comments', 'is_confirmed', 'confirmation_key', 'email', 'finalized', 'inserted', 'updated', 'completed'))

    data = StringIO(dedent(
        '''\
        135\t16\t23
        135\t15\t22
        135\t17\t12
        135\t11\t1
        '''))
    cursor.copy_from(data, 'form_scores', columns=('group_id', 'form_id', 'score'))
    cursor.execute('''SELECT pg_catalog.setval('group_id_seq', 152, true);''')

    data = StringIO(dedent(
        '''\
        30\tworld\t90\t\tN/A
        28\tArrivee\t1000\tMich\t
        10\tDépart\t-1000\tMich\t+352 123456
        26\tGrillposten\t0\t0\t
        '''))
    cursor.copy_from(data, 'station', columns=('id', 'name', '"order"', 'contact', 'phone'))

    data = StringIO(dedent(
        '''\
        144\t10\t0\t12\t\\N
        142\t10\t0\t5\t\\N
        142\t26\t2\t0\t22
        137\t10\t0\t12\t1222
        137\t26\t1\t224\t223
        135\t10\t0\t11\t0
        144\t26\t2\t0\t0
        '''))
    cursor.copy_from(data, 'group_station_state', columns=('group_id', 'station_id', 'state', 'score', 'form_score'))

    data = StringIO(dedent(
        '''\
        misc\ten\t\t\ttext/html\t2015-05-17 16:46:05.6927+02\t\\N
        misc\tlu\t\t\ttext/html\t2015-05-17 16:46:05.6927+02\t\\N
        misc\tde\tMisc\thello world<b>yoinks de</b>eofijdf\ttext/html\t2015-05-17 16:46:05.6927+02\t\\N
        misc2\tde\t\t\ttext/html\t2015-05-17 16:46:05.6927+02\t\\N
        misc2\ten\tmisc2\tmisc2\ttext/html\t2015-05-17 16:46:05.6927+02\t\\N
        misc2\tlu\t\t\ttext/html\t2015-05-17 16:46:05.6927+02\t\\N
        helloworld\tde\t\t\ttext/html\t2015-05-17 16:46:05.6927+02\t\\N
        helloworld\ten\tHello World\tHello World\ttext/html\t2015-05-17 16:46:05.6927+02\t\\N
        helloworld\tlu\t\t\ttext/html\t2015-05-17 16:46:05.6927+02\t\\N
        foo\tde\t\\N\t\\N\ttext/html\t2015-05-17 16:46:05.6927+02\t\\N
        '''))
    cursor.copy_from(data, 'page', columns=('name', 'locale', 'title', 'content', 'media_type', 'inserted', 'updated'))

    data = StringIO(dedent(
        '''\
        event_date\t"2014-05-13"\t
        helpdesk\t"23432"\t
        registration_open\tfalse\t
        shout\t"shout shout shout"\t
        '''))
    cursor.copy_from(data, 'settings', columns=('key', 'value', 'description'))
    cursor.execute('''SELECT pg_catalog.setval('station_id_seq', 32, true);''')

    data = StringIO(dedent(
        '''\
        lost\tPosten\tlost\tposten@lost.lu\t\\N\tf
        admin\tTest Admin User\tadmin\tadmin@example.com\t\\N\tt
        '''))
    cursor.copy_from(data, '"user"', columns=('login', 'name', 'password', 'email', 'locale', 'admin'))
