from setuptools import setup, find_packages
from pkg_resources import resource_string
version = resource_string('lost_tracker', 'version.txt').decode('ascii')
setup(
    name="lost-tracker",
    version=version.strip(),
    packages=find_packages(),
    install_requires=[
        'Flask-Login==0.2.9',
        'Flask-SQLAlchemy==1.0',
        'Flask==0.10.1',
        'IMAPClient==0.12',
        'Pillow==2.8.1',
        'SQLAlchemy==0.9.3',
        'config-resolver >= 4.2, <5.0',
        'envelopes==0.4',
        'flask-babel==0.9',
        'psycopg2==2.5.2',
        'requests==2.6.0',
    ],
    extras_require={
        'dev': [
            'alembic',
        ],
        'test': [
            'pytest',
            'pytest-xdist'
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
