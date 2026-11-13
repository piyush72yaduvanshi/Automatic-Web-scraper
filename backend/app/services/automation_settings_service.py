"""Central configuration service for automation rules and toggles."""

import json
from typing import Any
from sqlalchemy.orm import Session
from app.models.automation import AutomationSettings


class AutomationSettingsService:
    """Manages automation configuration with type-safe getters."""
    
    @classmethod
    def get_setting(cls, key: str, db: Session, default: Any = None) -> Any:
        """Get automation setting value with type conversion."""
        setting = db.query(AutomationSettings).filter(AutomationSettings.setting_key == key).first()
        if not setting:
            return default
        
        if setting.data_type == 'boolean':
            return setting.setting_value.lower() == 'true'
        elif setting.data_type == 'integer':
            return int(setting.setting_value)
        elif setting.data_type == 'json':
            return json.loads(setting.setting_value)
        return setting.setting_value
    
    @classmethod
    def is_auto_enroll_enabled(cls, db: Session) -> bool:
        """Check if auto-enrollment to outreach is enabled."""
        return cls.get_setting('auto_enroll_to_outreach', db, True)
    
    @classmethod
    def is_auto_approve_enabled(cls, db: Session) -> bool:
        """Check if auto-approval of emails is enabled."""
        return cls.get_setting('auto_approve_emails', db, True)
    
    @classmethod
    def is_auto_crm_enabled(cls, db: Session) -> bool:
        """Check if auto-conversion to CRM is enabled."""
        return cls.get_setting('auto_convert_to_crm', db, True)
    
    @classmethod
    def get_min_score_for_outreach(cls, db: Session) -> int:
        """Get minimum qualification score for auto-enrollment."""
        return cls.get_setting('min_score_for_outreach', db, 70)
    
    @classmethod
    def get_min_score_for_crm(cls, db: Session) -> int:
        """Get minimum qualification score for CRM conversion."""
        return cls.get_setting('min_score_for_crm', db, 60)
    
    @classmethod
    def is_email_enrichment_enabled(cls, db: Session) -> bool:
        """Check if email enrichment is enabled."""
        return cls.get_setting('email_enrichment_enabled', db, True)
    
    @classmethod
    def get_batch_size(cls, db: Session) -> int:
        """Get bulk processing batch size."""
        return cls.get_setting('bulk_processing_batch_size', db, 50)
