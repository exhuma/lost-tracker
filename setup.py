from setuptools import setup, find_packages
from pkg_resources import resource_string
VERSION = resource_string('lost_tracker', 'version.txt').decode('ascii')
setup(
    name="lost-tracker",
    version=VERSION.strip(),
    packages=find_packages(),
    install_requires=[
        'config-resolver >= 4.2, <5.0',
        'envelopes==0.4',
        'facebook-sdk>=1.0.0a0',
        'flask-babel==0.9',
        'flask-security==1.7.5',
        'flask-social>=1.6.2',
        'flask-sqlalchemy==2.1',
        'flask==0.10.1',
        'google-api-python-client==1.5.0',
        'gouge >= 1.1, <2.0',
        'imapclient==1.0.1',
        'markdown==2.6.5',
        'pillow==2.8.1',
        'psycopg2==2.5.2',
        'python-twitter>=3.0rc1',
        'pytz',
        'qrcode==5.2.2',
        'requests==2.6.0',
        'sqlalchemy==0.9.3',
    ],
    extras_require={
        'dev': [
            'alembic',
        ],
        'test': [
            'pytest',
            'pytest-xdist',
            'mock'
        ]
    },
    entry_points={
        'console_scripts': [
            'fetch_photos = lost_tracker.mailfetcher:run_cli',
        ],
    },
    include_package_data=True,
    author="Michel Albert",
    author_email="michel@albert.lu",
    description="Tracker for Lost in the Darkness",
    license="BSD",
    url="http://exhuma.github.com/lost-tracker",
)
