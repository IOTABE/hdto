# HDTO — Plataforma dos Homens Batistas do Tocantins

Aplicação Django para a UMHB-TO/CBT: portal institucional, cadastro hierárquico de igrejas e organizações (HD, ERV, ER), censo com LGPD, painel analítico, mapa das congregações e eventos com QR Code.

## Stack

- Python 3.12 gerenciado por **uv**
- Django 5.2 LTS + Django REST Framework
- **SQLite + SpatiaLite** em desenvolvimento
- **PostgreSQL + PostGIS** em produção (porta 5434)
- Docker para o app; Nginx no host para proxy reverso/TLS
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
docs/            PRD, plano, runbook e manual de personas
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

Acesse http://localhost:8006. O comando do compose roda `migrate` e `runserver`.

> O host precisa das bibliotecas GDAL/GEOS/PROJ/SpatiaLite para rodar `uv run` diretamente. A imagem `Dockerfile.dev` já as inclui — por isso o fluxo padrão é via Docker.

### Erro `Could not find the GDAL library`

Isso acontece ao rodar `uv run manage.py` no host sem as bibliotecas nativas. Escolha uma opção:

**Opção A — Docker (recomendada, sem alterar o sistema):**
```bash
cp -n .env.example .env
# gere e preencha FIELD_ENCRYPTION_KEY no .env
docker compose up --build
```

**Opção B — instalar no host (Arch/Manjaro/BigLinux):**
```bash
sudo pacman -S --needed gdal geos proj libspatialite
gdal-config --version
```
Se ainda não localizar, preencha no `.env`:
```env
GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so
SPATIALITE_LIBRARY_PATH=/usr/lib/mod_spatialite.so
```

### Testes e lint

```bash
docker compose run --rm web sh -c "uv sync --frozen && uv run ruff check . && uv run pytest"
```

### Captcha

O formulário de cadastro usa o **django-simple-captcha**: a imagem é gerada localmente pelo próprio Django/Pillow, sem depender de servidores externos nem de chaves de API. Não é necessária nenhuma configuração adicional.

A imagem é servida por `/captcha/image/<chave>/` e expira conforme `CAPTCHA_TIMEOUT` (padrão: 5 minutos). Em testes automatizados, `CAPTCHA_TEST_MODE` aceita a resposta `PASSED`.

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
| GET | `/institucional/historia/` | História institucional |
| GET | `/institucional/diretoria/` | Diretoria por biênio |
| GET/POST | `/institucional/contato/` | Contato por e-mail, WhatsApp ou registro local |
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

Variáveis essenciais: `SECRET_KEY`, `FIELD_ENCRYPTION_KEY`, `CPF_HASH_PEPPER`, `DB_*` (porta **5434**). O captcha usa `django-simple-captcha` e não requer variáveis de ambiente.

## Interface

O frontend usa princípios de Material UX (elevação, estados, foco visível, áreas de toque de 44px, snackbars) combinados com glassmorphism (painéis translúcidos, blur e gradientes suaves). O CSS e os scripts ficam em `static/` e não dependem de build de Tailwind.

## LGPD

- CPF cifrado com Fernet e hash HMAC para unicidade.
- Consentimento append-only com trigger no PostgreSQL.
- Menores exigem responsável legal (CT-02).
- Revogação anonimiza PII e inativa a conta.
- Painel expõe apenas agregados com supressão de grupos menores que `CENSO_K_ANONIMATO`.
- Cabeçalhos de segurança e CSP configurados.
