from setuptools import setup, find_packages
setup(
    name="lost-tracker",
    version="1.2.8",
    packages=find_packages(),
    install_requires=[
        'Flask-SQLAlchemy==0.16',
        'Flask==0.9',
        'SQLAlchemy==0.8.0b2',
        'alembic==0.6.2',
        'config-resolver >= 4.2, <5.0',
        'mock==1.0.1',
        'psycopg2==2.4.6',
    ],
    include_package_data=True,
    author="Michel Albert",
    author_email="michel@albert.lu",
    description="Tracker for Lost in the Darkness",
    license="BSD",
    url="http://exhuma.github.com/lost-tracker",
)
