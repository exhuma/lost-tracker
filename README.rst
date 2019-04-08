Tracker for Lost in the Darkness
================================

What is lost-tracker?
---------------------

This application is a tool to help organisation of a local event ("Lost in the
Darkness"). If you are not involved with this event, you can most likely move
on :)

In short: It helps with registration of groups for a game. Once the game is
live, it helps live-tracking of the scores of the competing teams via a mobile
app.


Development
-----------

Required Tools
~~~~~~~~~~~~~~

* invoke (Python Task Runner). This is optional but highly convenient!
* Python 3
* docker (for javascript compilation)


Additional Notes
~~~~~~~~~~~~~~~~

* The application sends e-mails. If it's running in "DEBUG" mode (see the
  ``.ini`` file), those e-mails are NOT sent. Instead, they are only logged.
* During development, there's an additional route available: ``/fake_login``
  which immediately logs you in as admin. You can also log-in as standard user
  by specifying an e-mail in the request:
  ``/fake_login?email=jdoe@example.com``

  This route is obviously not available in the production environment (or, to
  be more precive, when run as a WSGI application). NEVER run this application
  in debug mode on a production host!


Setting up the development environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
    binaries (for the plovr_ server). I have tried with OpenJDK with mixed
    results. The official binaries work best!

    YMMV


If you want to develop on lost-tracker, follow these steps to get a development
environment up and running:

Clone the code::

    git clone https://github.com/exhuma/lost-tracker

Enter the cloned folder, switch to the ``develop`` branch  and run the develop
invoke-task. Running that task will set up a virtual-env, download required
dependencies and install the application into that environment::

    cd lost-tracker
    git checkout develop  # Make sure you're on the latest developmen branch
    inv develop           # Prepares a virtualenv and downloads dependencies.

When this successfully completes you should have an environment ready for happy
hacking.

One final note: JavaScript is compiled using the google-closure compiler with
the help of plovr_. The compiler has been wrapped in a docker container and
should be downloaded and run transparently. An invoke task is available::

    inv serve_plovr


Configuration
~~~~~~~~~~~~~

See ``INSTALL.rst``


Running a Development Instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Settings for the development server are in your configuration file in the
section ``[devserver]``. Make sure to set these to your liking.

You should also adapt the database connection string, and while you're at it,
look through the rest of the config file as well.

Once all is configured the development server can be run with::

    inv serve_web

During development (when ``DEBUG=True``), you also need to run the plovr_
server in parallel. Simply open a new shell and type::

    inv serve_plovr

Social Logins During Development
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can skip social logins during development by accessing the URL
``/fakelogin``. This is only accessible when running the development server
though. On production, this route is unavailable for security reasons.

.. _plovr: http://www.plovr.com
