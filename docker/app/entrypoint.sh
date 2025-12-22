#!/bin/bash
set -e

echo "Running migrations..."
alembic upgrade head || echo "No migrations to run yet"

echo "Starting application..."
exec "$@"
