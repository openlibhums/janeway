#!/bin/bash

sudo apt-get install python3 python3-pip python-pip virtualenvwrapper -y
source /usr/local/bin/virtualenvwrapper.sh
sudo apt-get install libxml2-dev libxslt1-dev python3-dev zlib1g-dev lib32z1-dev libffi-dev libssl-dev libjpeg-dev libmysqlclient-dev mysql-client mysql-server git -y
mkvirtualenv janeway -p python3
workon janeway
git clone https://github.com/BirkbeckCTP/janeway.git
cd janeway
pip3 install -r requirements.txt
