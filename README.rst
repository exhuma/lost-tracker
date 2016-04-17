Tracker for Lost in the Darkness
================================

Development
-----------

Required Tools
~~~~~~~~~~~~~~

* fabric (Python Task Runner)
* Python 2.7 (Python 3.5 was tested hasl-arsedly, may work...)
* Oracle Java 1.7+ (Tested with OpenJDK with mixed results). This is needed for
  live JS compilation. Without it, no JavaScript will run!


Additional Notes
~~~~~~~~~~~~~~~~

* The application sends e-mails. If it's running in "DEBUG" mode (see the
  ``.ini`` file), those e-mails are NOT sent. Instead, they are only logged.
* Currently you are required to properly log in. Even in development. So you
  need API keys for one of Facebook or Google!


Setting up the environment
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    You MAY run into missing system dependencies (header files) as some
    third-party Python modules contain C source. You will see this if you get a
    "*File not found*" error. On the top of my head, those dependencies should
    be:

    * python-dev (for anything, really)
    * libpq-dev (For postgres connections)
    * libjpeg-dev (for thumbnail generation in the image gallery)
    * libffi-dev (for social logins)

    Additionally, I *strongly* recommend to install the official Oracle Java
    binaries (for the plovr server). I have tried with OpenJDK with mixed
    results. The official binaries work best!

    YMMV


If you want to develop on lost-tracker, follow these steps to get a development
environment set up and running:

Clone the code::

    git clone https://github.com/exhuma/lost-tracker

... or, if you want to use SSH::

    git clone ssh://git@github.com/exhuma/lost-tracker

Enter the cloned folder and run the develop fabric-task. Running that task will
set up a virtual-env, dowload required dependencies and install the application
into that environment::

    cd lost-tracker
    fab develop

When this successfully completes you should have an environment ready for happy
hacking.

One final note: JavaScript is compiled using the google-closure compiler with
the help of plovr. Those dependencies should have been downloaded for you into
the ``__libs__`` folder. You *must* run plovr during development! As a
convenience, there's a ``tmux-serve.bash`` script which will run both the
web-server and the plovr server::

    ./tmux-serve.bash


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
