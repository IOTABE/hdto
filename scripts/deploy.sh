#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE="docker compose -f docker-compose.prod.yml"

echo "==> Construindo imagem"
$COMPOSE build web

echo "==> Aplicando migrações"
$COMPOSE run --rm -e RUN_MIGRATIONS=0 web \
  python manage.py migrate --noinput

echo "==> Coletando estáticos"
$COMPOSE run --rm -e RUN_MIGRATIONS=0 web \
  python manage.py collectstatic --noinput

echo "==> Subindo aplicação"
# --remove-orphans remove containers antigos (ex.: caddy) que saíram do compose.
$COMPOSE up -d --remove-orphans web

if [ "${RELOAD_NGINX:-0}" = "1" ]; then
  echo "==> Recarregando Nginx"
  sudo nginx -t
  sudo systemctl reload nginx
fi

echo "==> Status"
$COMPOSE ps
