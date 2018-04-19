#!/bin/bash
set -e # everything must succeed.
echo "[-] install.sh"

python=$(which python3) # ll: /usr/bin/python3
py=${python##*/} # ll: python3

# check for python3
if [ ! -e "venv/bin/$py" ]; then
    echo "could not find venv/bin/$py, recreating venv"
    rm -rf venv
    $python -m venv venv
fi

if [ ! -e "app.cfg" ]; then
    cp example.cfg app.cfg
fi

source venv/bin/activate

pip install -r requirements.txt

python src/manage.py migrate --no-input

echo "[✓] install.sh"
