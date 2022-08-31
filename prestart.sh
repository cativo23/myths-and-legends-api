#! /usr/bin/env bash

# Let the DB start
python /code/app/backend_pre_start.py

# Run migrations
alembic upgrade head

# Create initial data in DB
python /code/app/initial_data.py