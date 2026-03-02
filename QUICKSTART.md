# Quick Start Guide

## 🚀 Get Up and Running in 5 Minutes

### Prerequisites
- Docker & Docker Compose installed
  OR
- Python 3.12+ and Node.js 18+ (for running without Docker)

### Option 1: Docker (Recommended)

```bash
# Clone and navigate
git clone <repo> permit-intel-cleveland
cd permit-intel-cleveland

# Copy environment config
cp .env.example .env

# Start services
docker-compose up --build

# In another terminal, initialize database
docker-compose exec backend python -c \
  "from app.models.database import engine, Base; Base.metadata.create_all(bind=engine)"

# Access services:
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Frontend: http://localhost:3000
```

### Option 2: Local Development (Python + Node)

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

---

## 📊 Test the Pipeline Immediately

Once running, test the full pipeline:

```bash
cd backend
python3 test_pipeline.py
```

This will:
1. ✓ Ingest 3 sample permits from SF, NYC
2. ✓ Score each permit (generates WIN score)
3. ✓ List permits in database
4. ✓ Manage sources
5. ✓ Generate summary report

**Expected output:**
```
✓ Ingested SF-2024-001: 100 Market St
✓ Scored SF-2024-001: WIN=0.62
Total permits in database: 3
✓ Pipeline test completed successfully!
```

---

## 🔌 API Endpoints Quick Reference

### Permits
- `POST /permits/ingest` – Ingest a single permit
- `GET /permits/` – List all permits  
- `GET /permits/{id}` – Get permit details
- `POST /permits/{id}/score` – Compute WIN score
- **`POST /permits/{id}/analyze`** – Full pipeline analysis (returns everything!)
- `GET /permits/wins` – Ranked WINS TABLE

### Sources
- `GET /sources/` – List registered data sources
- `POST /sources/add` – Register a new source

### Health
- `GET /` – API info
- `GET /health` – Health check

---

## 🧪 Example API Call (Full Pipeline)

```bash
# 1. Ingest a permit
curl -X POST http://localhost:8000/permits/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "permit_id": "SF-2024-TEST",
    "city": "San Francisco",
    "address": "123 Main St",
    "valuation": 2500000,
    "status": "Issued",
    "permit_type": "Commercial",
    "description": "TI for tech office with electrical work",
    "source_url": "https://example.com"
  }'

# 2. Get the permit ID from response, then analyze it
# Replace {id} with the returned ID
curl http://localhost:8000/permits/{id}/analyze | jq .

# This returns:
# {
#   "permit": { ... },
#   "score": { "win_score": 0.65, ... },
#   "opportunity_synthesis": { "leverage_angles": [...] },
#   "multi_vertical_packages": [ {...}, {...} ],
#   "cross_sell_opportunities": [...],
#   "asset_packs": [ {...}, {...} ],
#   "buyer_discovery_plans": [...]
# }
```

---

## 📚 Full Documentation Structure

- **Backend Code**: `backend/app/` – FastAPI services, models, API routes
- **Frontend Code**: `frontend/src/` – React dashboard
- **Database**:  
  - Schema: `db/init.sql`
  - Migrations: `db/migrations/` (Alembic)
- **Tests**: `backend/tests/` – pytest test suite
- **Sample Data**: `backend/test_pipeline.py` – automated integration test

---

## 🎯 Common Tasks

### Run Tests
```bash
cd backend
pytest -v
```

### Run Full Pipeline Test Script
```bash
cd backend
python3 test_pipeline.py
```

### Add a New City Source
```bash
curl -X POST http://localhost:8000/sources/add \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Chicago",
    "urls": {
      "type": "Socrata",
      "url": "https://data.cityofchicago.org/Buildings/Building-Permits/ydr8-5enu"
    }
  }'
```

### View API Documentation
Open browser to: **http://localhost:8000/docs**

---

## 📝 Environment Variables

See `.env.example`:
```
DATABASE_URL=postgresql://user:pass@db:5432/permitdb
REDIS_URL=redis://redis:6379/0
```

For SQLite (default local testing):
```
DATABASE_URL=sqlite:///./test.db
```

---

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| `Connection refused` | Check Docker is running: `docker ps` |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` in `backend/` |
| `Port 8000 already in use` | Change `docker-compose.yml` or kill process: `lsof -i :8000` |
| `Table doesn't exist` | Run database init: `python -c "from app.models.database import engine, Base; Base.metadata.create_all(bind=engine)"` |

---

## 🎓 Next Steps

1. **Ingest real data**: Fetch permits from Socrata/ArcGIS sources
2. **Enhance scoring**: Refine WIN score logic in `services/scoring_service.py`
3. **Expand verticals**: Add more business categories to `curation_service.py`
4. **Implement auto-OSINT**: Build out `osint_service.py` with real enrichment
5. **Build UI**: Enhance `frontend/` with permit visualization
6. **Deploy**: Use Docker to deploy to cloud (Render, Heroku, AWS)

---

**Questions?** Check the full [README.md](./README.md) and API docs at `http://localhost:8000/docs`
