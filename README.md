# Permit Arbitrage Intelligence Hub

This repository contains a proof-of-concept full-stack web application that implements a pipeline for ingesting, scoring, and curating building permit data from public sources.

## Overview

The platform is built for a solo user and includes:

- **Backend**: FastAPI with SQLAlchemy and PostgreSQL (or SQLite for local testing)
- **Frontend**: React application with a simple dashboard
- **Database**: PostgreSQL (schema defined and migrations via Alembic)
- **Background tasks**: Celery with Redis (placeholder tasks included)

The system is designed to ingest permit data, compute a WIN score, perform auto-OSINT, and generate vertical-specific intelligence packages. The current codebase provides a skeleton with stubbed services and can be extended following the provided structure.

## Repository Structure

```
/backend
  app/
    main.py
    api/
    models/
    services/
    tasks/
  requirements.txt
  Dockerfile
/frontend
  src/
  package.json
  Dockerfile
/db
  init.sql
  migrations/
    alembic.ini
    env.py
    versions/
docker-compose.yml
.env.example
README.md
```

## Getting Started

### Prerequisites

- Docker & Docker Compose
- (Optional) Python 3.12+ and Node.js 18+ for running without Docker

### Local Setup using Docker

1. Clone the repository and change directory:
   ```bash
   git clone <repo-url> permit-intel-cleveland
   cd permit-intel-cleveland
   ```

2. Copy example environment file:
   ```bash
   cp .env.example .env
   ```

3. Start services:
   ```bash
   docker-compose up --build
   ```

   This will launch PostgreSQL on port 5432, Redis on 6379, the backend API on 8000, and the frontend on 3000.

4. Initialize the database (alternatively run migrations with Alembic):
   ```bash
   docker-compose exec backend python -c "from app.models.database import engine, Base; Base.metadata.create_all(bind=engine)"
   ```

### Running Without Docker

### Tests

From the repository root, you can run backend tests with:

```bash
cd backend
pytest
```

The tests use the in-memory SQLite database configured by default.


1. Create and activate a Python virtual environment.
2. Install backend requirements:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Install frontend dependencies:
   ```bash
   cd frontend && npm install
   ```
4. Configure environment variables (e.g., `DATABASE_URL`, `REDIS_URL`).
5. Start backend:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
6. Start frontend:
   ```bash
   cd frontend && npm start
   ```

## Source Discovery and Managing Cities

When adding a new city, manually search for the municipality's open data portal (often Socrata or ArcGIS).  The app does not yet automate the discovery; simply use the `POST /sources/add` endpoint with a JSON payload of the form:

```json
{
  "city": "San Francisco",
  "urls": {"socrata": "https://data.sfgov.org/resource/i98e-djp9.json"}
}
```

Future enhancements should implement a crawler that compiles a SOURCE PACK as described in the specification. For now, the payload serves as a plugin stub for ingestion.

## Using the API

FastAPI automatically generates documentation at `http://localhost:8000/docs`.

Basic endpoints:

- `GET /permits/` – list permits
- `POST /permits/ingest` – ingest a permit record (JSON payload)
- `POST /permits/{permit_id}/score` – compute and store score for a permit
- `GET /sources/` – list data sources

Example ingest payload:

```json
{
  "permit_id": "123",
  "city": "San Francisco",
  "address": "100 Market St",
  "valuation": 2000000,
  "status": "Filed",
  "source_url": "https://data.sfgov.org/..."
}
```

## Running the Pipeline (Test Data)

1. Use the API to ingest one or more sample permits (e.g., from San Francisco dataset).
2. Trigger scoring for a permit.
3. View results via the API or in the React dashboard.

The pipeline components such as auto-OSINT enrichment, opportunity synthesis, and asset generation are implemented as stubbed services. They can be filled out later by following comments and function names.

## Testing

A minimal test script can be added to automate ingest, scoring, and package generation. For now, manual API calls or `curl` are sufficient.

## Development Notes

- **Database**: The SQLAlchemy models in `backend/app/models/models.py` mirror the schema in `db/init.sql`.
- **Migrations**: Alembic is configured under `db/migrations/`. Run `alembic revision --autogenerate -m "message"` from the repo root to add migrations.
- **Background Jobs**: Celery tasks are defined in `backend/app/tasks/tasks.py` and use Redis broker. Start a worker with `celery -A backend.app.tasks.celery_app.celery worker --loglevel=info`.
- **Frontend**: The React dashboard is minimal; extend by adding more pages and API interactions.

## Next Steps

- Implement the full ingest normalization and source management logic
- Flesh out scoring, auto-OSINT, curation, and asset factory services
- Add UI components for pipeline control and opportunity views
- Expand database schema and add constraints
- Add authentication (JWT) if desired
- Write unit tests for services and API endpoints

---

This scaffold provides a runnable starting point for the Permit Arbitrage Intelligence Hub. Build out the pipeline components to meet the detailed specification and enjoy!
