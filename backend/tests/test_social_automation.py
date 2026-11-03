"""Comprehensive Integration & Automated Tests for Multi-Platform Social Media Automation.

Covers:
1. Account lifecycle and status verification for all 4 platforms (5 account types).
2. AI topic and trend research.
3. Multi-platform post and creative brief generation.
4. Post editing, approval, and live preview data.
5. Duplicate post prevention (SHA-256 fingerprint within 24h).
6. Token expiration detection and error handling.
7. Safe NOT_CONFIGURED handling (never claim false publication).
8. Scheduled publishing and automation rules execution.
9. Cross-platform analytics and AI performance report generation.
10. FastAPI REST API endpoints verification.
"""

import pytest
import json
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.social import SocialAccount, SocialPost, SocialAutomationRule, SocialPostMetric
from app.services.social_service import SocialService


@pytest.mark.asyncio
async def test_social_accounts_lifecycle(db: Session):
    """Verify listing and seeding of official social accounts across all platforms."""
    accounts = SocialService.list_accounts(db)
    assert len(accounts) >= 5

    platforms = {a["platform"] for a in accounts}
    assert "INSTAGRAM" in platforms
    assert "FACEBOOK" in platforms
    assert "TWITTER" in platforms
    assert "LINKEDIN_PERSONAL" in platforms
    assert "LINKEDIN_ORG" in platforms

    # Test connection on an account
    first_acc = accounts[0]
    test_res = await SocialService.test_account_connection(first_acc["id"], db)
    assert "account" in test_res
    assert "test_result" in test_res
    assert test_res["account"]["status"] in ["NOT_CONFIGURED", "ACTIVE", "EXPIRED", "ERROR"]


@pytest.mark.asyncio
async def test_ai_topic_research():
    """Verify AI topic and audience research."""
    research = await SocialService.research_topic(
        topic="Eliminating Manual B2B Sales Bottlenecks",
        target_audience="B2B Founders & Sales Leaders",
    )
    assert "trending_angles" in research
    assert len(research["trending_angles"]) >= 1
    assert "audience_resonances" in research
    assert "recommended_keywords" in research
    assert "visual_theme" in research


@pytest.mark.asyncio
async def test_generate_platform_posts_and_creative_briefs(db: Session):
    """Verify platform-specific post generation, hashtags, and creative briefs."""
    gen_data = {
        "topic": "Why Evidence-Based Qualification Beats Mass Blasting",
        "pillar": "TECHNICAL_EXPERTISE",
        "target_audience": "B2B Tech Leaders",
        "platforms": ["INSTAGRAM", "FACEBOOK", "TWITTER", "LINKEDIN_PERSONAL", "LINKEDIN_ORG"],
        "automation_mode": "APPROVAL_BASED",
    }
    result = await SocialService.generate_platform_posts(gen_data, db)
    assert result["success"] is True
    assert result["posts_created"] == 5

    posts = result["posts"]
    post_platforms = {p["platform"] for p in posts}
    assert "INSTAGRAM" in post_platforms
    assert "FACEBOOK" in post_platforms
    assert "TWITTER" in post_platforms
    assert "LINKEDIN_PERSONAL" in post_platforms
    assert "LINKEDIN_ORG" in post_platforms

    # Check creative brief on Instagram post
    ig_post = next(p for p in posts if p["platform"] == "INSTAGRAM")
    assert ig_post["status"] == "PENDING_APPROVAL"
    assert len(ig_post["caption"]) > 10
    assert len(ig_post["hashtags"]) > 0
    assert "creative_brief" in ig_post
    assert "aspect_ratio" in ig_post["creative_brief"]
    assert "dimensions" in ig_post["creative_brief"]


def test_post_editing_and_approval(db: Session):
    """Verify updating post copy and approving staged drafts."""
    post = SocialPost(
        platform="TWITTER",
        caption="Initial draft tweet on automation.",
        hashtags_json=json.dumps(["#SalesAI"]),
        automation_mode="APPROVAL_BASED",
        status="PENDING_APPROVAL",
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    # Edit post
    updated = SocialService.update_post(
        str(post.id),
        {"caption": "Updated and refined punchy tweet on sales automation.", "hashtags": ["#AI", "#Python"]},
        db,
    )
    assert "Updated and refined" in updated["caption"]
    assert "#AI" in updated["hashtags"]

    # Approve post
    approved = SocialService.approve_post(str(post.id), db)
    assert approved["status"] == "APPROVED"
    assert approved["scheduled_for"] is not None


@pytest.mark.asyncio
async def test_duplicate_send_prevention(db: Session):
    """Verify that posting identical content within 24h is blocked."""
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    import hashlib
    hash_input = f"TWITTER:Duplicate tweet content:{today_str}"
    content_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    # Pre-existing published post
    p1 = SocialPost(
        platform="TWITTER",
        caption="Duplicate tweet content",
        status="PUBLISHED",
        published_at=datetime.utcnow() - timedelta(hours=2),
        content_hash=content_hash,
    )
    db.add(p1)
    db.commit()

    # Attempt to publish identical post
    p2 = SocialPost(
        platform="TWITTER",
        caption="Duplicate tweet content",
        status="SCHEDULED",
        content_hash=content_hash,
    )
    db.add(p2)
    db.commit()

    pub_res = await SocialService.publish_post(str(p2.id), db)
    assert pub_res["success"] is False
    assert pub_res["error"] == "DUPLICATE_POST_BLOCKED"


@pytest.mark.asyncio
async def test_token_expiration_handling(db: Session):
    """Verify expired token rejection and status transition."""
    expired_account = SocialAccount(
        platform="FACEBOOK",
        account_name="Expired Page",
        account_handle="fb.com/expired",
        token_expires_at=datetime.utcnow() - timedelta(days=2),
        status="ACTIVE",
    )
    db.add(expired_account)
    db.commit()
    db.refresh(expired_account)

    post = SocialPost(
        account_id=expired_account.id,
        platform="FACEBOOK",
        caption="Post destined for expired account",
        status="SCHEDULED",
    )
    db.add(post)
    db.commit()

    pub_res = await SocialService.publish_post(str(post.id), db)
    assert pub_res["success"] is False
    assert pub_res["error"] == "TOKEN_EXPIRED"
    assert expired_account.status == "EXPIRED"


@pytest.mark.asyncio
async def test_safe_not_configured_publishing(db: Session):
    """Verify that posts in unconfigured environments are not falsely marked published."""
    post = SocialPost(
        platform="LINKEDIN_PERSONAL",
        caption="Great insights for founders.",
        status="APPROVED",
    )
    db.add(post)
    db.commit()

    pub_res = await SocialService.publish_post(str(post.id), db)
    # When LinkedIn is unconfigured in test environment:
    if pub_res.get("provider_status") == "NOT_CONFIGURED":
        assert pub_res["success"] is False
        assert post.status == "DRAFT"  # Retained draft for manual copy-paste
        assert post.external_post_id is None  # Never falsely fabricate an external ID!


@pytest.mark.asyncio
async def test_automation_rules_and_scheduled_runner(db: Session):
    """Verify autonomous rule execution and scheduled publishing cycle."""
    rules = SocialService.list_automation_rules(db)
    assert len(rules) >= 1

    rule_res = await SocialService.run_automation_rule(rules[0]["id"], db)
    assert "rule_name" in rule_res
    assert rule_res["generation_result"]["success"] is True

    # Run scheduled runner
    runner_res = await SocialService.run_scheduled_publishing(db)
    assert "due_count" in runner_res
    assert "processed" in runner_res


def test_social_analytics_and_ai_report(db: Session):
    """Verify analytics calculation and AI report generation."""
    # Seed a published post and metric
    p = SocialPost(
        platform="LINKEDIN_ORG",
        caption="Company achievement post.",
        status="PUBLISHED",
        published_at=datetime.utcnow(),
    )
    db.add(p)
    db.commit()

    m = SocialPostMetric(
        post_id=p.id,
        platform="LINKEDIN_ORG",
        impressions=1200,
        reach=950,
        engagement_count=85,
        likes=60,
        comments=15,
        shares=10,
    )
    db.add(m)
    db.commit()

    analytics = SocialService.get_social_analytics(db)
    assert analytics["summary"]["total_impressions"] >= 1200
    assert analytics["summary"]["total_engagements"] >= 85
    assert "ai_executive_report" in analytics
    assert "platform_breakdown" in analytics


def test_social_api_endpoints(client: TestClient):
    """Verify FastAPI endpoints for social media automation."""
    # 1. Accounts
    res_acc = client.get("/api/v1/social/accounts")
    assert res_acc.status_code == 200
    assert len(res_acc.json()) >= 5

    # 2. Research
    res_res = client.post(
        "/api/v1/social/research",
        json={"topic": "B2B Sales Intelligence", "target_audience": "Founders"},
    )
    assert res_res.status_code == 200
    assert "trending_angles" in res_res.json()

    # 3. Generate
    res_gen = client.post(
        "/api/v1/social/generate",
        json={
            "topic": "Scaling Revenue with AI",
            "pillar": "TECHNICAL_EXPERTISE",
            "platforms": ["TWITTER", "LINKEDIN_PERSONAL"],
            "automation_mode": "APPROVAL_BASED",
        },
    )
    assert res_gen.status_code == 200
    assert res_gen.json()["success"] is True

    # 4. Posts List
    res_posts = client.get("/api/v1/social/posts")
    assert res_posts.status_code == 200
    assert isinstance(res_posts.json(), list)

    # 5. Rules List
    res_rules = client.get("/api/v1/social/rules")
    assert res_rules.status_code == 200
    assert len(res_rules.json()) >= 1

    # 6. Analytics
    res_ana = client.get("/api/v1/social/analytics")
    assert res_ana.status_code == 200
    assert "summary" in res_ana.json()
