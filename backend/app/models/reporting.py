"""Automated Daily, Weekly, and Monthly Report Snapshots."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Index

from app.core.database import Base
from app.models.guid import GUID


class ReportSnapshot(Base):
    """Archival report snapshot computed from real operational data."""

    __tablename__ = "report_snapshots"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    # Report Types: DAILY, WEEKLY, MONTHLY
    report_type = Column(String(50), nullable=False, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # JSON structured metrics for this period
    metrics_json = Column(Text, nullable=False)
    executive_summary = Column(Text, nullable=False)
    recommendations_json = Column(Text, nullable=True)  # JSON array of actionable recommendations
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
