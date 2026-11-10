#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Construindo imagem"
docker compose -f docker-compose.prod.yml build

echo "==> Aplicando migrações"
docker compose -f docker-compose.prod.yml run --rm -e RUN_MIGRATIONS=0 web \
  python manage.py migrate --noinput

echo "==> Coletando estáticos"
docker compose -f docker-compose.prod.yml run --rm -e RUN_MIGRATIONS=0 web \
  python manage.py collectstatic --noinput

echo "==> Subindo serviços"
docker compose -f docker-compose.prod.yml up -d

echo "==> Status"
docker compose -f docker-compose.prod.yml ps
