from configparser import SafeConfigParser
from getpass import getuser
from os.path import dirname, exists

from fabric import Connection
from invoke import Context, task

from blessings import Terminal

ROLES = {
    'prod': '178.62.219.167',
}


REMOTE_FOLDER = '/var/www/lost.lu/www'
REMOTE_USER = 'lost_tracker'
DOCKER_PLOVR = 'exhuma/lost-tracker-closure'


@task
def deploy(ctx):  # type: ignore
    build(ctx)
    babel_compile(ctx)
    upload(ctx)
    with Connection(ROLES['prod'], user=REMOTE_USER) as conn:
        install(conn)
        clean(conn)


@task
def publish(ctx):  # type: ignore
    ctx.run('docker login')
    ctx.run('docker push malbert/lost-tracker:latest')


# @task
# def install():
#     name = fab.local('python setup.py --fullname', capture=True)
#     with fab.cd(REMOTE_FOLDER):
#         fab.run('env/bin/pip install alembic')
#         fab.run('env/bin/pip install -r requirements.txt')
#         fab.run('env/bin/pip install {0}.tar.gz'.format(name))
#         fab.run('env/bin/alembic upgrade head')
#         fab.run('touch wsgi/lost-tracker.wsgi')
# 
# 
# @fab.task
# def clean():
#     name = fab.local('python setup.py --fullname', capture=True)
#     with fab.cd(REMOTE_FOLDER):
#         fab.run('rm {0}.tar.gz'.format(name))
#         fab.run('rm requirements.txt')
# 
# 
# @fab.task
# @fab.with_settings(user=REMOTE_USER)
# def redeploy():
#     name = fab.local('python setup.py --name', capture=True)
#     with fab.cd(REMOTE_FOLDER):
#         fab.run('env/bin/pip uninstall %s' % name)
#     fab.execute(deploy)
# 
# 
# @fab.task
# @fab.with_settings(user=getuser())
# def bootstrap():
#     fab.run('mkdir -p %s' % REMOTE_FOLDER)
#     fab.sudo('apt-get install aptitude')
#     fab.sudo('aptitude update')
#     fab.sudo('aptitude install -y '
#              'apache2 libapache2-mod-wsgi python3-venv libpq-dev '
#              'libffi-dev '
#              'python3-dev python-dev libjpeg-dev build-essential '
#              'postgresql')
#     with fab.cd(REMOTE_FOLDER):
#         fab.run('mkdir -p wsgi')
#         fab.put('wsgi/lost-tracker.wsgi', '/tmp')
#         fab.run('[ -f wsgi/lost-tracker.wsgi ] || mv /tmp/lost-tracker.wsgi',
#                 'wsgi')
#         fab.run('[ -f /tmp/lost-tracker.wsgi ] && rm -f /tmp/lost-tracker.wsgi')
#         fab.run('[ -d env ] || pyvenv env')
#         fab.run('./env/bin/pip install -U pip alembic')
#     fab.sudo('chown -R {0}:{0} {1}'.format(REMOTE_USER, REMOTE_FOLDER))


@task
def alembic(ctx):  # type: ignore
    "Run DB Migrations"
    ctx.run('./env/bin/alembic upgrade head', env={'PYTHONWARNINGS': ''})


@task
def develop(ctx):  # type: ignore
    """
    Sets up a new development environment. Should be run right after cloning
    the repo.
    """
    l = ctx.run
    ini_file = '.mamerwiselen/lost-tracker/app.ini'

    l('[ -d env ] || python3 -m venv env')
    l('./env/bin/pip install "setuptools>=0.8"')  # needed by IMAPClient
    # some packages are unavailable on pypi :( -> Use custom-requirements.txt
    l('./env/bin/pip install -r custom-requirements.txt')
    l('./env/bin/pip install -e .[dev,test]')
    l('docker pull {}'.format(DOCKER_PLOVR))
    l('mkdir -p .mamerwiselen/lost-tracker')

    ini_is_missing = l('[ -f ' + ini_file + ' ]').failed

    term = Terminal()
    if ini_is_missing:
        print(term.green('No INI file found. Please fill in the following '
                         'values:'))
        print('')
        print(term.green('      Look at "app.ini.dist" for documentation.'))
        print('')
        print(term.yellow('   The file will be stored in {}'.format(ini_file)))
        print(term.yellow('   You can change this at any time. If you do, you '
                          'need to restart the application if it is still '
                          'running!'))
        print('')
        cfg = SafeConfigParser()
        cfg.read('app.ini.dist')
        for sect in cfg.sections():
            for opt in cfg.options(sect):
                curval = cfg.get(sect, opt)
                newval = input('{}:{} = '.format(
                    term.green(sect),
                    term.bold_blue(opt)))
                if not newval.strip():
                    newval = curval
                cfg.set(sect, opt, newval)
        cfg.write(open(ini_file, 'w'))
        print(term.green('>>> New config file created in ' + ini_file))
    else:
        print(term.bold_white('=== Kept old config file from ' + ini_file))
    babel_compile(ctx)
    print(term.green('Applying database migrations...'))
    print(term.yellow('NOTE: The DB must exist, and the URL in %r must be '
                     'correct. I will pause now to give you a chance to fix '
                     'that, if needed. Press ENTER when ready.' % ini_file))
    print(term.yellow('This step can always be re-executed by running '
                     '"fab alembic"'))
    input('Press ENTER when ready...')
    alembic(ctx)
    print(term.green('Done!'))


@task
def build_js(ctx):  # type: ignore
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

    term = Terminal()
    if not needs_build:
        print(term.blue(input_file),
              term.green('is older than'),
              term.blue(output_file),
              term.green('Assuming it has not changed and skipping '
                         'closure-build!'))
        return
    else:
        print(term.blue(input_file),
              term.green('has changed'),
              term.green('recompiling to'),
              term.blue(output_file))

    ctx.run('docker run -v {}:/app --rm {} build /app/plovr-config.js'.format(
        dirname(__file__),
        DOCKER_PLOVR,
    ))

@task
def build(ctx):  # type: ignore
    """
    Compile JS sources.
    """
    from os import listdir
    build_js(ctx)
    ctx.run('rm -rf dist')
    ctx.run('python setup.py sdist')
    files = [fname for fname in listdir('dist') if not fname.startswith('.')]
    assert len(files) == 1
    ctx.run('mv dist/%s dist/docker.tar.gz' % files[0])
    ctx.run(
        'docker build -t malbert/lost-tracker:2019 -t malbert/lost-tracker:latest .')



@task
def extract_pot(ctx):  # type: ignore
    ctx.run('./env/bin/pybabel extract '
            '-F babel.cfg -o messages.pot lost_tracker')


@task
def babel_init(ctx, locale):  # type: ignore
    """
    Initialise support for a new locale.
    """
    ctx.run('./env/bin/pybabel init '
            '-i messages.pot -d lost_tracker/translations -l {}'.format(
                locale))


@task
def babel_compile(ctx):  # type: ignore
    """
    Compile all translations into the application.
    """
    ctx.run('./env/bin/pybabel compile -f -d lost_tracker/translations')


@task
def babel_update(ctx):  # type: ignore
    """
    Extracts translations and updates the pot template.
    """
    extract_pot(ctx)
    ctx.run('./env/bin/pybabel update '
            '-i messages.pot '
            '-d lost_tracker/translations')


# def _get_psql_params():
#     '''
#     return a list of PostgreSQL parameters. These parameters are usable for
#     commands like ``psql`` or ``pg_dump``. It uses a config-file containing a
#     ``db.dsn`` option to determine those parameters.
#     '''
#     from urlparse import urlparse
#     with fab.cd(REMOTE_FOLDER), fab.hide('stdout', 'running', 'stderr'):
#         dsn = fab.run(
#             './env/bin/python -c "'
#             'from config_resolver import Config; '
#             'import logging; logging.basicConfig(level=logging.ERROR); '
#             "config = Config('mamerwiselen', 'lost-tracker'); "
#             "print(config.get('db', 'dsn'))"
#             '"'
#         ).strip()
#     if not dsn:
#         fab.abort(clr.red('Unable to get DSN from config file!'))
# 
#     # psql does not support SQLAlchemy Style DSNs so we need to parse it and
#     # reconstruct a proper command
#     dsn_detail = urlparse(dsn)
#     psql_params = ['-U', dsn_detail.username]
#     if dsn_detail.port:
#         psql_params.extend(['-p', dsn_detail.port])
#     if dsn_detail.hostname and dsn_detail.hostname != 'localhost':
#         psql_params.extend(['-h', dsn_detail.hostname])
#     psql_params.append(dsn_detail.path[1:])
#     return psql_params
# 
# 
# @fab.task
# def pull_db():
#     psql_params = _get_psql_params()
#     with fab.cd(REMOTE_FOLDER):
#         tempfile = fab.run('mktemp --tmpdir=.')
#         full_cmd = ['pg_dump', '--clean', '-f', tempfile] + psql_params
#         fab.run(' '.join(full_cmd))
#         retrieved_files = fab.get(tempfile)
#         fab.run('rm %s' % tempfile)
#         if len(retrieved_files) != 1:
#             fab.abort(clr.red('Expected to retrieve exactly one file. '
#                               'But got %d!' % len(retrieved_files)))
#         local_file = next(iter(retrieved_files))
#         fab.local('psql -X -q -f %s lost_tracker_2016' % local_file)
#         fab.local('rm %s' % local_file)


@task
def serve_plovr(ctx):  # type: ignore
    """
    Run JS development server.
    """
    ctx.run('docker run -p 9810:9810 -v {}:/app --rm {} '
            'serve /app/plovr-config.js'.format(
                dirname(__file__),
                DOCKER_PLOVR,
            ))


@task
def serve_web(ctx):  # type: ignore
    """
    Run development server.
    """
    ctx.run('./env/bin/python lost_tracker/main.py')
