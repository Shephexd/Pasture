#/bin/bash
nginx
gunicorn pasture.configs.wsgi:application --bind unix/tmp/gunicorn.sock