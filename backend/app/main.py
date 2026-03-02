from fastapi import FastAPI
from .api import permits, sources, data_sources
from .models.database import engine, Base

# create tables on startup (simple for demo)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Permit Arbitrage Intelligence Hub",
    description="Full-stack permit intelligence platform for commercial real estate opportunities",
    version="1.0.0"
)

# allow CORS for frontend during development
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if True else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(permits.router, prefix="/permits", tags=["permits"])
app.include_router(sources.router, prefix="/sources", tags=["sources"])
app.include_router(data_sources.router, prefix="/data", tags=["data-fetching"])

@app.get("/")
def root():
    """API documentation and health check."""
    return {
        "message": "Permit Arbitrage Intelligence Hub API",
        "version": "1.0.0",
        "docs": "/docs",
        "description": "Ingest permits → Score → Synthesize → Curate → Monetize",
        "features": [
            "Real data source integration (Socrata, ArcGIS)",
            "Auto-OSINT enrichment (public records, news)",
            "Multi-vertical intelligence packages",
            "Buyer discovery & asset generation"
        ]
    }

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "permit-intelligence-hub"}
