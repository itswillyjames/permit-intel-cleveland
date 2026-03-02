from .celery_app import celery
from ..models.database import SessionLocal
from ..models import models
from ..services import osint_service, scoring_service, curation_service, asset_service

@celery.task
def process_permit(permit_id: int):
    db = SessionLocal()
    try:
        permit = db.query(models.Permit).get(permit_id)
        if not permit:
            return
        # score
        score = scoring_service.compute_score(permit)
        db.add(score)
        db.commit()
        # maybe enrich and other pipeline steps
        # stub for demonstration
    finally:
        db.close()
