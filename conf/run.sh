#/bin/bash
gunicorn pasture.configs.wsgi:application --bind 0.0.0.0:$PORT
