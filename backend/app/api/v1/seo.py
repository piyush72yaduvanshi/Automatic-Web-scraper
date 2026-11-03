"""FastAPI Router for SEO & Inbound Marketing Engine."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_api_key
from app.services.seo_service import SEOService

router = APIRouter(prefix="/seo", tags=["SEO & Inbound Marketing"], dependencies=[Depends(verify_api_key)])


@router.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    """List SEO projects."""
    return SEOService.list_projects(db=db)


@router.get("/projects/{project_id}/keywords")
def list_keywords(project_id: str, db: Session = Depends(get_db)):
    """List keywords and search intent clusters for a project."""
    return SEOService.list_keywords(project_id=project_id, db=db)


@router.post("/projects/{project_id}/clusters")
async def generate_keyword_clusters(
    project_id: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    """AI brainstorms high-intent keywords and semantic clusters."""
    seed_topic = payload.get("seed_topic")
    if not seed_topic:
        raise HTTPException(status_code=400, detail="seed_topic is required")
    try:
        return await SEOService.generate_keyword_clusters(project_id=project_id, seed_topic=seed_topic, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/keywords/{keyword_id}/brief")
async def create_content_brief(keyword_id: str, db: Session = Depends(get_db)):
    """AI creates an SEO content brief and meta title/description."""
    try:
        return await SEOService.create_content_brief(keyword_id=keyword_id, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
