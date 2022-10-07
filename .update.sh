#!/usr/bin/env bash
set -euo pipefail

# This command will run an update on Janeway.

pip3 install -r requirements.txt
python3 src/manage.py migrate
python3 src/manage.py build_assets
python3 src/manage.py collectstatic --no-input
DJANGO_SETTINGS_MODULE=1 python3 src/manage.py compilemessages
python3 src/manage.py load_default_settings
python3 src/manage.py update_repository_settings
python3 src/manage.py install_plugins
python3 src/manage.py update_translation_fields
echo "REMINDER: don't forget to restart your webserver!"
exit 0
