# HDTO — Plataforma dos Homens Batistas do Tocantins

Aplicação Django para a UMHB-TO/CBT: portal institucional, cadastro hierárquico de igrejas e organizações (SMHB, GAM, ER), censo com LGPD, painel analítico, mapa das congregações e eventos com QR Code.

## Stack

- Python 3.12 gerenciado por **uv**
- Django 5.2 LTS + Django REST Framework
- **SQLite + SpatiaLite** em desenvolvimento
- **PostgreSQL + PostGIS** em produção (porta 5434)
- Docker para o app; Caddy para TLS
- Templates + Leaflet + Chart.js (sem SPA)

## Estrutura

```
apps/
  accounts/      usuários e RBAC
  institutions/  associação, igreja, organização
  members/       membros, responsáveis, consentimento LGPD
  census/        respostas e agregações do censo
  dashboard/     API de indicadores
  geo/           municípios, mapa e importação IBGE
  events/        eventos, inscrições, QR/ICS/check-in
  content/       páginas, notícias e galerias
  core/          base, criptografia, validadores, middleware
config/settings/ base, dev e prod
docs/            PRD, plano e runbook
```

## Desenvolvimento

Pré-requisitos: Docker e, opcionalmente, `uv`.

```bash
cp .env.example .env
# gere a chave de criptografia
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# preencha FIELD_ENCRYPTION_KEY no .env

docker compose up --build
```

Acesse http://localhost:8000. O comando do compose roda `migrate` e `runserver`.

> O host precisa das bibliotecas GDAL/GEOS/PROJ/SpatiaLite para rodar `uv run` diretamente. A imagem `Dockerfile.dev` já as inclui — por isso o fluxo padrão é via Docker.

### Testes e lint

```bash
docker compose run --rm web sh -c "uv sync --frozen && uv run ruff check . && uv run pytest"
```

### Comandos úteis

```bash
# migrações
docker compose run --rm web uv run python manage.py makemigrations
docker compose run --rm web uv run python manage.py migrate

# superusuário
docker compose run --rm web uv run python manage.py createsuperuser

# importar os 139 municípios do TO (GeoJSON do IBGE)
docker compose run --rm web uv run python manage.py importar_municipios_to --arquivo /caminho/municipios.geojson
```

## Endpoints principais

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Portal público |
| GET | `/institucional/<slug>/` | Página institucional |
| GET | `/noticias/` | Notícias publicadas |
| GET | `/eventos/` | Próximos eventos |
| GET | `/eventos/<id>/ical/` | Feed iCalendar |
| POST | `/eventos/checkin/<token>/` | Check-in por QR |
| GET | `/mapa/` | Mapa com clusters |
| GET | `/api/mapa/pontos/` | Pins com filtros e raio |
| GET | `/api/mapa/municipios/` | GeoJSON municipal |
| GET | `/api/censo/indicadores/` | Painel (admin/coord/diretor) |
| GET | `/cadastros/igrejas/nova/` | Formulário de igreja |
| GET | `/cadastros/organizacoes/nova/` | Formulário de organização |
| GET | `/cadastro/membro/` | Autocadastro censitário |
| GET | `/eventos/<id>/inscrever/` | Formulário de inscrição |
| GET | `/contas/painel/` | Painel analítico com filtros |
| GET | `/conta/perfil/` | Portal do titular |
| POST | `/conta/revogar-consentimento/` | Revogação + anonimização |
| GET | `/health/` | Healthcheck |

## Produção

Consulte `docs/RUNBOOK.md`. Resumo:

```bash
cp .env.example .env   # preencha segredos e DB_*
./scripts/deploy.sh
```

Variáveis essenciais: `SECRET_KEY`, `FIELD_ENCRYPTION_KEY`, `CPF_HASH_PEPPER`, `DB_*` (porta **5434**).

## Interface

O frontend usa princípios de Material UX (elevação, estados, foco visível, áreas de toque de 44px, snackbars) combinados com glassmorphism (painéis translúcidos, blur e gradientes suaves). O CSS e os scripts ficam em `static/` e não dependem de build de Tailwind.

## LGPD

- CPF cifrado com Fernet e hash HMAC para unicidade.
- Consentimento append-only com trigger no PostgreSQL.
- Menores exigem responsável legal (CT-02).
- Revogação anonimiza PII e inativa a conta.
- Painel expõe apenas agregados com supressão de grupos menores que `CENSO_K_ANONIMATO`.
- Cabeçalhos de segurança e CSP configurados.
