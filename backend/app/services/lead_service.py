"""Lead service for managing business leads."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc

from app.models import (
    BusinessLead,
    LeadContact,
    ContactType,
    LeadSocialProfile,
    SocialPlatform,
    LeadSourceEvidence,
)
from app.extractors import PhoneExtractor


class LeadService:
    """Service for business lead operations."""
    
    @staticmethod
    def create_or_update_lead(db: Session, lead_data: Dict[str, Any]) -> BusinessLead:
        """
        Create or update a business lead and attach initial contact info if present.
        """
        data = dict(lead_data)
        initial_phone = data.pop("phone", None)
        data.pop("rating", None)
        data.pop("reviews", None)

        # Check for existing lead by provider external ID or name + website
        existing_lead = None
        if data.get("provider_external_id"):
            existing_lead = db.query(BusinessLead).filter(
                BusinessLead.provider_external_id == data["provider_external_id"]
            ).first()

        if not existing_lead and data.get("business_name") and data.get("website"):
            existing_lead = db.query(BusinessLead).filter(
                BusinessLead.business_name == data["business_name"],
                BusinessLead.website == data["website"],
            ).first()

        valid_columns = {c.name for c in BusinessLead.__table__.columns}
        clean_data = {k: v for k, v in data.items() if k in valid_columns}

        if existing_lead:
            # Update existing lead with non-null values
            for key, value in clean_data.items():
                if value is not None:
                    setattr(existing_lead, key, value)
            db.commit()
            db.refresh(existing_lead)
            lead = existing_lead
        else:
            # Create new lead
            lead = BusinessLead(**clean_data)
            db.add(lead)
            db.commit()
            db.refresh(lead)

        # Add initial phone if discovered directly (e.g. from Google Maps card)
        if initial_phone:
            normalized_ph = PhoneExtractor.normalize_phone(initial_phone) or initial_phone
            existing_phone_contact = db.query(LeadContact).filter(
                LeadContact.lead_id == lead.id,
                LeadContact.normalized_value == normalized_ph,
            ).first()

            if not existing_phone_contact:
                db.add(LeadContact(
                    lead_id=lead.id,
                    contact_type=ContactType.PHONE,
                    original_value=initial_phone,
                    normalized_value=normalized_ph,
                    verification_status="verified",
                    source_url="https://maps.google.com",
                ))
                db.commit()

        return lead
    
    @staticmethod
    def get_lead(db: Session, lead_id: UUID) -> Optional[BusinessLead]:
        """Get lead by ID with related data."""
        return db.query(BusinessLead).filter(BusinessLead.id == lead_id).first()
    
    @staticmethod
    def list_leads(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None,
        city: Optional[str] = None,
        has_email: Optional[bool] = None,
        has_phone: Optional[bool] = None,
        has_social: Optional[bool] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        List business leads with filters and pagination.
        """
        from sqlalchemy import case
        
        query = db.query(
            BusinessLead,
            func.count(func.distinct(
                case((LeadContact.contact_type == ContactType.EMAIL, LeadContact.id), else_=None)
            )).label("email_count"),
            func.count(func.distinct(
                case((LeadContact.contact_type == ContactType.PHONE, LeadContact.id), else_=None)
            )).label("phone_count"),
            func.count(func.distinct(LeadSocialProfile.id)).label("social_count"),
        ).outerjoin(LeadContact, BusinessLead.id == LeadContact.lead_id)\
         .outerjoin(LeadSocialProfile, BusinessLead.id == LeadSocialProfile.lead_id)
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    BusinessLead.business_name.ilike(f"%{search}%"),
                    BusinessLead.category.ilike(f"%{search}%"),
                )
            )
        
        if category:
            query = query.filter(BusinessLead.category.ilike(f"%{category}%"))
        
        if city:
            query = query.filter(BusinessLead.city.ilike(f"%{city}%"))
        
        query = query.group_by(BusinessLead.id)
        
        # Apply email/phone/social filters
        if has_email is not None:
            if has_email:
                query = query.having(func.count(func.distinct(
                    case((LeadContact.contact_type == ContactType.EMAIL, LeadContact.id), else_=None)
                )) > 0)
            else:
                query = query.having(func.count(func.distinct(
                    case((LeadContact.contact_type == ContactType.EMAIL, LeadContact.id), else_=None)
                )) == 0)
        
        if has_phone is not None:
            if has_phone:
                query = query.having(func.count(func.distinct(
                    case((LeadContact.contact_type == ContactType.PHONE, LeadContact.id), else_=None)
                )) > 0)
            else:
                query = query.having(func.count(func.distinct(
                    case((LeadContact.contact_type == ContactType.PHONE, LeadContact.id), else_=None)
                )) == 0)
        
        if has_social is not None:
            if has_social:
                query = query.having(func.count(func.distinct(LeadSocialProfile.id)) > 0)
            else:
                query = query.having(func.count(func.distinct(LeadSocialProfile.id)) == 0)
        
        total = query.count()
        results = query.order_by(desc(BusinessLead.created_at)).offset(skip).limit(limit).all()
        
        leads = []
        for row in results:
            lead = row[0]
            lead_dict = {
                'id': str(lead.id),
                'business_name': lead.business_name,
                'category': lead.category,
                'description': lead.description,
                'address': lead.address,
                'city': lead.city,
                'state': lead.state,
                'country': lead.country,
                'website': lead.website,
                'source_provider': lead.source_provider,
                'provider_external_id': lead.provider_external_id,
                'status': lead.status,
                'created_at': lead.created_at.isoformat() if lead.created_at else None,
                'updated_at': lead.updated_at.isoformat() if lead.updated_at else None,
                'email_count': row[1],
                'phone_count': row[2],
                'social_count': row[3],
            }
            leads.append(lead_dict)
        
        return leads, total
    
    @staticmethod
    def add_enrichment_data(db: Session, lead_id: UUID, enrichment_data: Dict[str, Any]) -> None:
        """
        Add enrichment data to a lead with deduplication and source evidence tracking.
        """
        lead = db.query(BusinessLead).filter(BusinessLead.id == lead_id).first()
        if not lead:
            return

        # Fetch existing emails and phones to avoid duplicates
        existing_contacts = db.query(LeadContact).filter(LeadContact.lead_id == lead_id).all()
        existing_emails = {c.normalized_value.lower() for c in existing_contacts if c.contact_type == ContactType.EMAIL and c.normalized_value}
        existing_phones = {c.normalized_value for c in existing_contacts if c.contact_type == ContactType.PHONE and c.normalized_value}

        # Add emails
        for email_data in enrichment_data.get("emails", []):
            email_val = email_data.get("email", "").lower().strip()
            if email_val and email_val not in existing_emails:
                existing_emails.add(email_val)
                contact = LeadContact(
                    lead_id=lead_id,
                    contact_type=ContactType.EMAIL,
                    original_value=email_val,
                    normalized_value=email_val,
                    verification_status=email_data.get("verification_status", "unverified"),
                    source_url=email_data.get("source_url"),
                )
                db.add(contact)
        
        # Add phones
        for phone_data in enrichment_data.get("phones", []):
            norm_phone = phone_data.get("normalized") or phone_data.get("original")
            if norm_phone and norm_phone not in existing_phones:
                existing_phones.add(norm_phone)
                contact = LeadContact(
                    lead_id=lead_id,
                    contact_type=ContactType.PHONE,
                    original_value=phone_data.get("original", norm_phone),
                    normalized_value=norm_phone,
                    verification_status=phone_data.get("verification_status", "unverified"),
                    source_url=phone_data.get("source_url"),
                )
                db.add(contact)
        
        # Add social profiles
        existing_socials = db.query(LeadSocialProfile).filter(LeadSocialProfile.lead_id == lead_id).all()
        existing_soc_keys = {(s.platform.value if hasattr(s.platform, "value") else str(s.platform), s.profile_url.lower()) for s in existing_socials}

        for social_data in enrichment_data.get("social_profiles", []):
            raw_platform = str(social_data.get("platform", "")).upper()
            if raw_platform == "TWITTER":
                raw_platform = "X"
            
            if raw_platform in SocialPlatform.__members__:
                platform_enum = SocialPlatform[raw_platform]
                url = social_data.get("url", "").strip()
                if url and (platform_enum.value, url.lower()) not in existing_soc_keys:
                    existing_soc_keys.add((platform_enum.value, url.lower()))
                    profile = LeadSocialProfile(
                        lead_id=lead_id,
                        platform=platform_enum,
                        profile_url=url,
                        verification_status=social_data.get("verification_status", "unverified"),
                        source_url=social_data.get("source_url"),
                    )
                    db.add(profile)

        # Add Source Evidence records
        for ev in enrichment_data.get("evidence", []):
            if ev.get("extracted_value") and ev.get("source_url"):
                evidence = LeadSourceEvidence(
                    lead_id=lead_id,
                    field_name=ev.get("field_name", "contact"),
                    extracted_value=str(ev.get("extracted_value")),
                    source_url=str(ev.get("source_url")),
                    provider=ev.get("provider", "enrichment"),
                )
                db.add(evidence)

        # Update description with AI summary if present and more informative
        ai_summary = enrichment_data.get("summary")
        if ai_summary and (not lead.description or len(ai_summary) > len(lead.description)):
            lead.description = ai_summary

        lead.status = "enriched"
        db.commit()
        db.refresh(lead)

    @staticmethod
    async def enrich_lead(db: Session, lead_id: UUID, custom_ai_key: Optional[str] = None) -> BusinessLead:
        """
        Enrich an existing lead using MultiSourceEnricher.
        """
        lead = LeadService.get_lead(db, lead_id)
        if not lead:
            raise ValueError("Lead not found")
        
        from app.providers.enrichment.multi_source_enricher import MultiSourceEnricher
        enricher = MultiSourceEnricher()

        # Find existing phone if any
        existing_phone = None
        phone_contact = db.query(LeadContact).filter(
            LeadContact.lead_id == lead_id,
            LeadContact.contact_type == ContactType.PHONE,
        ).first()
        if phone_contact:
            existing_phone = phone_contact.normalized_value or phone_contact.original_value

        enriched_data = await enricher.enrich_lead(
            business_name=lead.business_name,
            website=lead.website,
            category=lead.category,
            city=lead.city,
            state=lead.state,
            existing_phone=existing_phone,
            custom_ai_key=custom_ai_key,
        )

        LeadService.add_enrichment_data(db, lead_id, enriched_data)
        db.refresh(lead)
        return lead
