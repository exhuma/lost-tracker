#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'Mamer Wiselen'
SITENAME = 'lost.lu'
SITEURL = ''

PLUGIN_PATHS = ['pelican-plugins']
PLUGIN_EVENTS = {
    'ics_fname': 'calendar.ics',
}
PLUGINS = ['i18n_subsites', 'events']
I18N_SUBSITES = {
    'lu': {
        'SITENAME': 'lost.lu'
    },
    'de': {
        'SITENAME': 'lost.lu'
    },
    'en': {
        'SITENAME': 'lost.lu'
    }
}
STATIC_PATHS = ['static']

THEME = 'lost-lu-theme'
PATH = 'content'

TIMEZONE = 'Europe/Luxembourg'

DEFAULT_LANG = 'lu'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (('Pelican', 'http://getpelican.com/'),
         ('Python.org', 'http://python.org/'),
         ('Jinja2', 'http://jinja.pocoo.org/'),
         ('You can modify those links in your config file', '#'),)

# Social widget
SOCIAL = (('You can add links in your config file', '#'),
          ('Another social link', '#'),)

DEFAULT_PAGINATION = 10

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True
