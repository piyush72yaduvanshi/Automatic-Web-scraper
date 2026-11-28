"""FastAPI Router for Multi-Platform Social Media Automation Engine."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_api_key
from app.services.social_service import SocialService

router = APIRouter(prefix="/social", tags=["Social Media Automation"], dependencies=[Depends(verify_api_key)])


# =============================================================================
# 1. CONNECTED ACCOUNTS MANAGEMENT
# =============================================================================

@router.get("/accounts")
def list_connected_accounts(db: Session = Depends(get_db)):
    """List all connected social media accounts with health and follower metrics."""
    return SocialService.list_accounts(db=db)


@router.post("/accounts/{account_id}/test")
async def test_account_connection(account_id: str, db: Session = Depends(get_db)):
    """Test connection to official platform API and update health status."""
    try:
        return await SocialService.test_account_connection(account_id=account_id, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# 2. AI RESEARCH & MULTI-PLATFORM GENERATION
# =============================================================================

@router.post("/research")
async def research_topic(data: Dict[str, Any] = Body(...)):
    """AI researches trending hooks, audience resonance points, and hashtags."""
    topic = data.get("topic", "")
    target_audience = data.get("target_audience", "B2B Founders & Growth Leaders")
    if not topic.strip():
        raise HTTPException(status_code=400, detail="Field 'topic' is required.")
    return await SocialService.research_topic(topic=topic, target_audience=target_audience)


@router.post("/generate")
async def generate_platform_posts(data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """
    AI generates platform-specific posts, captions, hashtags, and creative briefs
    across Instagram, Facebook, X, and LinkedIn (Personal & Org).
    """
    try:
        return await SocialService.generate_platform_posts(data=data, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# 3. POSTS CRUD, PREVIEW & EDITING
# =============================================================================

@router.get("/posts")
def list_social_posts(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List social media posts with optional platform and status filters."""
    return SocialService.list_posts(db=db, platform=platform, status=status, limit=limit)


@router.put("/posts/{post_id}")
def update_social_post(post_id: str, data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """Edit post caption, hashtags, media URLs, or scheduled time before publishing."""
    try:
        return SocialService.update_post(post_id=post_id, data=data, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/posts/{post_id}/approve")
def approve_social_post(post_id: str, db: Session = Depends(get_db)):
    """Approve a staged draft post for scheduling or immediate publishing."""
    try:
        return SocialService.approve_post(post_id=post_id, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/posts/{post_id}/publish")
async def publish_social_post_now(post_id: str, db: Session = Depends(get_db)):
    """Immediately publish post via official platform API with strict confirmation."""
    try:
        return await SocialService.publish_post(post_id=post_id, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/publish-scheduled")
async def publish_due_scheduled_posts(db: Session = Depends(get_db)):
    """Trigger scheduled publishing cycle for all posts currently due."""
    try:
        return await SocialService.run_scheduled_publishing(db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 4. AUTOMATION RULES & MODES
# =============================================================================

@router.get("/rules")
def list_automation_rules(db: Session = Depends(get_db)):
    """List automation rules (Manual, Approval-based, Fully automated)."""
    return SocialService.list_automation_rules(db=db)


@router.post("/rules/{rule_id}/run")
async def run_automation_rule(rule_id: str, db: Session = Depends(get_db)):
    """Manually trigger an automation rule to research and generate scheduled posts."""
    try:
        return await SocialService.run_automation_rule(rule_id=rule_id, db=db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# 5. TELEMETRY, ANALYTICS & REPORTS
# =============================================================================

@router.get("/analytics")
def get_social_analytics(db: Session = Depends(get_db)):
    """Retrieve real cross-platform analytics and AI performance report."""
    return SocialService.get_social_analytics(db=db)


@router.post("/analytics/sync")
async def sync_platform_metrics(db: Session = Depends(get_db)):
    """Fetch live engagement metrics from platform APIs for recent posts."""
    try:
        return await SocialService.sync_platform_metrics(db=db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 6. AUTONOMOUS SOCIAL LISTENING & LEAD EXTRACTION AGENT
# =============================================================================

@router.post("/listening/run-now")
async def run_social_listening_scan(
    data: Dict[str, Any] = Body(default={}),
    db: Session = Depends(get_db),
):
    """
    On-demand execution of the Autonomous Social Listening Agent across FB, Insta, X, and LinkedIn.
    Scans posts, comments, buyer intent keywords, extracts leads, and auto-enrolls in outreach!
    """
    from app.services.social_listening_agent import SocialListeningAgent
    platforms = data.get("platforms", ["FACEBOOK", "INSTAGRAM", "X", "LINKEDIN"])
    keywords = data.get("keywords")
    limit = data.get("limit_per_platform", 5)
    days_back = data.get("days_back", 3)
    try:
        return await SocialListeningAgent.run_listening_scan(
            platforms=platforms,
            keywords=keywords,
            days_back=days_back,
            limit_per_platform=limit,
            db=db,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/listening/status")
def get_social_listening_status(db: Session = Depends(get_db)):
    """Retrieve social listening agent stats, leads captured, and supported channels."""
    from app.models.social_media_lead import SocialMediaLead
    total_captured = db.query(SocialMediaLead).count()
    return {
        "status": "active",
        "channels": ["FACEBOOK", "INSTAGRAM", "X", "LINKEDIN"],
        "total_social_leads_captured": total_captured,
        "default_schedule": "Every 4 Hours + Daily Comprehensive Scan",
        "auto_outreach_enabled": True,
    }

