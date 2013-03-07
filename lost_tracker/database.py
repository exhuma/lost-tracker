from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()

    import lost_tracker.models  # NOQA
    import lost_tracker.main  # NOQA
    Base.metadata.create_all()
    print 'Database created on {0}'.format(Base.metadata)
