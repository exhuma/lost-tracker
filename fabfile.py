from __future__ import print_function
from ConfigParser import SafeConfigParser

import fabric.api as fab
import fabric.colors as clr

fab.env.roledefs = {
    'failover': ['lostlu@dozer.foobar.lu'],
    'prod': ['lost_tracker_backup@eurinfo.net'],
}


REMOTE_FOLDER = '/var/www/lost.lu/www'
PLOVR_REVISION = '9f12b6c'
PLOVR = 'plovr/build/plovr-{}.jar'.format(PLOVR_REVISION)
CLOSURE_REVISION = '57bdfe0093c'



@fab.task
@fab.roles('prod', 'failover')
def deploy():
    fab.execute(build)
    fab.execute(babel_compile)
    fab.execute(upload)
    fab.execute(install)
    fab.execute(clean)


@fab.task
def upload():
    fab.local('python setup.py sdist')
    name = fab.local('python setup.py --fullname', capture=True)
    with fab.cd(REMOTE_FOLDER):
        fab.put('dist/{0}.tar.gz'.format(name), '.')
        fab.put('alembic.ini', '.')
        fab.put('alembic', '.')
        fab.put('requirements.txt', '.')


@fab.task
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
def redeploy():
    name = fab.local('python setup.py --name', capture=True)
    with fab.cd(REMOTE_FOLDER):
        fab.run('env/bin/pip uninstall %s' % name)
    fab.execute(deploy)


@fab.task
def bootstrap():
    with fab.cd(REMOTE_FOLDER):
        fab.run('mkdir -p wsgi')
        fab.put('wsgi/lost-tracker.wsgi', 'wsgi')


@fab.task
def develop():
    """
    Sets up a new development environment. Should be run right after cloning
    the repo.
    """
    l = fab.local
    l('[ -d env ] || virtualenv env')
    l('./env/bin/pip uninstall lost_tracker || true')
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
        ini_exists = l('[ -f .mamerwiselen/lost-tracker/app.ini ]').failed

    if ini_exists:
        cfg = SafeConfigParser()
        cfg.read('app.ini.dist')
        for sect in cfg.sections():
            for opt in cfg.options(sect):
                curval = cfg.get(sect, opt)
                newval = fab.prompt('{}:{} = '.format(
                    clr.green(sect),
                    clr.blue(opt, bold=True)), default=curval)
                cfg.set(sect, opt, newval)
        cfg.write(open('.mamerwiselen/lost-tracker/app.ini', 'w'))
        print(clr.green('>>> New config file created in '
                        '.mamerwiselen/lost-tracker/app.ini'))
    else:
        print(clr.white('=== Kept old config file from '
                        '.mamerwiselen/lost-tracker/app.ini', bold=True))
    fab.execute(babel_compile)
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
    stat_out = stat(output_file)

    if stat_in.st_mtime <= stat_out.st_mtime:
        print(clr.blue(input_file),
              clr.green('is older than'),
              clr.blue(output_file),
              clr.green('Assuming it has not changed and skipping '
                        'closure-build!'))
        return

    fab.local('java -jar __libs__/{} build plovr-config.js'.format(PLOVR))


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
