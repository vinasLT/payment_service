#!/bin/bash
set -e

echo "⏳ Waiting for DB"
until pg_isready -h "$PAYMENT_DB_HOST" -p "$PAYMENT_DB_PORT" -U "$PAYMENT_DB_USER"; do
  sleep 1
done
echo "📦 Applying migrations"
alembic upgrade head

echo "🚀 Start App"
exec "$@"