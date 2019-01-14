#!/bin/bash
coverage run --source="./src" src/manage.py test
coverage report
coverage xml

