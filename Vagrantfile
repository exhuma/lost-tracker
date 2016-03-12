# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

$script = <<SCRIPT
#!/usr/bin/env bash

BASEDIR=/opt/lost-tracker
ENVDIR=${BASEDIR}/env

echo "[***] Running system setup..."
aptitude update
aptitude -y install \
    apache2 \
    build-essential \
    git \
    libapache2-mod-wsgi \
    libffi-dev \
    libjpeg-dev \
    libpng12-0 \
    libpq-dev \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    postgresql-server \
    python-dev \
    python-virtualenv \
    vim-nox

mkdir -p ${BASEDIR}
virtualenv ${ENVDIR}
# XXX pyvenv-3.4 ${ENVDIR}
# XXX useradd -r -d ${BASEDIR} -m lostlu
# XXX chown -R lostlu ${BASEDIR}

echo "[***] Installing the application..."

${ENVDIR}/bin/pip install -U pip
${ENVDIR}/bin/pip install -r /vagrant/requirements.txt
${ENVDIR}/bin/pip install -e /vagrant
SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/precise32"
  config.vm.network :forwarded_port, guest: 50000, host: 50000
  config.vm.network :forwarded_port, guest: 9810, host: 9810
  config.vm.provision "shell", inline: $script
end
