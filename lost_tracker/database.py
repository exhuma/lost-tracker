from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False))
Base = declarative_base()
Base.query = db_session.query_property()
