import fabric.api as fab


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
