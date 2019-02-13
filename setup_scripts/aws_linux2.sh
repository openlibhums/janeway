#!/bin/bash

# Uncomment lines below to also install httpd and mod_wsgi
sudo yum install gcc-c++ python3 python3-devel python-virtualenv libxslt-devel zlib-devel libffi-devel libjpeg-turbo-devel mariadb mariadb-devel git -y
# sudo yum install httpd httpd-devel -y
virtualenv -p python3 .janewayenv
source ~/.janewayenv/bin/activate
git clone https://github.com/BirkbeckCTP/janeway.git
cd janeway
pip3 install -r requirements.txt
# pip3 install mod_wsgi
