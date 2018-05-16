#!/bin/bash

apt-get update -qq
apt-get install -y -qq python-dev python-pip git
/usr/bin/pip install -q --upgrade pip==8.1.1
/usr/bin/pip install -q invoke
# pip install requests[security]
curl -L https://get.docker.com/ | bash
sudo usermod -a -G docker vagrant
cd /vagrant
/usr/local/bin/invoke pythons
/usr/local/bin/invoke requirements
export PATH=$PATH:/usr/local/pyenv/shims:/usr/local/pyenv/bin
$PATH
