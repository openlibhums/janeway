#!/bin/bash
# scrub.sh uses the autopep8 tool to clean up whitespace and other small bits

# E501 = don't squeeze lines to fix max length
# E401 = don't put imports on separate lines
# E309 = don't put a blank line after class declaration

autopep8 \
    --in-place --recursive --aggressive \
    --ignore E501,E401,E309 \
    --exclude *.html \
    src/