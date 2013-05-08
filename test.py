from unittest import TestCase, main

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import lost_tracker.models as lm
from lost_tracker.database import Base


class TestModel(TestCase):

    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        self.session = scoped_session(sessionmaker(autocommit=False,
                                      autoflush=False))

        Base.query = self.session.query_property()
        Base.metadata.create_all(bind=self.engine)
        Base.metadata.bind = self.engine

        lm.form_scores.insert(values={
            'group_id': 1,
            'form_id': 1,
            'score': 10
        }).execute()

        lm.Group.__table__.insert(values={
            'id': 1,
            'name': u'group a',
            'order': 10,
            'cancelled': False,
            'contact': u'contact 1',
            'phone': u'phone 1',
            'direction': lm.DIR_A,
            'start_time': u'12:30'
        }).execute()
        lm.Group.__table__.insert(values={
            'id': 2,
            'name': u'group b',
            'order': 5,
            'cancelled': False,
            'contact': u'contact 2',
            'phone': u'phone 2',
            'direction': lm.DIR_B,
            'start_time': u'12:10'
        }).execute()
        lm.Group.__table__.insert(values={
            'id': 3,
            'name': u'group c',
            'order': 6,
            'cancelled': True,
            'contact': u'contact 3',
            'phone': u'phone 3',
            'direction': lm.DIR_B,
            'start_time': u'12:00'
        }).execute()

        lm.Station.__table__.insert(values={
            'id': 1,
            'name': u'station1',
            'order': 10,
            'contact': u'station 1 contact',
            'phone': u'station 1 phone',
        }).execute()
        lm.Station.__table__.insert(values={
            'id': 2,
            'name': u'station2',
            'order': 6,
            'contact': u'station 2 contact',
            'phone': u'station 2 phone',
        }).execute()

        lm.Form.__table__.insert(values={
            'id': 1,
            'name': u'form1',
            'max_score': 100
        }).execute()
        lm.Form.__table__.insert(values={
            'id': 2,
            'name': u'form2',
            'max_score': 80
        }).execute()

        lm.GroupStation.__table__.insert(values={
            'group_id': 1,
            'station_id': 1,
            'state': lm.STATE_ARRIVED,
            'score': 10
        }).execute()

    def tearDown(self):
        self.session.remove()


if __name__ == '__main__':
    main()
