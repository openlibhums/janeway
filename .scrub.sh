#!/bin/bash
# scrub.sh uses the autopep8 tool to clean up whitespace and other small bits

# E261 = double space before inline comment
# E501 = don't squeeze lines to fix max length
# E302 = don't go crazy with the double whitespace between funcs
# E401 = don't put imports on separate lines
# E309 = don't put a blank line after class declaration

autopep8 \
    --in-place --recursive --aggressive \
    --ignore E501,E302,E261,E401,E309 \
    --exclude *.html \
    src/