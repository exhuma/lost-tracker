from ConfigParser import SafeConfigParser

import fabric.api as fab
import fabric.colors as clr


fab.env.roledefs['prod'] = ['dozer.foobar.lu']


@fab.task
@fab.roles('prod')
def deploy():
    fab.local('python setup.py sdist')
    name = fab.local('python setup.py --fullname', capture=True)
    with fab.cd('/var/www/lost.lu/tracker'):
        fab.put('dist/{0}.tar.gz'.format(name), '.')
        fab.run('env/bin/pip install {0}.tar.gz'.format(name))
        fab.put('alembic.ini', '.')
        fab.put('alembic', '.')
        fab.run('LOST_TRACKER_SETTINGS=/var/www/lost.lu/tracker/siteconf.py '
                'env/bin/alembic upgrade head')
        fab.run('touch wsgi/lost-tracker.wsgi')
        #fab.run('rm {0}.tar.gz'.format(name))


@fab.task
@fab.roles('prod')
def bootstrap():
    deploy()
    with fab.cd('/var/www/lost.lu/tracker'):
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
    l('./env/bin/pip install -e .')
    l('mkdir -p __libs__')

    with fab.lcd('__libs__'):
        l('[ -f plovr-81ed862.jar ] || '
          'wget https://plovr.googlecode.com/files/plovr-81ed862.jar')
        l('[ -d closure-library ] || '
          'git clone https://code.google.com/p/closure-library/')

    with fab.lcd('__libs__/closure-library'):
        l('git pull')

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
    print(clr.green('Done!'))


@fab.task
def build():
    """
    Compile JS sources.
    """
    fab.local('java -jar __libs__/plovr-81ed862.jar build plovr-config.js')
