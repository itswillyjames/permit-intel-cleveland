# Permit Arbitrage Intelligence Hub

This repository has been refactored to a **single FastAPI service** that serves a React frontend. It is optimized for deployment on Render with a deterministic build and minimal dependencies.

## Structure

```
backend/
  app/
    main.py
  requirements.txt

frontend/
  package.json
  package-lock.json

README.md
```

All other files and documentation have been removed to keep the repository clean.

## Development

### Frontend

1. `cd frontend`
2. `npm install` (lock file is committed; do not use `npm ci` in production)
3. `npm run build` produces a `build/` directory (not tracked by git).

### Backend

1. `cd backend`
2. `pip install -r requirements.txt` (contains only `fastapi` and `uvicorn[standard]`)
3. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

The backend serves static files from `app/static` and exposes a health endpoint at `/api/health`.

## Deployment (Render)

Set the service's **Root Directory** to the repo root (leave blank).

**Build Command**:
```bash
cd frontend && npm install && npm run build && \
  cd .. && rm -rf backend/app/static && mkdir -p backend/app/static && \
  cp -r frontend/build/* backend/app/static/ && \
  cd backend && pip install -r requirements.txt
```

**Start Command**:
```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Notes

- The React build directory is generated during deployment and is not committed.
- Only one Render Web Service is required; no database, Redis, or other services are used.
- The backend dependencies are limited to FastAPI and Uvicorn for a deterministic, lightweight container.

This configuration provides a stable, production‑safe deployment with minimal moving parts.
