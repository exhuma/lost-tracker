#!/bin/bash

# Wait for the DB
sleep 3

python3 /materialize_config.py
chmod 600 /etc/mamerwiselen/lost-tracker/app.ini
(cd /alembic && alembic upgrade head)
gunicorn -w 4 -b "0.0.0.0:8080" "lost_tracker.main:make_app()"
