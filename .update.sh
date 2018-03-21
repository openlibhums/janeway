#!/usr/bin/env bash

# This command will run an update on Janeway.
python3 src/manage.py backup
pip3 install -r requirements.txt
python3 src/manage.py migrate
python3 src/manage.py build_assets
python3 src/manage.py collectstatic --no-input
python3 src/manage.py sync_settings_to_journals
python3 src/manage.py install_plugins