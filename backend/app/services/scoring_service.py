from ..models import models
from sqlalchemy.orm import Session
import random

# compute a dummy WIN score for demonstration
def compute_score(permit: models.Permit) -> models.Score:
    # simple heuristic
    value_score = (permit.valuation or 0) / 1000000
    delay_score = 0.5
    commercial_score = 1.0 if permit.permit_type and "commercial" in permit.permit_type.lower() else 0.5
    competition_score = random.random()
    win_score = min(1.0, value_score * 0.5 + delay_score * 0.2 + commercial_score * 0.2 + competition_score * 0.1)
    score = models.Score(
        permit=permit,
        win_score=win_score,
        value_score=value_score,
        delay_score=delay_score,
        commercial_score=commercial_score,
        competition_score=competition_score,
        reasoning="auto-generated",
    )
    return score
