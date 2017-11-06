#!/bin/bash

sudo apt-get install python3 python3-pip python-pip virtualenvwrapper -y
source /etc/bash_completion.d/virtualenvwrapper
sudo apt-get install libxml2-dev libxslt1-dev python3-dev zlib1g-dev lib32z1-dev libffi-dev libssl-dev libjpeg-dev default-libmysqlclient-dev mysql-client mysql-server git -y
mkvirtualenv janeway -p /usr/bin/python3
workon janeway
git clone https://github.com/BirkbeckCTP/janeway.git
cd janeway
pip3 install -r requirements.txt
