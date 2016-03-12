# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

$script = <<SCRIPT
#!/usr/bin/env bash

BASEDIR=/opt/lost-tracker
ENVDIR=${BASEDIR}/env
CONFDIR=${BASEDIR}/.mamerwiselen/lost-tracker

echo "[***] Running system setup..."
add-apt-repository -y ppa:webupd8team/java

echo debconf shared/accepted-oracle-license-v1-1 select true | \
  sudo debconf-set-selections
echo debconf shared/accepted-oracle-license-v1-1 seen true | \
    sudo debconf-set-selections

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
    oracle-java8-installer \
    postgresql \
    postgresql-client \
    python-dev \
    python-virtualenv \
    vim-nox

mkdir -p ${BASEDIR}
virtualenv ${ENVDIR}

echo "[***] Installing the application..."

${ENVDIR}/bin/pip install -U pip
${ENVDIR}/bin/pip install -r /vagrant/requirements.txt
${ENVDIR}/bin/pip install -e /vagrant[dev]

cp /vagrant/vagrant_resources/pg_hba.conf /etc/postgresql/9.1/main
service postgresql reload
createuser -U postgres -DRS lostlu
createdb -U postgres -O lostlu lostlu

mkdir -p ${CONFDIR}
cp -v /vagrant/vagrant_resources/app.ini ${CONFDIR}
(cd ${BASEDIR} && ${ENVDIR}/bin/alembic -c /vagrant/vagrant_resources/alembic.ini upgrade head)

chown -R vagrant ${BASEDIR}

echo "================================================================================"
echo " To run the servers, enter the VM using "vagrant ssh""
echo " next run:"
echo "   (cd ${BASEDIR} && ./env/bin/python /vagrant/lost_tracker/main.py)"
echo "   (cd /vagrant && java -jar __libs__/plovr/build/plovr-9f12b6c.jar serve plovr-config.js)"
echo ""
echo " BOTH COMMANDS MUST BE RUNNING!"
echo "================================================================================"
SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/precise32"
  config.vm.network :forwarded_port, guest: 50000, host: 50000
  config.vm.network :forwarded_port, guest: 9810, host: 9810
  config.vm.provision "shell", inline: $script
end
