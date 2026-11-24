"""Social Media, Content Marketing, SEO, Paid Ads, and Community Research Models."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.guid import GUID


class ContentItem(Base):
    """Multi-channel content piece mapped across content pillars."""

    __tablename__ = "content_items"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    
    # 5 Content Pillars:
    # TECHNICAL_EXPERTISE, PROOF_OF_WORK, PROBLEM_AWARENESS, COMPANY_UPDATES, OFFERS_AND_SERVICES
    pillar = Column(String(100), default="TECHNICAL_EXPERTISE", index=True)
    target_audience = Column(String(255), nullable=True)
    
    # JSON array of platforms e.g. ["LINKEDIN", "X", "REDDIT"]
    platforms_json = Column(Text, nullable=True)
    
    core_idea = Column(Text, nullable=False)
    # JSON dictionary of drafted text by platform: {"LINKEDIN": "...", "X": "..."}
    platform_drafts_json = Column(Text, nullable=True)
    
    # Status: DRAFT, PENDING_APPROVAL, APPROVED, SCHEDULED, PUBLISHED, REJECTED
    status = Column(String(50), default="DRAFT", index=True)
    published_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    calendar_entries = relationship("ContentCalendarEntry", back_populates="content_item", cascade="all, delete-orphan")


class ContentCalendarEntry(Base):
    """Calendar schedule for a content item on a specific channel."""

    __tablename__ = "content_calendar_entries"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    content_item_id = Column(GUID(), ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String(50), nullable=False)  # LINKEDIN, X, INSTAGRAM, FACEBOOK, REDDIT, QUORA
    scheduled_for = Column(DateTime, nullable=False, index=True)
    
    # Status: SCHEDULED, PUBLISHED, FAILED, CANCELLED
    status = Column(String(50), default="SCHEDULED", index=True)
    # If no live API is connected: NOT_CONFIGURED
    publishing_provider_status = Column(String(50), default="NOT_CONFIGURED")
    external_post_url = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    content_item = relationship("ContentItem", back_populates="calendar_entries")


class SEOProject(Base):
    """SEO and Inbound Marketing campaign/project."""

    __tablename__ = "seo_projects"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    target_domain = Column(String(255), nullable=False)
    target_location = Column(String(100), default="National")
    gsc_connected = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    keywords = relationship("SEOKeyword", back_populates="project", cascade="all, delete-orphan")


class SEOKeyword(Base):
    """Target keyword with clustering, search intent, and content brief status."""

    __tablename__ = "seo_keywords"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID(), ForeignKey("seo_projects.id", ondelete="CASCADE"), nullable=False, index=True)
    keyword = Column(String(255), nullable=False, index=True)
    cluster_name = Column(String(100), default="General")
    
    # Intent: INFORMATIONAL, COMMERCIAL, TRANSACTIONAL, NAVIGATIONAL
    search_intent = Column(String(50), default="COMMERCIAL")
    search_volume = Column(Integer, default=0)
    difficulty_score = Column(Float, default=0.0)
    target_page_type = Column(String(50), default="SERVICE_PAGE")  # SERVICE_PAGE, INDUSTRY_PAGE, LOCATION_PAGE, BLOG
    
    # Content brief and drafted meta
    content_brief = Column(Text, nullable=True)
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    
    status = Column(String(50), default="PLANNED", index=True)  # PLANNED, BRIEF_CREATED, DRAFTED, PUBLISHED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("SEOProject", back_populates="keywords")


class PaidAdReport(Base):
    """Spend, click, and conversion reporting for paid advertising channels."""

    __tablename__ = "paid_ad_reports"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    platform = Column(String(50), nullable=False)  # GOOGLE_ADS, META_ADS, REDDIT_ADS
    campaign_name = Column(String(255), nullable=False)
    spend_usd = Column(Float, default=0.0)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    leads_attributed = Column(Integer, default=0)
    report_date = Column(DateTime, nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CommunityDiscussion(Base):
    """Community research, question discovery, and approved helpful answers."""

    __tablename__ = "community_discussions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    platform = Column(String(50), default="REDDIT")  # REDDIT, QUORA, FORUM
    thread_title = Column(String(500), nullable=False)
    thread_url = Column(String(500), nullable=False)
    topic = Column(String(255), nullable=True)
    relevance_score = Column(Float, default=0.8)
    draft_response = Column(Text, nullable=True)
    
    # Status: PENDING_REVIEW, APPROVED, POSTED, DISMISSED
    status = Column(String(50), default="PENDING_REVIEW", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

