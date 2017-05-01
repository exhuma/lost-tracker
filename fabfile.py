from __future__ import print_function
from ConfigParser import SafeConfigParser
from getpass import getuser
from os.path import exists, dirname

import fabric.api as fab
import fabric.colors as clr

fab.env.roledefs = {
    'prod': ['178.62.219.167'],
}


REMOTE_FOLDER = '/var/www/lost.lu/www'
REMOTE_USER = 'lost_tracker'
DOCKER_PLOVR = 'exhuma/lost-tracker-closure'


@fab.task
@fab.roles('prod')
@fab.with_settings(user=REMOTE_USER)
def deploy():
    fab.execute(build)
    fab.execute(babel_compile)
    fab.execute(upload)
    fab.execute(install)
    fab.execute(clean)


@fab.task
@fab.with_settings(user=REMOTE_USER)
def upload():
    fab.local('python setup.py sdist')
    name = fab.local('python setup.py --fullname', capture=True)
    with fab.cd(REMOTE_FOLDER):
        fab.put('dist/{0}.tar.gz'.format(name), '.')
        fab.put('alembic.ini', '.')
        fab.put('alembic', '.')
        fab.put('requirements.txt', '.')


@fab.task
@fab.with_settings(user=REMOTE_USER)
def install():
    name = fab.local('python setup.py --fullname', capture=True)
    with fab.cd(REMOTE_FOLDER):
        fab.run('env/bin/pip install -r requirements.txt')
        fab.run('env/bin/pip install {0}.tar.gz'.format(name))
        fab.run('env/bin/alembic upgrade head')
        fab.run('touch wsgi/lost-tracker.wsgi')


@fab.task
def clean():
    name = fab.local('python setup.py --fullname', capture=True)
    with fab.cd(REMOTE_FOLDER):
        fab.run('rm {0}.tar.gz'.format(name))
        fab.run('rm requirements.txt')


@fab.task
@fab.with_settings(user=REMOTE_USER)
def redeploy():
    name = fab.local('python setup.py --name', capture=True)
    with fab.cd(REMOTE_FOLDER):
        fab.run('env/bin/pip uninstall %s' % name)
    fab.execute(deploy)


@fab.task
@fab.with_settings(user=getuser())
def bootstrap():
    fab.run('mkdir -p %s' % REMOTE_FOLDER)
    fab.sudo('apt-get install aptitude')
    fab.sudo('aptitude update')
    fab.sudo('aptitude install -y '
             'apache2 libapache2-mod-wsgi python3-venv libpq-dev '
             'libffi-dev '
             'python3-dev python-dev libjpeg-dev build-essential '
             'postgresql')
    with fab.cd(REMOTE_FOLDER):
        fab.run('mkdir -p wsgi')
        fab.put('wsgi/lost-tracker.wsgi', '/tmp')
        fab.run('[ -f wsgi/lost-tracker.wsgi ] || mv /tmp/lost-tracker.wsgi',
                'wsgi')
        fab.run('[ -f /tmp/lost-tracker.wsgi ] && rm -f /tmp/lost-tracker.wsgi')
        fab.run('[ -d env ] || pyvenv env')
        fab.run('./env/bin/pip install -U pip alembic')
    fab.sudo('chown -R {0}:{0} {1}'.format(REMOTE_USER, REMOTE_FOLDER))


@fab.task
def alembic():
    "Run DB Migrations"
    with fab.settings(shell_env={'PYTHONWARNINGS': ''}):
        fab.local('./env/bin/alembic upgrade head')


@fab.task
def develop():
    """
    Sets up a new development environment. Should be run right after cloning
    the repo.
    """
    l = fab.local
    ini_file = '.mamerwiselen/lost-tracker/app.ini'

    l('[ -d env ] || virtualenv env')
    l('./env/bin/pip install "setuptools>=0.8"')  # needed by IMAPClient
    # some packages are unavailable on pypi :( -> Use requirements.txt
    l('./env/bin/pip install -r requirements.txt')
    l('./env/bin/pip install -e .[dev,test]')
    l('mkdir -p __libs__')

    with fab.lcd('__libs__'):
        l('[ -d plovr ] || '
          'git clone https://github.com/bolinfest/plovr.git')
        l('[ -d closure-library ] || '
          'git clone https://github.com/google/closure-library.git')

    with fab.lcd('__libs__/plovr'):
        l('git fetch')
        l('git checkout {}'.format(PLOVR_REVISION))

    with fab.lcd('__libs__/closure-library'):
        l('git fetch')
        l('git checkout {}'.format(CLOSURE_REVISION))

    l('mkdir -p .mamerwiselen/lost-tracker')

    with fab.settings(warn_only=True):
        ini_is_missing = l('[ -f ' + ini_file + ' ]').failed

    if ini_is_missing:
        print(clr.green('No INI file found. Please fill in the following '
                        'values:'))
        print('')
        print(clr.green('      Look at "app.ini.dist" for documentation.'))
        print('')
        print(clr.yellow('   The file will be stored in {}'.format(ini_file)))
        print(clr.yellow('   You can change this at any time. If you do, you '
                         'need to restart the application if it is still '
                         'running!'))
        print('')
        cfg = SafeConfigParser()
        cfg.read('app.ini.dist')
        for sect in cfg.sections():
            for opt in cfg.options(sect):
                curval = cfg.get(sect, opt)
                newval = fab.prompt('{}:{} = '.format(
                    clr.green(sect),
                    clr.blue(opt, bold=True)), default=curval)
                cfg.set(sect, opt, newval)
        cfg.write(open(ini_file, 'w'))
        print(clr.green('>>> New config file created in ' + ini_file))
    else:
        print(clr.white('=== Kept old config file from ' + ini_file, bold=True))
    fab.execute(babel_compile)
    print(clr.green('Applying database migrations...'))
    print(clr.yellow('NOTE: The DB must exist, and the URL in %r must be '
                     'correct. I will pause now to give you a chance to fix '
                     'that, if needed. Press ENTER when ready.' % ini_file))
    print(clr.yellow('This step can always be re-executed by running '
                     '"fab alembic"'))
    fab.prompt('Press ENTER when ready...')
    fab.execute(alembic)
    print(clr.green('Done!'))


@fab.task
def build():
    """
    Compile JS sources.
    """
    from os import stat
    from json import load
    with open('plovr-config.js') as fp:
        plovr_config = load(fp)

    input_file = plovr_config['inputs']
    output_file = plovr_config['output-file']

    stat_in = stat(input_file)

    if exists(output_file):
        stat_out = stat(output_file)
        needs_build = stat_in.st_mtime > stat_out.st_mtime
    else:
        needs_build = True

    if not needs_build:
        print(clr.blue(input_file),
              clr.green('is older than'),
              clr.blue(output_file),
              clr.green('Assuming it has not changed and skipping '
                        'closure-build!'))
        return
    else:
        print(clr.blue(input_file),
              clr.green('has changed'),
              clr.green('recompiling to'),
              clr.blue(output_file))

    fab.local('docker run -v {}:/app --rm {} build /app/plovr-config.js'.format(
        dirname(__file__),
        DOCKER_PLOVR,
    ))


@fab.task
def extract_pot():
    fab.local('./env/bin/pybabel extract '
              '-F babel.cfg -o messages.pot lost_tracker')


@fab.task
def babel_init(locale):
    """
    Initialise support for a new locale.
    """
    fab.local('./env/bin/pybabel init '
              '-i messages.pot -d lost_tracker/translations -l {}'.format(
                  locale))


@fab.task
def babel_compile():
    """
    Compile all translations into the application.
    """
    fab.local('./env/bin/pybabel compile -f -d lost_tracker/translations')


@fab.task
def babel_update():
    """
    Extracts translations and updates the pot template.
    """
    fab.execute(extract_pot)
    fab.local('./env/bin/pybabel update '
              '-i messages.pot '
              '-d lost_tracker/translations')


def _get_psql_params():
    '''
    return a list of PostgreSQL parameters. These parameters are usable for
    commands like ``psql`` or ``pg_dump``. It uses a config-file containing a
    ``db.dsn`` option to determine those parameters.
    '''
    from urlparse import urlparse
    with fab.cd(REMOTE_FOLDER), fab.hide('stdout', 'running', 'stderr'):
        dsn = fab.run(
            './env/bin/python -c "'
            'from config_resolver import Config; '
            'import logging; logging.basicConfig(level=logging.ERROR); '
            "config = Config('mamerwiselen', 'lost-tracker'); "
            "print(config.get('db', 'dsn'))"
            '"'
        ).strip()
    if not dsn:
        fab.abort(clr.red('Unable to get DSN from config file!'))

    # psql does not support SQLAlchemy Style DSNs so we need to parse it and
    # reconstruct a proper command
    dsn_detail = urlparse(dsn)
    psql_params = ['-U', dsn_detail.username]
    if dsn_detail.port:
        psql_params.extend(['-p', dsn_detail.port])
    if dsn_detail.hostname and dsn_detail.hostname != 'localhost':
        psql_params.extend(['-h', dsn_detail.hostname])
    psql_params.append(dsn_detail.path[1:])
    return psql_params


@fab.task
def pull_db():
    psql_params = _get_psql_params()
    with fab.cd(REMOTE_FOLDER):
        tempfile = fab.run('mktemp --tmpdir=.')
        full_cmd = ['pg_dump', '--clean', '-f', tempfile] + psql_params
        fab.run(' '.join(full_cmd))
        retrieved_files = fab.get(tempfile)
        fab.run('rm %s' % tempfile)
        if len(retrieved_files) != 1:
            fab.abort(clr.red('Expected to retrieve exactly one file. '
                              'But got %d!' % len(retrieved_files)))
        local_file = next(iter(retrieved_files))
        fab.local('psql -X -q -f %s lost_tracker_2016' % local_file)
        fab.local('rm %s' % local_file)


@fab.task
def serve_plovr():
    """
    Run JS development server.
    """
    fab.local('docker run -v {}:/app --rm {} serve /app/plovr-config.js'.format(
        dirname(__file__),
        DOCKER_PLOVR,
    ))


@fab.task
def serve_web():
    """
    Run development server.
    """
    fab.local('./env/bin/python lost_tracker/main.py')
