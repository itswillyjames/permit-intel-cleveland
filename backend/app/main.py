from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .api import permits, sources, data_sources
from .models.database import engine, Base

# create tables on startup (simple for demo)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# include existing routers for API functionality
app.include_router(permits.router, prefix="/api/permits", tags=["permits"])
app.include_router(sources.router, prefix="/api/sources", tags=["sources"])
app.include_router(data_sources.router, prefix="/api/data", tags=["data-fetching"])

@app.get("/api/health")
def health():
    return {"status": "healthy"}

# Serve static files from build output
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    index_path = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(index_path)

