from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models import models
from ..models.database import get_db
from ..services import (
    ingest_service,
    scoring_service,
    synthesis_service,
    curation_service,
    asset_service,
    buyer_discovery_service,
)

router = APIRouter()

@router.get("/")
def read_permits(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all permits with optional pagination."""
    permits = db.query(models.Permit).offset(skip).limit(limit).all()
    return permits

@router.post("/ingest")
def ingest_permit(data: dict, db: Session = Depends(get_db)):
    """Ingest a single permit record."""
    permit = ingest_service.ingest(data, db)
    return permit

@router.get("/{permit_id}")
def get_permit(permit_id: int, db: Session = Depends(get_db)):
    """Get details of a specific permit."""
    permit = db.query(models.Permit).filter(models.Permit.id == permit_id).first()
    if not permit:
        raise HTTPException(status_code=404, detail="Permit not found")
    return permit

@router.post("/{permit_id}/score")
def score_permit(permit_id: int, db: Session = Depends(get_db)):
    """Compute and store WIN score for a permit."""
    permit = db.query(models.Permit).filter(models.Permit.id == permit_id).first()
    if not permit:
        raise HTTPException(status_code=404, detail="Permit not found")
    
    score = scoring_service.compute_score(permit)
    db.add(score)
    db.commit()
    db.refresh(score)
    return score

@router.post("/{permit_id}/analyze")
def analyze_permit(permit_id: int, db: Session = Depends(get_db)):
    """
    Full permit analysis pipeline:
    1. Retrieve permit
    2. Score
    3. Synthesize opportunities
    4. Curate vertical packages
    5. Identify buyers
    """
    permit = db.query(models.Permit).filter(models.Permit.id == permit_id).first()
    if not permit:
        raise HTTPException(status_code=404, detail="Permit not found")
    
    # Score
    score = db.query(models.Score).filter(models.Score.permit_id == permit_id).first()
    if not score:
        score = scoring_service.compute_score(permit)
        db.add(score)
        db.commit()
        db.refresh(score)
    
    # Synthesize opportunity
    opportunity = synthesis_service.synthesize_opportunity(permit, score)
    
    # Curate multi-vertical packages
    packages = curation_service.curate_permit(permit)
    
    # Cross-sell opportunities
    cross_sells = curation_service.identify_cross_sells(packages)
    
    # Asset pack for each vertical
    asset_packs = []
    for pkg in packages:
        assets = asset_service.generate_assets(permit, pkg, pkg["vertical"])
        asset_packs.append(assets)
    
    # Buyer discovery for each vertical
    discovery_plans = []
    for pkg in packages:
        plan = buyer_discovery_service.generate_buyer_discovery_plan(permit, pkg["vertical"])
        discovery_plans.append(plan)
    
    return {
        "permit": permit,
        "score": {
            "win_score": round(score.win_score, 2),
            "value_score": round(score.value_score, 2),
            "delay_score": round(score.delay_score, 2),
            "commercial_score": round(score.commercial_score, 2),
            "competition_score": round(score.competition_score, 2),
        },
        "opportunity_synthesis": opportunity,
        "multi_vertical_packages": packages,
        "cross_sell_opportunities": cross_sells,
        "asset_packs": asset_packs,
        "buyer_discovery_plans": discovery_plans,
    }

@router.get("/{permit_id}/wins")
def get_wins_table(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get a ranked WINS TABLE of permits sorted by WIN score.
    """
    permit_scores = db.query(models.Permit, models.Score).outerjoin(models.Score).all()
    
    # Sort by win_score descending
    sorted_results = sorted(
        permit_scores,
        key=lambda x: x.Score.win_score if x.Score else 0,
        reverse=True
    )
    
    results = []
    for permit, score in sorted_results[:limit]:
        results.append({
            "id": permit.id,
            "permit_id": permit.permit_id,
            "city": permit.city,
            "address": permit.address,
            "valuation": permit.valuation,
            "win_score": round(score.win_score, 2) if score else None,
            "status": permit.status,
            "permit_type": permit.permit_type,
        })
    
    return {
        "total": len(sorted_results),
        "records": results
    }
