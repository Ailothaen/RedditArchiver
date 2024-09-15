#!/bin/bash
source /app/bin/activate
/app/bin/gunicorn --bind 0.0.0.0:5000 --workers 1 wsgi:app
