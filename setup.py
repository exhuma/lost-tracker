from setuptools import setup, find_packages
setup(
    name="lost-tracker",
    version="1.2.8",
    packages=find_packages(),
    install_requires=[
        'Flask-Login==0.2.9',
        'Flask-SQLAlchemy==1.0',
        'Flask==0.10.1',
        'SQLAlchemy==0.9.3',
        'alembic==0.6.3',
        'config-resolver >= 4.2, <5.0',
        'envelopes==0.4',
        'envelopes==0.4',
        'flask-babel==0.9',
        'mock==1.0.1',
        'psycopg2==2.5.2',
        'requests==2.2.1'
    ],
    include_package_data=True,
    author="Michel Albert",
    author_email="michel@albert.lu",
    description="Tracker for Lost in the Darkness",
    license="BSD",
    url="http://exhuma.github.com/lost-tracker",
)
