INSTALLATION
------------

.. note:: I recommend using virtualenv, but nothing prevents you installing
          it into the root system

Requirements
~~~~~~~~~~~~

When installing this package, it will build the Postgres client. So you'll need
the necessary headers, plus gcc on your machine.

For Ubuntu, run the following::

   sudo apt-get install libpq-dev python-dev build-essential

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

    # export MAMERWISELEN_LOST_TRACKER_PATH="/path/which/contains/app.ini"
    # ./env/bin/alembic upgrade head


.. note::

    The environment variable should point to the path *containing* ``app.ini``.
    Not the filename itself!


Configuration
-------------

Configuration is handled using ``ini`` style config files. An example file is
given in ``app.ini.dist``.

The file is looked up using config_resolver_.

.. _config_resolver:: https://config-resolver.readthedocs.org/en/latest/
