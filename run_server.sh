#!/bin/bash

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser --noinput

gunicorn eth_swap_indexer.asgi
