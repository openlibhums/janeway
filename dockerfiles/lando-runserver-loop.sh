#!/bin/sh

set -u

while true; do
  python3 /app/src/manage.py runserver 0.0.0.0:8000 -v 3 --noreload
  echo "Janeway runserver exited, restarting in 2 seconds..."
  sleep 2
done
