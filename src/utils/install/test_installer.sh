#!/bin/sh

cd ../../
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py loaddata utils/install/roles.json
python3 manage.py install_journal --journal_name Test --journal_code tstj --base_url janeway.systems --delete
python3 manage.py createsuperuser --noinput --email noreply@example.com --username admin
python3 manage.py scrape_oai http://c21.openlibhums.org/jms/index.php/up/oai/ 1 1
