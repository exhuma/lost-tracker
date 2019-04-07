from setuptools import setup, find_packages
from pkg_resources import resource_string
VERSION = resource_string('lost_tracker', 'version.txt').decode('ascii')
setup(
    name="lost-tracker",
    version=VERSION.strip(),
    packages=find_packages(),
    install_requires=[
        'config-resolver >= 4.2, <5.0',
        'envelopes',
        'flask < 1.0',
        'flask-babel',
        'flask-security',
        'flask-sqlalchemy',
        'gouge >= 1.1, <2.0',
        'imapclient',
        'markdown',
        'pillow',
        'psycopg2',
        'pytz',
        'qrcode',
        'requests',
        'sqlalchemy',
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
