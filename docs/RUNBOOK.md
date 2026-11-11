# Runbook de Produção — HDTO

## 1. Pré-requisitos na VPS

- Docker e Docker Compose.
- Domínio apontando para a VPS.
- PostgreSQL com PostGIS na porta **5434**.

Criar banco e role:

```sql
CREATE ROLE hdto_app LOGIN PASSWORD 'senha-forte' NOSUPERUSER NOCREATEDB;
CREATE DATABASE hdto_db OWNER hdto_app ENCODING 'UTF8';
\c hdto_db
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

Garantir que o Postgres aceite conexão do container (bind/bridge e `pg_hba.conf`) e que o firewall permita apenas a VPS/rede Docker.

## 2. Configuração

```bash
git clone git@github.com:IOTABE/hdto.git
cd hdto
cp .env.example .env
```

Preencher:

```env
DEBUG=False
SECRET_KEY=...
ALLOWED_HOSTS=hdto.exemplo.org.br
CSRF_TRUSTED_ORIGINS=https://hdto.exemplo.org.br
FIELD_ENCRYPTION_KEY=...   # Fernet
CPF_HASH_PEPPER=...
DB_NAME=hdto_db
DB_USER=hdto_app
DB_PASSWORD=...
DB_HOST=host.docker.internal
DB_PORT=5434
DB_SSLMODE=prefer
CENSO_K_ANONIMATO=5
```

Configurar o proxy reverso no Nginx do host apontando para `127.0.0.1:8006` (exemplo na seção 3).

Gerar chaves:

```bash
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
uv run python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 3. Deploy

```bash
./scripts/deploy.sh
```

O script constrói a imagem, aplica migrações, coleta estáticos e sobe apenas o serviço `web` (removendo containers órfãos). O app fica acessível em `127.0.0.1:8006`.

Exemplo de bloco Nginx (proxy reverso + TLS via Certbot):

```nginx
server {
    listen 80;
    server_name hdto.exemplo.org.br;
    location / { return 301 https://$host$request_uri; }
}

server {
    listen 443 ssl;
    server_name hdto.exemplo.org.br;

    ssl_certificate     /etc/letsencrypt/live/hdto.exemplo.org.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hdto.exemplo.org.br/privkey.pem;

    client_max_body_size 10m;

    location / {
        proxy_pass http://127.0.0.1:8006;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Após alterar o Nginx: `sudo nginx -t && sudo systemctl reload nginx`. O deploy pode recarregar automaticamente com `RELOAD_NGINX=1 ./scripts/deploy.sh`.

Verificações:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f web
curl -fsS https://hdto.exemplo.org.br/health/
```

## 4. Primeira carga

```bash
# superusuário
docker compose -f docker-compose.prod.yml run --rm web python manage.py createsuperuser

# malha municipal do IBGE (139 municípios)
docker compose -f docker-compose.prod.yml run --rm web up

# termo de consentimento vigente
docker compose -f docker-compose.prod.yml run --rm web python manage.py shell -c \
  "from apps.members.models import TermoVersao; TermoVersao.objects.get_or_create(versao='1.0', defaults={'texto': '...', 'vigente': True})"

# associações regionais e usuários iniciais no /admin/
```

## 5. Backup e restauração

Backup diário (cron):

```cron
0 3 * * * pg_dump -h 127.0.0.1 -p 5434 -U hdto_app -Fc hdto_db > /var/backups/hdto_$(date +\%F).dump
```

Restauração:

```bash
pg_restore -h 127.0.0.1 -p 5434 -U hdto_app -d hdto_db --clean --if-exists /var/backups/hdto_2026-01-01.dump
docker compose -f docker-compose.prod.yml restart web
```

Backup da mídia: volume Docker `hdto_media` (`docker run --rm -v hdto_media:/data ... tar`).

## 6. Operação

- Logs: `docker compose -f docker-compose.prod.yml logs -f web`.
- Migrações manuais: `docker compose ... run --rm -e RUN_MIGRATIONS=0 web python manage.py migrate`.
- Coleta de estáticos: automática no entrypoint.
- Healthcheck: `GET /health/` (verifica banco).
- Atualização:

```bash
git pull
./scripts/deploy.sh
```

- Rollback: `git checkout <tag-anterior> && ./scripts/deploy.sh` (migrações podem exigir plano de reversão).

## 7. Diagnóstico

| Sintoma | Causa provável | Ação |
|---|---|---|
| `502` no Nginx | app não subiu | logs do `web`; checar `.env` |
| `could not connect to server` | Postgres/porta 5434 | testar `pg_isready -h VPS -p 5434`; `pg_hba.conf` |
| `GDAL not found` | imagem sem libs | rebuild da imagem |
| `FIELD_ENCRYPTION_KEY obrigatória` | variável ausente | preencher `.env` e reiniciar |
| mapa vazio | municípios não importados | rodar `importar_municipios_to` |
| erros de migração | schema divergente | `showmigrations`; avaliar restore |

## 8. Segurança

- TLS 1.3/HSTS via Nginx + settings de produção.
- CSP e `X-Frame-Options: DENY`.
- Argon2id para senhas.
- CPF cifrado e hash HMAC.
- Consentimento imutável também no banco (trigger PostgreSQL).
- Revisar `DEBUG=False` e segredos fora do repositório.
- Rotacionar `SECRET_KEY` exige reautenticação; rotação de `FIELD_ENCRYPTION_KEY` exige migração de dados.
