#!/usr/bin/env bash

# This command will run an update on Janeway.

pip3 install -r requirements.txt
python3 src/manage.py backup
python3 src/manage.py migrate
python3 src/manage.py build_assets
python3 src/manage.py collectstatic --no-input
DJANGO_DEFAULT_SETTINGS=1 python3 src/manage.py compilemessages
python3 src/manage.py load_default_settings
python3 src/manage.py install_plugins
