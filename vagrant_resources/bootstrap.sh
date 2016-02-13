#!/usr/bin/env bash 

BASEDIR=/opt/lost-tracker
ENVDIR=${BASEDIR}/env

echo "[***] Running system setup..."
aptitude update
aptitude -y install \
    apache2 \
    build-essential \
    libapache2-mod-wsgi \
    libjpeg-dev \
    libpng12-0 \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    python3 \
    python3-dev \
    vim-nox
pip install virtualenv

mkdir ${BASEDIR}
virtualenv ${ENVDIR}
useradd -r -d ${BASEDIR} -m lostlu
chown -R lostlu ${BASEDIR}

echo "[***] Installing the application..."

${ENVDIR}/bin/pip install -e /vagrant
