#!/bin/bash
coverage run --omit=["*/migrations/*"] src/manage.py test
coverage report
coverage xml -o jenkins/coverage.xml

