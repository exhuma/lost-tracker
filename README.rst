Tracker for Lost in the Darkness
================================

INSTALLATION
------------

.. note:: I recommend using virtualenv, but nothing prevents you installing
          it into the root system

Requirements
~~~~~~~~~~~~

When installing this package, it will build the MySQL and Postgres clients. So
you'll need the necessary headers, plus gcc on your machine.

For Ubuntu, run the following::

   sudo apt-get install libmysqlclient-dev libpq-dev python-dev \
                        build-essential

Installation procedure
~~~~~~~~~~~~~~~~~~~~~~

- Download the latest package from http://www.github.com/exhuma/lost-tracker I
  recommend using the latest tagged version, but if you want bleeding edge, you
  may also download the "master" branch.

- untar the package::

     tar xzf exhuma-lost-tracker-<version number+hash>.tar.gz

- enter the folder::

     cd exhuma-lost-tracker-<version number+hash>

When not using virtualenv, you may skip this section
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note:: If you don't have virtualenv, run the following:

    ``sudo apt-get install python-setuptools && easy_install virtualenv``

- create a virtualenv::

     virtualenv --no-site-packages /path/to/your/env

- activate the environment::

     source /path/to/your/env/bin/activate

Without virtualenv
~~~~~~~~~~~~~~~~~~

- run the installer::

     python setup.py install


Database initialisation
~~~~~~~~~~~~~~~~~~~~~~~

To initialise the database run the following commands::

    # export LOST_TRACKER_SETTINGS="/tmp/my/conf/file.py"
    # ./env/bin/python
    >>> from lost_tracker.database import init_db
    >>> init_db()


Configuration
-------------

Configuration is handled using default Python script files. Currently the only
configuration variable is ``DB_DSN`` representing the database connection
string.

An example config file could be::

    DB_DSN = 'postgres://user:passwd@localhost/dbname'

The file is only read by setting an environment variable called
LOST_TRACKER_SETTINGS pointing to the file. For example::

    export LOST_TRACKER_SETTINGS="/tmp/my/conf/file.py"
    ./env/bin/python lost_tracker/main.py
