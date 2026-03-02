# Architecture & Design Document

## System Overview

The **Permit Arbitrage Intelligence Hub** is a modular, service-oriented full-stack application that transforms free permit data into monetizable commercial real estate intelligence.

### High-Level Flow

```
SOURCE DATA (Socrata, ArcGIS, public records)
     ↓
[INGEST] - Normalize & store permits in database
     ↓
[SCORE] - Compute WIN score (value + delay + commercial + competition)
     ↓
[SYNTHESIZE] - Generate 3 leverage angles with proof points
     ↓
[CURATE] - Create vertical-specific intelligence packages
     ↓
[IDENTIFY BUYERS] - Discover and qualify potential buyers
     ↓
[GENERATE ASSETS] - Create pitches, NDAs, one-pagers, call scripts
     ↓
[MONETIZE] - Package for sale (fixed fee, hybrid, rev-share, referral)
```

---

## Service Architecture

### Core Services (`backend/app/services/`)

#### 1. **ingest_service.py**
_Normalize and ingest permit data from various sources._

```python
def ingest(raw_data: dict, db: Session) -> models.Permit
```

- Accepts raw JSON from Socrata, ArcGIS, or custom sources
- Normalizes to standard schema:  
  `permit_id, city, address, lat/lon, permit_type, description, valuation, status, filed_date, issued_date, applicant, contractor, owner, source_url`
- Stores in PostgreSQL (or SQLite for testing)
- **Next Enhancement**: Auto-normalize different source formats (Socrata → ArcGIS schema mapping)

---

#### 2. **scoring_service.py**
_Compute WIN score to identify high-opportunity permits._

```python
def compute_score(permit: models.Permit) -> models.Score
```

**WIN Score Components (0–1 scale):**
- `value_score` (0–1): Valuation ÷ $1M cap
- `delay_score` (0–1): Estimated likelihood of delays
- `commercial_score` (0–1): Commercial vs. residential probability
- `competition_score` (0–1): Market competition level
- **Composite**: `win_score = 0.5×value + 0.2×delay + 0.2×commercial + 0.1×competition`

**Thresholds:**
- `> 0.7` → Trigger auto-OSINT enrichment
- `> 0.5` → Valuable opportunity
- `< 0.3` → Lower priority

---

#### 3. **synthesis_service.py**
_Generate leverage angles and proof points for opportunities._

```python
def synthesize_opportunity(permit, score) -> dict
```

**3 Leverage Angles:**
1. **Delay Arbitrage**: Stalled permits need expediting (bridge loans, fast subcontractors, permit expediting)
2. **Vendor/Scope Arbitrage**: Specialized work requirements (electrical, HVAC, sprinklers) → premium subcontracting fees
3. **Financing Gap**: Large valuation + delays = capital needs (bridge financing, supplier financing, hard money)

**Proof Points**: Include permit data + industry benchmarks with source URLs.

---

#### 4. **curation_service.py**
_Create multi-vertical intelligence packages._

```python
def curate_permit(permit, enrichment_data) -> list[dict]
```

**Supported Verticals:**
- `mortgage_broker` – Financing gaps, owner contacts, property valuation
- `general_contractor` – Scope of work, subcontractor leads, bidding intelligence
- `electrician` – Electrical work, timeline, GC contact
- `hvac_specialist` – HVAC opportunities, timing, GC/PI contact
- `supplier` – Material lead size, timeline, procurement intelligence

**Each Package Contains:**
- Address, city, description, valuation, permit type
- Key fields (tailored per vertical)
- Leverage angle (which of 3 applies to this vertical)
- Cross-sell opportunities (other verticals interested in same project)

**Result**: 5+ curated packages from single permit, each optimized for different buyer.

---

#### 5. **buyer_discovery_service.py**
_Identify and qualify potential buyers._

```python
def generate_buyer_discovery_plan(permit, vertical) -> dict
```

**For Each Vertical + City, Provides:**
- **Why they pay**: Business case (e.g., "Fast lead on electrical work = win bid at premium rates")
- **OSINT Queries**: LinkedIn dorks, Google searches, legal OSINT patterns
- **Free Directories**: Licensing boards, chambers of commerce, industry chapters
- **Qualification Questions**: Ask during discovery to assess fit
- **Next Steps**: Templated action plan

**Example (Electrician in SF):**
```
Query: site:linkedin.com "San Francisco" "licensed electrician" commercial
Directory: SF Electricians Licensing Board
Question: "Are you licensed for commercial work?"
```

---

#### 6. **asset_service.py**
_Generate sales & outreach collateral._

```python
def generate_assets(permit, package, vertical) -> dict
```

**For Each Vertical Package:**
1. **Email Pitch Template** – 150-word value prop + CTA
2. **LinkedIn Message** – Casual intro + benefit statement
3. **One-Pager Brief** – PDF-ready executive summary
4. **Call Script** – Opening → value prop → discovery → pitch → close
5. **Objection Handling** – 3-4 common pushbacks + responses
6. **NDA Template** – Mutual confidentiality agreement (customizable)
7. **Deal Terms** – 3+1 monetization options with pricing

---

#### 7. **osint_service.py**
_Auto-enrichment via free public data (future enhancement)._

**Planned integrations:**
- County assessor data (property values, ownership history)
- Lien & judgment records (financial health signals)
- News mentions (press coverage = market momentum)
- Business registration databases (company credibility)
- Social media profiles (owner/GC reputation)
- Past permits (project history)

**Currently**: Stub. To implement, call APIs with `requests`, respect `robots.txt`, cache results, cite sources.

---

### API Endpoints (`backend/app/api/`)

#### **permits.py**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/permits/` | GET | List all permits (paginated) |
| `/permits/ingest` | POST | Ingest single permit JSON |
| `/permits/{id}` | GET | Get permit details |
| `/permits/{id}/score` | POST | Compute WIN score |
| `/permits/{id}/analyze` | POST | **Full pipeline** (score → synthesize → curate → discover → assets) |
| `/permits/wins` | GET | Ranked WINS TABLE sorted by WIN score |

**`/permits/{id}/analyze` Response Structure:**
```json
{
  "permit": { /* full permit data */ },
  "score": { "win_score": 0.65, ... },
  "opportunity_synthesis": {
    "leverage_angles": [
      { "angle": "delay_arbitrage", "opportunities": [...] },
      { "angle": "vendor_arbitrage", "opportunities": [...] }
    ]
  },
  "multi_vertical_packages": [
    { "vertical": "mortgage_broker", "content": {...} },
    { "vertical": "general_contractor", "content": {...} }
  ],
  "cross_sell_opportunities": [
    { "from": "GC", "to": "Electrician", "referral_fee": "10% of contract" }
  ],
  "asset_packs": [
    { "vertical": "mortgage_broker", "assets": { "pitch": "...", "call_script": "..." } }
  ],
  "buyer_discovery_plans": [
    { "vertical": "mortgage_broker", "discovery_plan": {...} }
  ]
}
```

#### **sources.py**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/sources/` | GET | List registered data sources |
| `/sources/add` | POST | Register new source for a city |

---

## Database Schema

### Tables (SQLAlchemy Models)

#### `permits`
```python
id (PK)
raw_json (JSONB) – raw source data
permit_id, city, address, lat, lon
permit_type, description, valuation, status
filed_date, issued_date
applicant, contractor, owner
source_url
created_at
```

#### `scores`
```python
id (PK)
permit_id (FK) → permits
win_score, value_score, delay_score, commercial_score, competition_score
reasoning (text explanation)
created_at
```

#### `enrichments`
```python
id (PK)
permit_id (FK) → permits
type (e.g., "assessor", "news", "liens")
data (JSONB) – enrichment payload
url – source URL
created_at
```

#### `packages`
```python
id (PK)
permit_id (FK) → permits
vertical (e.g., "mortgage_broker")
content (JSONB) – curated package
created_at
```

#### `sources`
```python
id (PK)
city (UNIQUE)
urls (JSONB) – array of source objects
last_fetch (TIMESTAMP)
created_at
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend API** | FastAPI | Async REST API, auto-docs |
| **ORM** | SQLAlchemy | Database abstraction |
| **Database** | PostgreSQL (prod) /<br/>SQLite (dev) | Persistent data storage |
| **Background** | Celery + Redis | Async tasks (auto-OSINT, batch processing) |
| **Frontend** | React + Axios | Dashboard UI |
| **Deployment** | Docker + docker-compose | Local & cloud deployment |

---

## Request/Response Flow Example

### Scenario: Mortgage Broker Wants to Buy Intelligence on a $2.5M Project

**1. Ingest Permit**
```bash
POST /permits/ingest
{
  "permit_id": "SF-2024-001",
  "city": "San Francisco",
  "address": "100 Market St",
  "valuation": 2500000,
  "permit_type": "Commercial",
  "description": "TI for tech office, electrical work required"
}
→ Returns permit with id: 42
```

**2. Analyze (Full Pipeline)**
```bash
POST /permits/42/analyze
→ Returns:
  - WIN score: 0.72 (high opportunity)
  - Leverage angles: "financing_arbitrage" + "vendor_arbitrage"
  - Vertical packages: [mortgage_broker, GC, electrician, supplier]
  - Package for mortgage broker includes:
    * Valuation: $2.5M
    * Owner contact: [TBD]
    * Property tax status: [enriched]
    * Financing gap analysis: High
    - Asset pack: pitch email, call script, deal terms
    - Buyer discovery: SF lenders, queries, qualification questions
```

**3. Buyer Discovery Execution**
- Use provided queries: "site:linkedin.com 'San Francisco' commercial lender"
- Research on: FINRA BrokerCheck, SBA Registered Lenders list
- Ask qualification: "Do you provide bridge financing?"

**4. Outreach**
- Send templated email (from asset pack)
- Follow up with call script
- Handle objections using provided response
- Close deal (fixed fee $10k, or 10% of origination fee if hybrid)

---

## Extensibility

### Adding a New Vertical

1. **Update `curation_service.py`:**
   ```python
   VERTICALS["new_vertical"] = {
       "description": "...",
       "key_fields": [...],
       "leverage_angle": "...",
   }
   ```

2. **Add to `buyer_discovery_service.py`:**
   ```python
   discovery_plans["new_vertical"] = {
       "why_they_pay": "...",
       "queries": [...],
       "directories": [...]
   }
   ```

3. **Add to `asset_service.py`:**
   ```python
   templates["new_vertical"] = { "subject": "...", "body": "..." }
   ```

4. **Test via API:**
   ```bash
   POST /permits/{id}/analyze
   → Includes new_vertical in packages
   ```

---

### Enhancing OSINT Enrichment

**Current**: Stubbed in `osint_service.py`

**To activate**, implement data fetches:
```python
def enrich(permit):
    enrichments = []
    
    # Assessor data
    assessor_data = fetch_assessor(permit.address)
    enrichments.append({
        "type": "assessor",
        "data": assessor_data,
        "url": "county.assessor.gov"
    })
    
    # Licenses
    licenses = fetch_business_licenses(permit.owner)
    enrichments.append(...)
    
    # News
    articles = fetch_news(permit.contractor)
    enrichments.append(...)
    
    return enrichments
```

---

## Performance & Scaling

### Current Capacity
- **SQLite** (default): Handles 10,000s of permits locally
- **PostgreSQL** (production): Scales to millions with indexing

### Optimization Points
1. **Async Processing**: Celery jobs for enrichment & asset generation
2. **Caching**: Cache buyer discovery queries, OSINT results
3. **Batch Operations**: Ingest 100+ permits at once
4. **Database Indexes**: `permits(city, status, valuation)`, `scores(win_score)`

### Deployment Options
- **Local**: `docker-compose up` (all-in-one)
- **Render**: Push Dockerfile, PostgreSQL add-on
- **AWS**: ECS + RDS + S3 (asset storage)
- **Heroku**: Docker runtime, PostgreSQL

---

## Security Considerations

1. **Data Privacy**: NDAs enforced, source URLs cited (transparency)
2. **Rate Limiting**: Respect `robots.txt` on all public data fetches
3. **Authentication**: Optional JWT for solo user (`.env` config)
4. **HTTPS**: Required in production (handled by deployment platform)
5. **API Keys**: All external API calls use free public APIs only

---

## Testing

### Unit Tests (`backend/tests/`)
- API endpoint validation
- Ingest normalization
- Scoring logic
- Database CRUD

### Integration Tests
- `test_pipeline.py` – End-to-end flow

### CI/CD
- Tests run in `docker-compose` before deployment
- All new commits validated with `pytest`

---

## Known Limitations & Future Work

### Current (MVP)
- ✓ Permit ingestion, scoring, synthesis
- ✓ Multi-vertical curation
- ✓ Asset generation templates
- ✓ Buyer discovery guidance
- ✗ No real auto-OSINT (stubbed)
- ✗ No real data sources (test data only)
- ✗ Limited UI (minimal dashboard)

### Roadmap
1. **Phase 2**: Integrate Socrata API + ArcGIS real data sources
2. **Phase 3**: Implement full auto-OSINT (assessor, news, licenses)
3. **Phase 4**: Enhanced UI (interactive pipeline, PDF export)
4. **Phase 5**: Real buyer matching (CRM integration)
5. **Phase 6**: ML scoring (train on historical deal success)

---

## Contact & Questions

For architectural questions or feature requests:
- Check [README.md](./README.md) for full documentation
- Review inline code comments
- Run [QUICKSTART.md](./QUICKSTART.md) to verify setup
