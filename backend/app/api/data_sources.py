from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..models import models
from ..models.database import get_db
from ..services import data_fetcher, osint_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/cities")
def list_available_cities():
    """List all cities with pre-configured data sources."""
    cities = data_fetcher.list_available_cities()
    return {
        "cities": cities,
        "count": len(cities),
        "note": "These cities have free, public data sources configured"
    }

@router.get("/{city}/source-config")
def get_source_config(city: str):
    """Get data source configuration for a city."""
    config = data_fetcher.get_source_config(city)
    if not config:
        raise HTTPException(status_code=404, detail=f"City {city} not found")
    return {
        "city": city,
        "config": config
    }

@router.post("/{city}/fetch")
def fetch_city_data(
    city: str,
    limit: int = 100,
    filters: dict = None,
    db: Session = Depends(get_db)
):
    """
    Fetch and ingest permits from a city's data source.
    
    Args:
        city: City name (must be in configured sources)
        limit: Number of permits to fetch
        filters: Optional filters (e.g., {"status": "Issued"})
    
    Returns:
        Ingest results
    """
    logger.info(f"Fetching permits from {city}...")
    
    # Fetch raw data
    raw_permits = data_fetcher.fetch_city_permits(city, limit=limit, filters=filters)
    
    if not raw_permits:
        raise HTTPException(
            status_code=404,
            detail=f"No permits found for {city} or API error"
        )
    
    # Ingest into database
    ingested = []
    for permit_data in raw_permits:
        try:
            permit = models.Permit(
                raw_json=permit_data,
                permit_id=permit_data.get("permit_id"),
                city=permit_data.get("city"),
                address=permit_data.get("address"),
                permit_type=permit_data.get("permit_type"),
                description=permit_data.get("description"),
                valuation=permit_data.get("valuation"),
                status=permit_data.get("status"),
                filed_date=permit_data.get("filed_date"),
                issued_date=permit_data.get("issued_date"),
                applicant=permit_data.get("applicant"),
                contractor=permit_data.get("contractor"),
                owner=permit_data.get("owner"),
                source_url=permit_data.get("source_url"),
            )
            db.add(permit)
            ingested.append(permit_data.get("permit_id"))
        except Exception as e:
            logger.error(f"Error ingesting permit: {e}")
            continue
    
    db.commit()
    
    return {
        "city": city,
        "total_fetched": len(raw_permits),
        "total_ingested": len(ingested),
        "permit_ids": ingested[:10],  # Show first 10
        "note": f"Fetched from {data_fetcher.get_source_config(city).get('socrata', 'unknown')}"
    }

@router.post("/{permit_id}/enrich")
def enrich_permit_osint(
    permit_id: int,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Enrich a permit with free public OSINT data.
    
    Args:
        permit_id: Permit ID to enrich
    
    Returns:
        Enrichment results
    """
    permit = db.query(models.Permit).filter(models.Permit.id == permit_id).first()
    if not permit:
        raise HTTPException(status_code=404, detail="Permit not found")
    
    # Run enrichment
    logger.info(f"Starting OSINT enrichment for permit {permit_id}...")
    
    enrichment_data = osint_service.enrich_permit(
        permit_id,
        {
            "contractor": permit.contractor,
            "owner": permit.owner,
            "address": permit.address,
            "city": permit.city,
        }
    )
    
    # Store enrichments in database
    for enr in enrichment_data:
        enrichment_record = models.Enrichment(
            permit_id=permit_id,
            type=enr["type"],
            data=enr["data"],
            url=enr.get("url", "")
        )
        db.add(enrichment_record)
    
    db.commit()
    
    # Generate summary
    summary = osint_service.generate_osint_summary(enrichment_data)
    
    return {
        "permit_id": permit_id,
        "enrichments_added": len(enrichment_data),
        "types": summary["types"],
        "summary": summary
    }

@router.get("/{permit_id}/enrichments")
def get_permit_enrichments(permit_id: int, db: Session = Depends(get_db)):
    """Get all enrichments for a permit."""
    enrichments = db.query(models.Enrichment).filter(
        models.Enrichment.permit_id == permit_id
    ).all()
    
    if not enrichments:
        raise HTTPException(status_code=404, detail="No enrichments found")
    
    return {
        "permit_id": permit_id,
        "total_enrichments": len(enrichments),
        "enrichments": [
            {
                "type": e.type,
                "data": e.data,
                "url": e.url,
                "created_at": e.created_at.isoformat() if e.created_at else None
            }
            for e in enrichments
        ]
    }
