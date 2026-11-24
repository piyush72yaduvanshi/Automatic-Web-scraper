"""Social Media Automation Models.

Supports multi-platform social media automation for:
1. Instagram (Graph API / Content Publishing API)
2. Facebook Pages (Graph API)
3. X (Twitter) (API v2)
4. LinkedIn (Personal Profile & Organization Pages)

Includes:
- SocialAccount: Connected accounts, OAuth tokens, handles, expiration, status.
- SocialPost: Platform posts, captions, hashtags, creative briefs, media, scheduling, external IDs, status.
- SocialAutomationRule: Manual, Approval-based, and Fully-automated scheduling rules.
- SocialPostMetric: Impressions, reach, likes, comments, shares, clicks, engagement rates.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.guid import GUID


class SocialAccount(Base):
    """Connected official social media account."""

    __tablename__ = "social_accounts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    # Platform: INSTAGRAM, FACEBOOK, TWITTER, LINKEDIN_PERSONAL, LINKEDIN_ORG
    platform = Column(String(50), nullable=False, index=True)
    account_name = Column(String(255), nullable=False)
    account_handle = Column(String(255), nullable=False)
    account_id = Column(String(255), nullable=True)  # External page_id, ig_user_id, twitter_user_id, linkedin_urn
    
    # Credentials / Tokens
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    
    # Status: ACTIVE, NOT_CONFIGURED, EXPIRED, REVOKED, ERROR
    status = Column(String(50), default="NOT_CONFIGURED", index=True)
    followers_count = Column(Integer, default=0)
    profile_image_url = Column(String(500), nullable=True)
    account_metadata_json = Column(Text, nullable=True)
    
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    posts = relationship("SocialPost", back_populates="account", cascade="all, delete-orphan")


class SocialPost(Base):
    """Platform-specific social media post with creative brief and publishing metadata."""

    __tablename__ = "social_posts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    content_item_id = Column(GUID(), ForeignKey("content_items.id", ondelete="SET NULL"), nullable=True, index=True)
    account_id = Column(GUID(), ForeignKey("social_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Platform: INSTAGRAM, FACEBOOK, TWITTER, LINKEDIN_PERSONAL, LINKEDIN_ORG
    platform = Column(String(50), nullable=False, index=True)
    
    # Content & Copy
    caption = Column(Text, nullable=False)
    hashtags_json = Column(Text, nullable=True)  # JSON array: ["#B2B", "#SalesTech"]
    media_urls_json = Column(Text, nullable=True)  # JSON array of image/video URLs
    
    # Creative Brief: Visual description, target aspect ratio, text overlay, color palette
    creative_brief_json = Column(Text, nullable=True)
    
    # Automation Mode: MANUAL, APPROVAL_BASED, FULLY_AUTOMATED
    automation_mode = Column(String(50), default="APPROVAL_BASED", index=True)
    
    # Publishing Status: DRAFT, PENDING_APPROVAL, APPROVED, SCHEDULED, PUBLISHING, PUBLISHED, FAILED, CANCELLED
    status = Column(String(50), default="DRAFT", index=True)
    scheduled_for = Column(DateTime, nullable=True, index=True)
    published_at = Column(DateTime, nullable=True)
    
    # External Publishing References
    external_post_id = Column(String(255), nullable=True)
    external_post_url = Column(String(500), nullable=True)
    # Publishing Provider Status: LIVE_API, NOT_CONFIGURED, SIMULATED, FAILED
    publishing_provider_status = Column(String(50), default="NOT_CONFIGURED")
    api_response_json = Column(Text, nullable=True)
    
    # Resilience & Failure Handling
    retry_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True, index=True)  # SHA256 for duplicate prevention
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    account = relationship("SocialAccount", back_populates="posts")
    metrics = relationship("SocialPostMetric", back_populates="post", cascade="all, delete-orphan")


class SocialAutomationRule(Base):
    """Rule for autonomous content research, drafting, and scheduling."""

    __tablename__ = "social_automation_rules"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    
    # Mode: MANUAL, APPROVAL_BASED, FULLY_AUTOMATED
    mode = Column(String(50), default="APPROVAL_BASED", index=True)
    
    # Target Platforms: JSON array e.g. ["INSTAGRAM", "FACEBOOK", "TWITTER", "LINKEDIN_PERSONAL", "LINKEDIN_ORG"]
    platforms_json = Column(Text, nullable=False)
    
    # Target Pillars: JSON array e.g. ["TECHNICAL_EXPERTISE", "PROBLEM_AWARENESS"]
    pillars_json = Column(Text, nullable=True)
    
    # Posting schedule times: JSON array of "HH:MM" strings e.g. ["09:00", "15:00"]
    posting_times_json = Column(Text, nullable=True)
    
    max_posts_per_day = Column(Integer, default=2)
    is_active = Column(Boolean, default=True, index=True)
    
    last_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class SocialPostMetric(Base):
    """Performance telemetry and engagement metrics for a published social post."""

    __tablename__ = "social_post_metrics"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    post_id = Column(GUID(), ForeignKey("social_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    
    impressions = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    engagement_count = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    post = relationship("SocialPost", back_populates="metrics")

