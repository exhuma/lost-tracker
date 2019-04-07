INSTALLATION
------------

Since 2019, this application is available as a docker-container. You should be
able to run it using::

    docker run exhuma/lost-tracker

Internally it will expose the port ``8080`` as HTTP

Environment Variables
---------------------

The following environment variables are available when running the container:

**TRACKER_DSN** (required)
    An SQLAlchemy databse URL. For example:
    ``postgresql://john:password@dbhost/dbname``

**TRACKER_HELPDESK**
    A text which is available on each page

**TRACKER_PHOTO_FOLDER**
    A folder-name which contains photos which are shown on the web-page.
    It is recommended to mount a host-folder into the running container to this
    location.

**TRACKER_HTTP_LOGIN**
    A plain-text HTTP username used for API clients

**TRACKER_HTTP_PASSWORD**
    A plain-text HTTP password used for API clients

**TRACKER_SECRET_KEY**
    Internally used for security. Should be set to a random string

**TRACKER_SHOUT**
    A text shown on each page

**TRACKER_FLICKR_API_KEY**
    A key which is allowed to access the Flickr API. This is used for
    additional photos.

**TRACKER_REGISTER_URL**
    An optional URL which will be used for registrations instead of the builtin
    solution


When the container starts up it will automatically apply database upgrades as
necessary.
