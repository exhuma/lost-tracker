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

    def tearDown(self):
        self.session.remove()


if __name__ == '__main__':
    main()
