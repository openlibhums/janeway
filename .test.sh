#!/bin/bash
# assumes a venv exists and is activated
# assumes code is linted
# called by test.sh and Travis CI

set -e # everything must pass

args="$@"
module="src"
print_coverage=1
if [ ! -z "$args" ]; then
    module="$args"
    print_coverage=0
fi

# remove any old compiled python files
find src/ -name '*.pyc' -delete

coverage run --source='src/' --omit='*/tests/*,*/migrations/*' src/manage.py test "$module" --no-input
