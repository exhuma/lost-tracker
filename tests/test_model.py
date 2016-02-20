import pytest

from seeds import reseed_db


@pytest.fixture(scope="module")
def freshdb(request):
    from sqlalchemy import create_engine
    from config_resolver import Config

    conf = Config('mamerwiselen', 'lost-tracker', require_load=True)
    dsn = conf.get('db', 'dsn')
    engine = create_engine(dsn)
    connection = engine.raw_connection()
    cursor = connection.cursor()
    reseed_db(cursor)
    connection.commit()

    def disconnect():
        engine.dispose()

    request.addfinalizer(disconnect)

    return conf
