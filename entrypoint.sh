#!/bin/bash
set -e

echo "Starting deployment checks..."

# Aspetta che il database sia pronto (opzionale, utile per docker-compose o ecs)
# echo "Waiting for postgres..."
# while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER
# do
#   echo "Waiting for postgres..."
#   sleep 2
# done

echo "Applying database migrations..."
alembic upgrade head

echo "Creating Super Admin (if not exists)..."
python create_super_admin.py

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips="*"
