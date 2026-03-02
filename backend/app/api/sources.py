from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models import models
from ..models.database import get_db

router = APIRouter()

@router.get("/")
def list_sources(db: Session = Depends(get_db)):
    return db.query(models.Source).all()

@router.post("/add")
def add_source(city: str, urls: dict, db: Session = Depends(get_db)):
    src = models.Source(city=city, urls=urls)
    db.add(src)
    db.commit()
    db.refresh(src)
    return src
