from setuptools import setup, find_packages
setup(
   name = "lost-tracker",
   version = "1.0",
   packages = find_packages(),
   install_requires = [
      'flask',
      'flask-sqlalchemy',
      'sqlalchemy'
      ],
   author = "Michel Albert",
   author_email = "michel@albert.lu",
   description = "Tracker for Lost in the Darkness",
   license = "BSD",
   url = "http://exhuma.github.com/lost-tracker",
)
