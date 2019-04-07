from os import environ
from string import Template

with open('/app.ini.dist') as fptr:
    template = Template(fptr.read())

with open('/etc/mamerwiselen/lost-tracker/app.ini', 'w') as fptr:
    fptr.write(template.substitute(dict(
        DSN=environ['TRACKER_DSN'],
        HELPDESK=environ['TRACKER_HELPDESK'],
        PHOTO_FOLDER=environ['TRACKER_PHOTO_FOLDER'],
        HTTP_LOGIN=environ['TRACKER_HTTP_LOGIN'],
        HTTP_PASSWORD=environ['TRACKER_HTTP_PASSWORD'],
        SECRET_KEY=environ['TRACKER_SECRET_KEY'],
        SHOUT=environ['TRACKER_SHOUT'],
        FLICKR_API_KEY=environ['TRACKER_FLICKR_API_KEY'],
    )))
