# Plano de Construção — Plataforma Homens Batistas do Tocantins (HDTO)

> Documento derivado do `docs/PRD Homens Batistas do Tocantins.md`.
> Objetivo: especificar os passos de criação do app, a arquitetura, os modelos e o roadmap de execução.
>
> Stack definida: **uv** (ambiente/dependências) · **Python 3.12** · **Django 5.2 LTS** · **SQLite/SpatiaLite (dev)** · **PostgreSQL + PostGIS (prod, VPS porta 5434)** · **Docker (app)**.

---

## 1. Resumo do produto

Plataforma web (site público + backoffice + APIs analíticas) para a liderança estadual da CBT/UMHB-TO, coordenadores associacionais, diretores locais e membros. Módulos:

| Módulo | Entrega principal | Origem no PRD |
|---|---|---|
| Institucional | Páginas de história/valores, ER/ERV/HD, notícias e galerias | §§ 3 |
| Governança | RBAC em 4 níveis e escopo hierárquico | § 2 |
| Cadastros | Associação → Igreja → Organização → Membro | § 4 |
| Censo | Coleta censitária + consentimento LGPD | §§ 5 e 8 |
| Dashboard | Indicadores, pirâmide etária, banco vocacional | § 5 |
| Geo/GIS | Mapa dos 139 municípios, clusters, filtros por raio | § 6 |
| Eventos | Calendário, inscrição, QR Code, ICS, rotas | § 3 |
| Privacidade | Portal do titular, revogação e expurgo | § 8 |

---

## 2. Decisões arquiteturais

| Tema | Decisão | Justificativa |
|---|---|---|
| Framework | Django 5.2 LTS + Django REST Framework | Admin/ORM maduros, SSRF-safe, ecossistema GeoDjango |
| Templates | Django Templates + HTMX + Alpine.js + Tailwind (build local) | Atende orçamento de < 1,5 MB e SEO do portal público |
| Mapa | Leaflet + Leaflet.markercluster, GeoJSON via API | Leve, sem chave paga, bom em 4G |
| Gráficos | Chart.js (ECharts opcional) consumindo endpoints agregados | Recalcula filtros sem recarregar página |
| Banco dev | SQLite + extensão SpatiaLite | Paridade GeoDjango sem subir Postgres local |
| Banco prod | PostgreSQL + PostGIS na VPS (porta 5434) | Consultas espaciais e metas < 400 ms |
| Arquivos | Volume Docker para `media/`; estáticos com WhiteNoise | Simples, sem S3 obrigatório |
| Assíncrono | Management commands + cron (Celery/Redis opcional) | Evita complexidade prematura |
| Auth | User customizado com e-mail; Argon2id | PRD exige Argon2id |
| LGPD | Campos sensíveis cifrados + CPF com hash HMAC | Unicidade sem expor o dado |
| Consentimento | Tabela append-only + trigger de proteção | Imutabilidade exigida no PRD |

### Fluxo hierárquico

```text
Associação Regional (N)
  └── Igreja / Congregação (N)  [igreja_mae para congregações sem CNPJ]
        └── Organização Local (HD | ERV | ER)  [no máximo 1 de cada]
              └── Membro (N)  [≥ 1 organização ativa]
                    ├── Responsável Legal (se < 18 anos)
                    └── Consentimento (append-only)
```

---

## 3. Pré-requisitos e verificações na VPS

Antes de codificar, validar:

- [ ] PostgreSQL acessível na porta **5434** (local ou IP privado).
- [ ] Extensão **PostGIS** instalada (`CREATE EXTENSION postgis;`).
- [ ] Criar role e database dedicados:
  ```sql
  CREATE ROLE hdto_app LOGIN PASSWORD '...' NOSUPERUSER NOCREATEDB;
  CREATE DATABASE hdto_db OWNER hdto_app ENCODING 'UTF8';
  \c hdto_db
  CREATE EXTENSION IF NOT EXISTS postgis;
  CREATE EXTENSION IF NOT EXISTS pg_trgm;
  ```
- [ ] Confirmar se o Postgres aceita conexões do container Docker (bind em `0.0.0.0` ou bridge, `pg_hba.conf`) e liberar firewall apenas para a rede do Docker/VPS.
- [ ] Definir domínio e TLS (Caddy/Nginx + Let's Encrypt).
- [ ] Obter a lista oficial das **associações regionais** da CBT e os dados base.
- [ ] Baixar malha municipal do TO (139 municípios) do IBGE (GeoJSON/Shapefile).

> Se o PostGIS não estiver disponível na VPS, o plano B é manter `latitude`/`longitude` decimais e fazer raio/distância por Haversine em Python/SQL. O recomendado é PostGIS.

---

## 4. Estrutura de pastas

```text
hdto/
├── manage.py
├── pyproject.toml
├── uv.lock
├── .python-version              # 3.12
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml           # dev (SQLite)
├── docker-compose.prod.yml      # prod (Postgres externo 5434)
├── Caddyfile
├── config/
│   ├── asgi.py / wsgi.py
│   ├── urls.py
│   └── settings/{base,dev,prod}.py
├── apps/
│   ├── core/          # mixins, base models, auditoria, utils
│   ├── accounts/      # User, RBAC, perfis
│   ├── institutions/  # Associação, Igreja, Organização
│   ├── members/       # Membro, Responsável, Consentimento
│   ├── census/        # Respostas censitárias + agregações
│   ├── events/        # Eventos, inscrições, QR, ICS
│   ├── content/       # Notícias, galerias, páginas
│   ├── geo/           # Municípios, importação IBGE, mapa
│   ├── dashboard/     # Serviços de indicadores e endpoints
│   └── api/           # Roteamento DRF (opcional, se não usar por app)
├── templates/
├── static/src/        # Tailwind, JS, ícones
├── locale/            # pt-BR
├── tests/
└── docs/
```

---

## 5. Bootstrap com `uv` (Fase 1)

```bash
# 1. Inicialização
git init
uv init --python 3.12
uv python pin 3.12

# 2. Dependências de produção
uv add "django>=5.2,<5.3" djangorestframework "psycopg[binary]" \
       django-environ whitenoise pillow qrcode argon2-cffi cryptography \
       django-filter gunicorn

# 3. Dependências de desenvolvimento
uv add --dev pytest pytest-django pytest-cov factory-boy ruff pre-commit \
           django-debug-toolbar

# 4. Projeto e apps
uv run django-admin startproject config .
mkdir -p apps && touch apps/__init__.py
uv run python manage.py startapp core apps/core
uv run python manage.py startapp accounts apps/accounts
uv run python manage.py startapp institutions apps/institutions
uv run python manage.py startapp members apps/members
uv run python manage.py startapp census apps/census
uv run python manage.py startapp events apps/events
uv run python manage.py startapp content apps/content
uv run python manage.py startapp geo apps/geo
uv run python manage.py startapp dashboard apps/dashboard
```

Ajustes obrigatórios em cada `apps/<app>/apps.py`: `name = "apps.<app>"`. Criar `apps/<app>/urls.py` quando houver rotas.

`pyproject.toml` (trechos relevantes):

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.dev"
python_files = ["test_*.py", "*_test.py"]
addopts = "--cov=apps --cov-report=term-missing"
```

### Dependências de sistema para GeoDjango

- **Dev (host Linux):** `libgdal-dev libgeos-dev libproj-dev libsqlite3-mod-spatialite`
- **Imagem Docker:** mesmas libs em runtime (`gdal-bin libgeos-c1v5 libproj25 libpq5`).

---

## 6. Configuração de settings

`config/settings/base.py` (essencial):

```python
import environ
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "rest_framework",
    "django_filters",
    "apps.core",
    "apps.accounts",
    "apps.institutions",
    "apps.members",
    "apps.census",
    "apps.events",
    "apps.content",
    "apps.geo",
    "apps.dashboard",
]

AUTH_USER_MODEL = "accounts.User"
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Araguaina"
USE_TZ = True

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

# Criptografia de campos sensíveis (chave em base64 no .env)
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY")
CPF_HASH_PEPPER = env("CPF_HASH_PEPPER")

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Segurança
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
```

`config/settings/dev.py`:

```python
from .base import *
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.spatialite",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
SPATIALITE_LIBRARY_PATH = "mod_spatialite"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

`config/settings/prod.py`:

```python
from .base import *
DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST", default="host.docker.internal"),
        "PORT": env("DB_PORT", default="5434"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {"sslmode": env("DB_SSLMODE", default="prefer")},
    }
}

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
```

`.env.example`:

```env
DEBUG=True
SECRET_KEY=troque-me
ALLOWED_HOSTS=localhost,127.0.0.1
FIELD_ENCRYPTION_KEY=base64-32-bytes
CPF_HASH_PEPPER=segredo-hmac

DB_NAME=hdto_db
DB_USER=hdto_app
DB_PASSWORD=troque-me
DB_HOST=host.docker.internal
DB_PORT=5434
DB_SSLMODE=prefer

CSRF_TRUSTED_ORIGINS=https://hdto.exemplo.org.br
```

> Gere as chaves:
> `uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` e
> `uv run python -c "import secrets; print(secrets.token_urlsafe(48))"`.

---

## 7. Apps e modelos (Fase 2 a 7)

### `apps/core`
- `TimeStampedModel` (created_at/updated_at).
- `AuditLog` (ator, ação, entidade, antes/depois em JSON, IP, timestamp).
- Mixins de escopo: `EstadoScopeMixin`, `RegionalScopeMixin`, `LocalScopeMixin`.
- `EncryptedCharField` / `EncryptedTextField` (Fernet).
- `hash_cpf(cpf)` (HMAC-SHA256 com pepper).

### `apps/accounts`
- `User` (e-mail como login, `is_active`, `must_change_password`).
- `Perfil` (`ADMIN_ESTADUAL`, `COORDENADOR_REGIONAL`, `DIRETOR_LOCAL`, `MEMBRO`).
- Vínculo do coordenador a `AssociacaoRegional`; do diretor a `Igreja`/`Organizacao`.
- Decorators/mixins de autorização + querysets já filtrados por escopo.

### `apps/institutions`
- `AssociacaoRegional`: nome, macrorregião, coordenador, contatos.
- `Igreja`: CNPJ único (validação de dígitos), razão social, nome fantasia, pastor, contato, endereço, `municipio` FK, `geom PointField(srid=4326)`, `associacao` FK, `igreja_mae` self-FK, `status` (`PENDENTE`, `HOMOLOGADA`, `INATIVA`), homologação (quem/quando).
- `Organizacao`: `tipo` (`HD`, `ERV`, `ER`), igreja FK, data de fundação, líder/conselheiro, contato, dia/horário, status. **Constraint `unique(igreja, tipo)`**.
- Regras: não criar organização em igreja não homologada; não duplicar tipo por igreja; congregação sem CNPJ exige `igreja_mae`.

### `apps/members`
- `Membro`: user (opcional), organizações M2M, nome, `cpf_encrypted` + `cpf_hash` único, nascimento, estado civil, profissão, talentos, contato, endereço, status (`PROVISORIO`, `ATIVO`, `INATIVO`).
- `ResponsavelLegal`: nome, `cpf_hash`/`cpf_encrypted`, parentesco, contato.
- `Consentimento`: membro FK, responsável FK (quando menor), IP, timestamp, `versao_termo`, `finalidade`. **Append-only** (bloquear `save` em update e `delete`, trigger no banco em prod).
- `TermoVersao`: versão, texto, vigência.
- Regra: menor de 18 anos só ativa após consentimento de responsável; CPF único.

### `apps/census`
- `RespostaCenso`: membro FK, escolaridade, profissão, competências técnicas, ministérios de socorro, disponibilidade, versão do formulário, campos sensíveis cifrados.
- `ServicoAgregacao`: funções que retornam contagens já anonimizadas (k-anonimato mínimo 5).
- Endpoints: `/api/censo/indicadores/`, `/api/censo/piramide/`, `/api/censo/vocacional/`.

### `apps/events`
- `Evento`: título, tipo, abrangência (`ESTADUAL`, `REGIONAL`, `LOCAL`), associação/igreja, início/fim, local, `geom`, descrição, banner, capacidade, inscrições abertas.
- `Inscricao`: evento + membro, status, `token` assinado (UUID/`django.core.signing`), check-in, timestamps. Constraint `unique(evento, membro)`.
- Geração de **QR Code** (`qrcode`) e feed **ICS** (`/eventos/<id>.ics`).

### `apps/content`
- `PaginaInstitucional` (slug, conteúdo, SEO), `Noticia`, `Galeria`, `Foto`.
- Editor no admin; imagens convertidas para WebP.

### `apps/geo`
- `Municipio`: nome, código IBGE, `geom MultiPolygonField(srid=4326)`, associação.
- Management command `importar_municipios_to` (GeoJSON IBGE).
- APIs do mapa: pins, clusters padrão do Leaflet, filtros por organização/associação, polígonos por densidade, raio por distância.

### `apps/dashboard`
- Views protegidas por escopo; agregações por associação/município/igreja/faixa etária.
- Cache de indicadores (Django cache; Redis opcional).

---

## 8. RBAC e escopo (Fase 2)

| Papel | Grupo Django | Escopo de queryset | Ações |
|---|---|---|---|
| Administrador Estadual | `admin_estadual` | Todas as associações/igrejas | Homologar, moderar eventos, censo global, auditoria |
| Coordenador Regional | `coord_regional` | Municípios/igrejas da sua associação | Validar registros, propor eventos regionais |
| Diretor/Conselheiro Local | `diretor_local` | Sua igreja/organizações | Ativar organizações, cadastrar membros, notificações |
| Membro | `membro` | Próprio perfil/dependentes | Autocadastro, consentimento, inscrições |

Implementação:
1. Grupos criados em data migration.
2. Permissões nomeadas (`institutions.homologar_igreja`, etc.).
3. `get_queryset()` por escopo em cada ViewSet/ListView.
4. Testes de autorização negativa (tentar acessar escopo alheio → 403/404).

---

## 9. LGPD e segurança (transversal, Fases 4 e 9)

- **Dado sensível:** filiação religiosa; base legal = consentimento específico e destacado (Art. 11, I).
- **Menores (9–17):** status provisório até consentimento de responsável (nome, CPF, vínculo) — atende CT-02.
- **Criptografia em repouso:** campos sensíveis do censo e CPF via Fernet (AES-128-CBC + HMAC; para AES-256 usar `cryptography` com chave de 32 bytes e modo GCM). Guardar chave fora do repositório.
- **CPF:** armazenar cifrado e um `cpf_hash` HMAC para unicidade/busca.
- **Consentimento append-only:** sem update/delete; trigger `BEFORE UPDATE OR DELETE` no PostGIS; registro de IP, timestamp e versão do termo.
- **Revogação/expurgo:** comando `anonimizar_titular` substitui PII por marcadores e preserva agregados; retenção conforme obrigações legais.
- **Painel/API:** apenas agregados; supressão de recortes com menos de 5 registros.
- **OWASP:** CSRF, XSS (escape de templates), SQLi (ORM), upload validado (tipo/tamanho), rate limit em login/autocadastro, CSP (`django-csp`), HSTS, cookies seguros.
- **Senhas:** Argon2id.
- **Auditoria:** log de ações administrativas e acessos a dados sensíveis.
- **TLS 1.3** terminado no Caddy/Nginx.

---

## 10. Frontend e performance

- Tailwind compilado no build (não CDN), HTMX (~14 KB), Alpine adiado.
- Leaflet carregado **somente** na página do mapa (lazy), tiles raster otimizados.
- Gráficos sob demanda após o primeiro paint.
- Imagens em WebP, `loading="lazy"`, dimensões explícitas.
- WhiteNoise com Brotli/Gzip; cache de estáticos com hash.
- Meta: HTML+CSS+JS inicial < 1,5 MB, layout fluido de 360 px a 4K.
- Endpoints de dashboard com cache e índices; meta < 400 ms.

---

## 11. Docker e produção

`Dockerfile` (multi-stage com uv):

```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
RUN uv sync --frozen --no-dev

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 gdal-bin libgeos-c1v5 libproj25 libsqlite3-mod-spatialite \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.prod
RUN python manage.py collectstatic --noinput
EXPOSE 8006
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8006", "--workers", "3", "--timeout", "60"]
```

`docker-compose.prod.yml` (Postgres **externo** na porta 5434):

```yaml
services:
  web:
    build: .
    env_file: .env
    restart: unless-stopped
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - media:/app/media
    expose:
      - "8006"
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request;urllib.request.urlopen('http://localhost:8006/health/')"]
      interval: 30s
      timeout: 5s
      retries: 3

  caddy:
    image: caddy:2
    restart: unless-stopped
    ports: ["80:80", "443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on: [web]

volumes:
  media:
  caddy_data:
  caddy_config:
```

`Caddyfile`:

```caddy
hdto.exemplo.org.br {
    encode zstd gzip
    reverse_proxy web:8006
}
```

Passos de deploy:

```bash
# na VPS
git clone <repo> && cd hdto
cp .env.example .env   # preencher segredos e DB_*
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml run --rm web python manage.py migrate
docker compose -f docker-compose.prod.yml run --rm web python manage.py importar_municipios_to
docker compose -f docker-compose.prod.yml run --rm web python manage.py createsuperuser
docker compose -f docker-compose.prod.yml up -d
```

Checklist de produção:
- [ ] `DEBUG=False`, `SECRET_KEY` e chaves fora do Git.
- [ ] `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` do domínio.
- [ ] Migrations e `collectstatic` no release.
- [ ] Health check `/health/`.
- [ ] Backup diário: `pg_dump -p 5434 -Fc hdto_db > backup_$(date +%F).dump` + retenção.
- [ ] Restore testado.
- [ ] Logs com rotação; Sentry opcional.
- [ ] Monitoramento de uptime e disco (mídia).
- [ ] Postgres com `listen_addresses` e `pg_hba` restritos.

---

## 12. Testes e homologação

- `pytest` + `pytest-django` + `factory_boy`; cobertura mínima 80% nos apps críticos.
- Testes de autorização por papel (positivos e negativos).
- Testes de LGPD: menor sem responsável (CT-02), consentimento imutável, expurgo.
- Testes de regra: CNPJ único, 1 organização por tipo, igreja não homologada.
- Testes de API: performance com `django-debug-toolbar`/`pytest-benchmark`, N+1 com `assertNumQueries`.
- E2E dos cenários do PRD (Playwright ou Django `LiveServerTestCase`):
  - CT-01: ativar ERV e refletir no mapa.
  - CT-02: bloquear menor sem responsável.
  - CT-03: filtrar Palmas + HD.
  - CT-04: dashboard filtrado pela Associação Norte.
- Teste de carga leve (k6/Locust) nas APIs de dashboard/mapa.

---

## 13. Roadmap de execução (estimativa 12–14 semanas, 1 dev)

### Fase 0 — Descoberta e infraestrutura (2–3 dias)
- Validar Postgres 5434 + PostGIS, criar DB/role.
- Definir domínio, TLS e estratégia de backup.
- Levantar associações regionais e dados base.

**DoD:** conexão de teste ao banco e `CREATE EXTENSION postgis` funcionando.

### Fase 1 — Fundação do projeto (1 semana)
- `uv init`, Django, estrutura de apps, settings split, ruff, pytest, pre-commit.
- Dockerfile dev, compose dev, `.env.example`, README.
- CI inicial (ruff + pytest + `makemigrations --check`).

**DoD:** `uv run manage.py runserver`, `uv run pytest` verde, `docker build` ok.

### Fase 2 — Core, usuários e RBAC (1–1,5 semana)
- User por e-mail, perfis, grupos, mixins de escopo, auditoria, admin.
- Telas de login/logout e gestão de usuários.

**DoD:** 4 papéis com escopos comprovados por testes.

### Fase 3 — Cadastros institucionais (1,5 semana)
- Modelos Associação/Igreja/Organização, validações, workflow de homologação.
- CRUD no admin + telas locais; seed e importação.

**DoD:** CT-01 (criação de ERV) e homologação de igreja funcionando.

### Fase 4 — Membros, consentimento e LGPD (2 semanas)
- Membro, responsável legal, consentimento append-only, cifragem e hash de CPF.
- Autocadastro, portal do titular, comando de anonimização/expurgo.
- Trigger de imutabilidade no Postgres.

**DoD:** CT-02 e testes de imutabilidade/expurgo passando.

### Fase 5 — Censo e dashboard (2 semanas)
- Formulário censitário, validações e versionamento.
- Serviços de agregação, endpoints, gráficos e filtros.
- k-anonimato e cache.

**DoD:** CT-04; APIs < 400 ms em base de teste.

### Fase 6 — Geo/GIS e mapa (1,5–2 semanas)
- `Municipio`, importação IBGE, pins, clusters, filtros, raio e popups.
- Índices espaciais e testes de performance.

**DoD:** CT-03; renderização < 1,2 s em 4G simulado.

### Fase 7 — Eventos e inscrições (1,5 semana)
- CRUD de eventos, inscrição, QR, ICS, check-in, rotas.
- Moderação por escopo.

**DoD:** inscrição → QR válido → check-in; feed ICS importável.

### Fase 8 — Portal público e conteúdo (1,5 semana)
- Páginas institucionais (ER/ERV/HD), notícias, galerias, SEO.
- Otimização de imagens e orçamento de carga.

**DoD:** Lighthouse ≥ 90 em performance/SEO; carga inicial < 1,5 MB.

### Fase 9 — Qualidade, segurança e homologação (1–1,5 semana)
- Revisão OWASP Top 10, CSP, rate limiting, uploads.
- E2E CT-01 a CT-04, cobertura, carga leve.
- Revisão de LGPD e roteiro de resposta a incidentes.

**DoD:** checklist de segurança assinado; todos os CTs verdes.

### Fase 10 — Deploy e operação (1 semana)
- Compose prod, Caddy/TLS, migrations, backup, monitoramento.
- Runbook, treinamento e go-live.

**DoD:** ambiente produtivo no ar, backup e restore validados.

---

## 14. Riscos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| PostGIS ausente/porta 5434 fechada | Mapa e raio não funcionam | Validar na Fase 0; plano B com lat/long + Haversine |
| Dados sensíveis expostos | Multa LGPD e dano reputacional | Cifragem, hash de CPF, agregação, auditoria, revisão jurídica |
| Consentimento de menores incompleto | Bloqueio legal do censo | Fluxo obrigatório de responsável + status provisório |
| Baixa conectividade no interior | Má experiência | HTMX, imagens WebP, orçamento de 1,5 MB, cache |
| SQLite dev ≠ PostGIS prod | Bugs só em produção | SpatiaLite no dev + testes de integração com PostGIS no CI |
| Escopo hierárquico vazando | Acesso indevido | Querysets por escopo + testes negativos |
| Postgres externo acessível demais | Risco de segurança | Firewall, SSL, role sem superuser, senha forte |

---

## 15. Checklist de go-live

- [ ] Migrations aplicadas e `migrate --check` limpo.
- [ ] Superusuário e grupos criados.
- [ ] Importação dos 139 municípios concluída.
- [ ] Termo de consentimento versionado e publicado.
- [ ] Domínio com TLS 1.3 e HSTS.
- [ ] Backups automáticos + restore testado.
- [ ] Monitoramento e alertas ativos.
- [ ] Cenários CT-01 a CT-04 aprovados.
- [ ] Política de privacidade e canal do titular publicados.
- [ ] Plano de resposta a incidentes documentado.
