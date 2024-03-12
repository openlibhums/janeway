#!/bin/bash
coverage run --omit=["*/migrations/*"] src/manage.py $1
coverage report
coverage xml -o jenkins/coverage.xml

