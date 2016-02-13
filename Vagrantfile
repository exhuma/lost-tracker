# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

$script = <<SCRIPT
#!/usr/bin/env bash

BASEDIR=/opt/lost-tracker
ENVDIR=${BASEDIR}/env

# XXX echo "[***] Running system setup..."
# XXX aptitude update
# XXX aptitude -y install \
# XXX     apache2 \
# XXX     build-essential \
# XXX     libapache2-mod-wsgi \
# XXX     libjpeg-dev \
# XXX     libpng12-0 \
# XXX     libpq-dev \
# XXX     libxml2-dev \
# XXX     libxslt1-dev \
# XXX     python3 \
# XXX     python3-dev \
# XXX     python3.4-venv \
# XXX     vim-nox
# XXX 
# XXX mkdir ${BASEDIR}
# XXX pyvenv-3.4 ${ENVDIR}
# XXX useradd -r -d ${BASEDIR} -m lostlu
# XXX chown -R lostlu ${BASEDIR}

echo "[***] Installing the application..."

${ENVDIR}/bin/pip install -e /vagrant
SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu-VAGRANTSLASH-trusty64"
  # config.vm.box_url = "http://files.vagrantup.com/precise32.box"
  config.vm.network :forwarded_port, guest: 8080, host: 8080
  config.vm.provision "shell", inline: $script
end
