from setuptools import setup, find_packages
setup(
    name="lost-tracker",
    version=open('lost_tracker/version.txt').read().strip(),
    packages=find_packages(),
    install_requires=[
        'Flask',
        'alembic',
        'config-resolver',
        'psycopg2',
    ],
    include_package_data=True,
    author="Michel Albert",
    author_email="michel@albert.lu",
    description="Tracker for Lost in the Darkness",
    license="BSD",
    url="http://exhuma.github.com/lost-tracker",
)
