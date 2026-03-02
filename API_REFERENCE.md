# API Quick Reference

## Base URL
- **Local**: `http://localhost:8000`
- **Production**: `https://yourdomain.com`

## 📋 Core Endpoints

### Permits

#### List Permits
```bash
GET /permits/?skip=0&limit=100
```
**Response**: Array of permits

#### Ingest Permit
```bash
POST /permits/ingest
Content-Type: application/json

{
  "permit_id": "SF-2024-001",
  "city": "San Francisco",
  "address": "100 Market St",
  "lat": 37.7942,
  "lon": -122.3969,
  "permit_type": "Commercial",
  "description": "Office TI with electrical work",
  "valuation": 2500000,
  "status": "Issued",
  "filed_date": "2024-01-15",
  "issued_date": "2024-02-01",
  "applicant": "John Developer LLC",
  "contractor": "ABC General Contractors",
  "owner": "Building Owner Corp",
  "source_url": "https://data.sfgov.org/..."
}
```
**Response**: Permit object with ID

#### Get Permit Details
```bash
GET /permits/{id}
```
**Response**: Single permit object

#### Compute WIN Score
```bash
POST /permits/{id}/score
```
**Response**: Score object with WIN score + components

#### **FULL PIPELINE ANALYSIS** ⭐
```bash
POST /permits/{id}/analyze
```
**Response**: Complete intelligence package
```json
{
  "permit": {...},
  "score": {...},
  "opportunity_synthesis": {...},
  "multi_vertical_packages": [...],
  "cross_sell_opportunities": [...],
  "asset_packs": [...],
  "buyer_discovery_plans": [...]
}
```

#### Ranked WINS Table
```bash
GET /permits/wins?skip=0&limit=100
```
**Response**: 
```json
{
  "total": 50,
  "records": [
    {
      "id": 1,
      "permit_id": "SF-2024-001",
      "city": "San Francisco",
      "address": "100 Market St",
      "valuation": 2500000,
      "win_score": 0.72,
      "status": "Issued",
      "permit_type": "Commercial"
    }
  ]
}
```

---

### Sources

#### List Sources
```bash
GET /sources/
```
**Response**: Array of registered sources

#### Register New Source
```bash
POST /sources/add
Content-Type: application/json

{
  "city": "San Francisco",
  "urls": {
    "type": "Socrata",
    "url": "https://data.sfgov.org/resource/i98e-djp9"
  }
}
```
**Response**: Source object

---

### System

#### Health Check
```bash
GET /
```
**Response**:
```json
{
  "message": "Permit Arbitrage Intelligence Hub API",
  "version": "1.0.0",
  "docs": "/docs",
  "description": "Ingest permits → Score → Synthesize → Curate → Monetize"
}
```

#### API Status
```bash
GET /health
```
**Response**:
```json
{
  "status": "healthy",
  "service": "permit-intelligence-hub"
}
```

#### Interactive Docs
```
GET /docs              → Swagger UI (try endpoints here)
GET /redoc             → ReDoc documentation
GET /openapi.json      → OpenAPI specification
```

---

## 🔄 Typical Workflow

### 1. Ingest a Permit
```bash
PERMIT_ID=$(curl -s -X POST http://localhost:8000/permits/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "permit_id": "SF-2024-001",
    "city": "San Francisco",
    "address": "100 Market St",
    "valuation": 2500000,
    "permit_type": "Commercial",
    "description": "Office TI",
    "source_url": "https://example.com"
  }' | jq -r '.id')

echo "Ingested permit ID: $PERMIT_ID"
```

### 2. Analyze Permit (Full Pipeline)
```bash
curl -s -X POST http://localhost:8000/permits/$PERMIT_ID/analyze \
  -H "Content-Type: application/json" | jq .
```

### 3. Get WINS Table (Top Opportunities)
```bash
curl -s http://localhost:8000/permits/wins | jq '.records[] | {permit_id, city, valuation, win_score}'
```

### 4. Access Interactive Docs
```
http://localhost:8000/docs
```
→ Try all endpoints in browser

---

## 📊 WIN Score Components

```
win_score = (0.5 × value_score) + (0.2 × delay_score) + (0.2 × commercial_score) + (0.1 × competition_score)

Where:
- value_score = valuation ÷ $1,000,000
- delay_score = 0–1 (estimated likelihood of delays)
- commercial_score = 1.0 if commercial, else 0.5
- competition_score = 0–1 (random baseline, ready for ML)
```

**Interpretation:**
- `> 0.7` → High-priority opportunity, trigger enrichment
- `0.5-0.7` → Good opportunity
- `< 0.3` → Lower priority

---

## 🎯 Leverage Angles (in Synthesis)

1. **Delay Arbitrage** (delay_score > 0.4)
   - Project delays → expedite services needed
   - Bridge loans, fast permits, premium subcontractors

2. **Vendor/Scope Arbitrage** (electrical/HVAC/sprinkler keywords)
   - Specialized work → premium subcontracting rates
   - GC & specialized trades bidding

3. **Financing Gap** (valuation > $500k)
   - Large projects → capital needs
   - Bridge financing, supplier financing, hard money

---

## 📦 Verticals (Multi-Vertical Curation)

Each permit curated into packages for:

1. **mortgage_broker** – Financing gaps, owner contacts
2. **general_contractor** – Scope, subcontractors, bidding
3. **electrician** – Electrical work, timeline
4. **hvac_specialist** – HVAC opportunities
5. **supplier** – Material needs, timeline

Each package includes:
- Key fields (tailored per vertical)
- Leverage angle (which of 3)
- Content (address, valuation, permit type)
- Cross-sell opportunities

---

## 💰 Deal Terms (Monetization Options)

For each vertical package:

1. **Fixed Fee** – e.g., $10,000 one-time
2. **Hybrid** – e.g., $2,500 + 10% success fee
3. **Revenue Share** – e.g., 3% of origination fee
4. **Referral Fee** – e.g., 10% of contract value (for cross-sell)

---

## 🔐 Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | OK | Request succeeded |
| 400 | Bad Request | Check JSON format |
| 404 | Not Found | Permit ID doesn't exist |
| 500 | Server Error | Check backend logs |

---

## 🛠️ Development Tips

### Run Tests
```bash
cd backend
pytest -v
```

### Run Test Pipeline
```bash
cd backend
python3 test_pipeline.py
```

### Start API (Development)
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### View Live API Docs
```
http://localhost:8000/docs
```

### Docker Stack
```bash
docker-compose up --build
# All services start: PostgreSQL, Redis, Backend, Frontend
```

---

## 📖 Full Documentation

- **README.md** – Complete setup & usage
- **QUICKSTART.md** – 5-minute startup
- **SYSTEM_DESIGN.md** – Architecture reference
- **SPEC_IMPLEMENTATION.md** – Feature mapping
- **BUILD_COMPLETE.md** – Project summary

---

## 🚀 Example: Complete Workflow (Python)

```python
import requests

BASE = "http://localhost:8000"

# 1. Ingest permit
permit_data = {
    "permit_id": "SF-2024-DEMO",
    "city": "San Francisco",
    "address": "250 Valencia St",
    "valuation": 3000000,
    "permit_type": "Commercial",
    "description": "Restaurant with electrical & HVAC",
    "source_url": "https://example.com"
}
r = requests.post(f"{BASE}/permits/ingest", json=permit_data)
permit_id = r.json()["id"]
print(f"✓ Ingested permit {permit_id}")

# 2. Full analysis
r = requests.post(f"{BASE}/permits/{permit_id}/analyze")
analysis = r.json()

# 3. Extract key insights
print(f"WIN Score: {analysis['score']['win_score']}")
print(f"Leverage Angles: {len(analysis['opportunity_synthesis']['leverage_angles'])}")
print(f"Verticals: {len(analysis['multi_vertical_packages'])}")
print(f"Cross-sell Opportunities: {len(analysis['cross_sell_opportunities'])}")

# 4. Access assets for mortgage_broker
mb_package = next(
    p for p in analysis['asset_packs'] 
    if p['vertical'] == 'mortgage_broker'
)
print(f"\nMortgage Broker Pitch:\n{mb_package['assets']['email_pitch']['body'][:200]}...")
```

---

**Ready to monetize permit intelligence?** 🎯

Start with `/docs` to explore all endpoints interactively!
