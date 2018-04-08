#!/bin/bash
# a wrapper around the '.test.sh' script that inits a venv if one not detected

set -e # everything must pass

echo "[-] .test.sh"

if [ ! -d venv ]; then
    echo "venv not found, creating"
    ./install.sh
fi

source venv/bin/activate

#./.test.sh || true

# run coverage test if tests pass
# only report coverage if we're running a complete set of tests

required_coverage=38 # bump this as coverage improves
covered=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')

coverage report # prints report
if [[ $covered < $required_coverage ]]; then
    echo
    echo "FAILED this project requires at least $required_coverage% coverage, got $covered%"
    echo
    exit 1
fi

echo "[✓] .test.sh"
