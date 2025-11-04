# Project Alpha Backend (FastAPI + PostgreSQL)

Project Alpha is a modular monolithic FastAPI backend for preventing internet misuse by children and students. It features a central Filter Engine that evaluates device browsing events into Categories A (unrestricted), B (partially restricted; alert), and C (blocked), with robust logging, alerts, and reporting.

## Tech Stack
- FastAPI, Pydantic
- SQLAlchemy (async) + Alembic
- PostgreSQL
- JWT auth (python-jose) + bcrypt
- Docker + docker-compose (Postgres, pgAdmin)
- Pytest for tests

## Quick Start

### 1) Clone and configure
```bash
cp config/.env.example .env
```
Edit `.env` as needed.

### 2) Docker build & run
```bash
docker compose up --build -d
```
This starts the app on port 8000, Postgres on 5432, and pgAdmin on 5050.

### 3) Run migrations and seed
```bash
make migrate
make seed
```

### 4) Docs
- Swagger UI: http://localhost:8000/docs

## Local Development
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Makefile / Scripts
- `make start` - run app locally with reload
- `make migrate` - run Alembic migrations
- `make revision` - create a new Alembic migration
- `make seed` - seed admin and sample blocked sites
- `make test` - run tests

## Structure
```
app/
  core/            # config, database, security, responses
  models/          # SQLAlchemy models
  schemas/         # Pydantic schemas
  services/        # filter_engine, email, analytics, logging
  routes/          # auth, users, devices, browsing, blocked_sites, activity, reports
  utils/           # helpers
  main.py          # FastAPI app and router mounting
alembic/           # migrations
```

## Notes on Scaling to Microservices
- Filter Engine, Email Service, and Analytics can be extracted as separate services with minimal changes. They currently communicate via well-defined service interfaces in `app/services/` and rely on database models and logging service abstractions.

## Testing
```bash
pytest -q
```

## Security
- Keep secrets only in environment variables
- Use strong JWT secret and rotate credentials in production

## License
MIT

