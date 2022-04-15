# -*- coding: utf-8 -*-

import os
import shutil
import sys
import datetime

from invoke import task
from invoke.util import cd

SETTINGS_FILE_BASE = 'pelicanconf.py'

def get_settings():
    from pelican.settings import DEFAULT_CONFIG, get_settings_from_file
    settings = {}
    settings.update(DEFAULT_CONFIG)
    LOCAL_SETTINGS = get_settings_from_file(SETTINGS_FILE_BASE)
    settings.update(LOCAL_SETTINGS)
    return settings

def get_config():
    settings= get_settings()
    config = {
        'settings_base': SETTINGS_FILE_BASE,
        'settings_publish': 'publishconf.py',
        # Output path. Can be absolute or relative to tasks.py. Default: 'output'
        'deploy_path': settings['OUTPUT_PATH'],
        # Port for `serve`
        'port': 8000,
    }
    return config

@task
def clean(c):
    """Remove generated files"""
    config = get_config()
    if os.path.isdir(config['deploy_path']):
        shutil.rmtree(config['deploy_path'])
        os.makedirs(config['deploy_path'])

@task
def build(c):
    """Build local version of site"""
    config = get_config()
    c.run('pelican -s {settings_base}'.format(**config))

@task
def rebuild(c):
    """`build` with the delete switch"""
    config = get_config()
    c.run('pelican -d -s {settings_base}'.format(**config))

@task
def regenerate(c):
    """Automatically regenerate site upon file modification"""
    config = get_config()
    c.run('pelican -r -s {settings_base}'.format(**config))

@task
def serve(c):
    """Serve site at http://localhost:$PORT/ (default port is 8000)"""

    from pelican.server import ComplexHTTPRequestHandler, RootedHTTPServer

    config = get_config()

    class AddressReuseTCPServer(RootedHTTPServer):
        allow_reuse_address = True

    server = AddressReuseTCPServer(
        config['deploy_path'],
        ('', config['port']),
        ComplexHTTPRequestHandler)

    sys.stderr.write('Serving on port {port} ...\n'.format(**config))
    server.serve_forever()

@task
def reserve(c):
    """`build`, then `serve`"""
    build(c)
    serve(c)

@task
def preview(c):
    """Build production version of site"""
    config = get_config()
    c.run('pelican -s {settings_publish}'.format(**config))

@task
def livereload(c):
    """Automatically reload browser tab upon file modification."""
    from livereload import Server
    settings = get_settings()
    config = get_config()
    build(c)
    server = Server()
    # Watch the base settings file
    server.watch(config['settings_base'], lambda: build(c))
    # Watch content source files
    content_file_extensions = ['.md', '.rst']
    for extension in content_file_extensions:
        content_blob = '{0}/**/*{1}'.format(settings['PATH'], extension)
        server.watch(content_blob, lambda: build(c))
    # Watch the theme's templates and static assets
    theme_path = settings['THEME']
    server.watch('{}/templates/*.html'.format(theme_path), lambda: build(c))
    static_file_extensions = ['.css', '.js']
    for extension in static_file_extensions:
        static_file = '{0}/static/**/*{1}'.format(theme_path, extension)
        server.watch(static_file, lambda: build(c))
    # Serve output path on configured port
    server.serve(port=config['port'], root=config['deploy_path'])


@task
def publish(c):
    """Publish to production via rsync"""
    config = get_config()
    c.run('pelican -s {settings_publish}'.format(**config))
    c.run(
        'rsync --delete --exclude ".DS_Store" -pthrvz -c '
        '-e "ssh -p {ssh_port}" '
        '{} {ssh_user}@{ssh_host}:{ssh_path}'.format(
            config['deploy_path'].rstrip('/') + '/',
            **config))


@task
def develop(c):
    """Set up a working environment"""
    c.run('[ -d env ] || python3 -m venv env')
    c.run('./env/bin/pip install -U pip')
    c.run('./env/bin/pip install pelican[Markdown] icalendar')
    c.run('[ -d pelican-plugins-src ] || '
          'git clone --recursive https://github.com/getpelican/pelican-plugins '
          'pelican-plugins-src')
