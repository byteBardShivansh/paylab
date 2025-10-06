# Payments Microservice (FastAPI)

Enterprise-grade Payments Microservice featuring FastAPI, SQLAlchemy, structured JSON logging, and environment-based configuration.

## Features
- Endpoints: `GET /health`, `GET /ready`, `POST /payments`
- API key security via `X-API-KEY`
- SQLAlchemy 2.0 with repository pattern
- PostgreSQL support; tests run on SQLite in-memory
- JSON structured logging
- 12-factor config via environment variables and `.env`
- Docker + docker-compose for local dev
- Pytest with coverage and edge cases

## Requirements
- Python 3.11+
- Optional: Docker and docker-compose

## Quickstart (local)
1. Create and activate a virtual environment, then install:
   ```bash
   python -m venv .venv
   . .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
   pip install -e .[dev]
   ```

2. Copy `.env.example` to `.env` and adjust values if needed:
   ```bash
   cp .env.example .env
   ```

3. Run the service:
   ```bash
   make run
   # Or directly:
   uvicorn app.main:app --reload
   ```

4. Test endpoints:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/ready
   curl -X POST http://localhost:8000/payments \
        -H 'Content-Type: application/json' \
        -H 'X-API-KEY: dev-secret' \
        -d '{"order_id":"ORD123","amount":10.5,"currency":"USD"}'
   ```

## Docker
Run Postgres and API together:
```bash
docker-compose up --build
```

## Testing
Run unit tests with coverage:
```bash
pytest
```

## Linting
```bash
make lint
# Auto-fix
make fmt
```

## Configuration
Set environment variables or use a `.env` file (see `.env.example`). Important settings:
- `API_KEY`: Required header value for `X-API-KEY`
- `DATABASE_URL`: SQLAlchemy URL. For Postgres: `postgresql+psycopg://user:pass@host:5432/db`
- `LOG_LEVEL`: INFO/DEBUG/WARN/ERROR

## Notes
- In production, use migrations (e.g., Alembic). This sample creates tables automatically on startup.
- Monetary amounts are stored as Decimal(12,2). API responses return float for simplicity; if required, adapt to string-decimal.
