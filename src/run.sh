#!/bin/bash
source env/bin/activate
env/bin/gunicorn --bind unix:run/gunicorn.sock --workers 1 wsgi:app
