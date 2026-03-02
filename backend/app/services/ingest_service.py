from ..models import models
from sqlalchemy.orm import Session

# stub for ingest pipeline
def normalize_record(raw: dict) -> dict:
    # minimal: just pass through
    return raw

def ingest(raw: dict, db: Session) -> models.Permit:
    normalized = normalize_record(raw)
    permit = models.Permit(
        raw_json=normalized,
        permit_id=normalized.get("permit_id"),
        city=normalized.get("city"),
        address=normalized.get("address"),
        valuation=normalized.get("valuation"),
        status=normalized.get("status"),
        source_url=normalized.get("source_url"),
    )
    db.add(permit)
    db.commit()
    db.refresh(permit)
    return permit
