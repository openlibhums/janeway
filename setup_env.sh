#!/bin/bash
source /usr/local/bin/virtualenvwrapper.sh

mkvirtualenv janeway -p python3
workon janeway
git clone git@github.com:BirkbeckCTP/janeway.git
cd janeway
pip install -r requirements.txt


