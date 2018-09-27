#!/bin/bash

apt-get update -qq
apt-get install -y -qq python-dev python-pip git
/usr/bin/pip install -q --upgrade
/usr/bin/pip install -q invoke
curl -L https://get.docker.com/ | bash
sudo usermod -a -G docker vagrant
cd /vagrant/ui/ci
/usr/local/bin/invoke pythons
/usr/local/bin/invoke requirements
/usr/local/bin/invoke requirements --path /vagrant/requirements.txt
/usr/local/bin/invoke requirements --path /vagrant/revizor/requirements.txt
cd /vagrant
/usr/local/bin/invoke grid
echo 'export PYTHONPATH=$PYTHONPATH:/vagrant/revizor/src:/vagrant/ui' >> /home/vagrant/.bashrc
