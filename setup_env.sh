#!/bin/bash
source /usr/local/bin/virtualenvwrapper.sh

mkvirtualenv janeway -p python3
workon janeway
git clone https://github.com/BirkbeckCTP/janeway.git
cd janeway
pip3 install -r requirements.txt


