"""Email Deliverability, Mailbox Health, and Domain Authentication Service.

Handles SPF, DKIM, DMARC, MX verification, connected mailbox health tracking,
email event logging, automatic safety pauses, and the Global Outbound Kill Switch.
"""

from typing import Dict, Any, List, Optional
import json
import uuid
import logging
from datetime import datetime
from sqlalchemy.orm import Session
import dns.resolver

from app.models.deliverability import EmailAccount, EmailDomain, EmailEvent
from app.models.outreach import OutreachCampaign
from app.models.orchestration import AuditLog

logger = logging.getLogger(__name__)


class DeliverabilityService:
    """Manages email infrastructure health, domain DNS authentication, and deliverability protection."""

    # In-memory kill switch with fallback flag; also persisted via memory/audit
    _global_outbound_kill_switch: bool = False

    @classmethod
    def get_kill_switch_status(cls) -> bool:
        """Returns True if global outbound sending is halted."""
        return cls._global_outbound_kill_switch

    @classmethod
    def set_kill_switch(cls, enabled: bool, reason: str, db: Session) -> Dict[str, Any]:
        """Activate or deactivate the global outbound kill switch."""
        cls._global_outbound_kill_switch = enabled
        log = AuditLog(
            action="KILL_SWITCH_TOGGLED",
            entity_type="system",
            details=json.dumps({"kill_switch_active": enabled, "reason": reason}),
        )
        db.add(log)
        db.commit()
        return {"kill_switch_active": enabled, "reason": reason, "timestamp": datetime.utcnow().isoformat()}

    @classmethod
    def check_duplicate_send(cls, recipient: str, campaign_id: Optional[str], db: Session) -> bool:
        """
        Check if recipient was already sent an email from this campaign or recently.
        Returns True if a duplicate send is detected (should be blocked).
        """
        q = db.query(EmailEvent).filter(
            EmailEvent.recipient == recipient.lower().strip(),
            EmailEvent.event_type.in_(["SENT", "DELIVERED"]),
        )
        if campaign_id:
            try:
                q = q.filter(EmailEvent.campaign_id == uuid.UUID(str(campaign_id)))
            except Exception:
                pass
        return q.count() > 0

    @classmethod
    def verify_domain_dns(cls, domain_name: str, db: Session) -> Dict[str, Any]:
        """
        Performs live DNS queries for SPF, DKIM, DMARC, and MX records.
        Distinguishes VERIFIED, FAILED, UNAVAILABLE, and UNVERIFIED states.
        """
        clean_domain = domain_name.lower().strip().replace("http://", "").replace("https://", "").split("/")[0]
        
        domain_rec = db.query(EmailDomain).filter(EmailDomain.domain_name == clean_domain).first()
        if not domain_rec:
            domain_rec = EmailDomain(domain_name=clean_domain)
            db.add(domain_rec)

        dns_results = {
            "spf_status": "UNAVAILABLE",
            "dkim_status": "UNVERIFIED",
            "dmarc_status": "UNAVAILABLE",
            "mx_status": "UNAVAILABLE",
            "raw_records": {},
        }

        # 1. MX Record Check
        try:
            mx_answers = dns.resolver.resolve(clean_domain, "MX")
            mx_hosts = [str(r.exchange) for r in mx_answers]
            dns_results["raw_records"]["mx"] = mx_hosts
            dns_results["mx_status"] = "VERIFIED" if mx_hosts else "FAILED"
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            dns_results["mx_status"] = "FAILED"
        except Exception as e:
            dns_results["mx_status"] = "UNAVAILABLE"
            dns_results["raw_records"]["mx_error"] = str(e)

        # 2. SPF Record Check (TXT on root domain)
        try:
            txt_answers = dns.resolver.resolve(clean_domain, "TXT")
            spf_records = [str(r) for r in txt_answers if "v=spf1" in str(r).lower()]
            dns_results["raw_records"]["spf"] = spf_records
            dns_results["spf_status"] = "VERIFIED" if spf_records else "FAILED"
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            dns_results["spf_status"] = "FAILED"
        except Exception as e:
            dns_results["spf_status"] = "UNAVAILABLE"
            dns_results["raw_records"]["spf_error"] = str(e)

        # 3. DMARC Record Check (TXT on _dmarc.domain)
        try:
            dmarc_answers = dns.resolver.resolve(f"_dmarc.{clean_domain}", "TXT")
            dmarc_records = [str(r) for r in dmarc_answers if "v=dmarc1" in str(r).lower()]
            dns_results["raw_records"]["dmarc"] = dmarc_records
            dns_results["dmarc_status"] = "VERIFIED" if dmarc_records else "FAILED"
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            dns_results["dmarc_status"] = "FAILED"
        except Exception as e:
            dns_results["dmarc_status"] = "UNAVAILABLE"
            dns_results["raw_records"]["dmarc_error"] = str(e)

        # 4. DKIM Record Check (default selectors: google, default, k1)
        for selector in ["google", "default", "k1"]:
            try:
                dkim_answers = dns.resolver.resolve(f"{selector}._domainkey.{clean_domain}", "TXT")
                dkim_records = [str(r) for r in dkim_answers if "v=dkim1" in str(r).lower() or "k=rsa" in str(r).lower()]
                if dkim_records:
                    dns_results["dkim_status"] = "VERIFIED"
                    dns_results["raw_records"]["dkim"] = dkim_records
                    break
            except Exception:
                continue

        # Update database record
        domain_rec.spf_status = dns_results["spf_status"]
        domain_rec.dkim_status = dns_results["dkim_status"]
        domain_rec.dmarc_status = dns_results["dmarc_status"]
        domain_rec.mx_status = dns_results["mx_status"]
        domain_rec.dns_records_json = json.dumps(dns_results["raw_records"])
        domain_rec.last_checked_at = datetime.utcnow()
        db.commit()

        return {
            "domain_name": clean_domain,
            "spf_status": domain_rec.spf_status,
            "dkim_status": domain_rec.dkim_status,
            "dmarc_status": domain_rec.dmarc_status,
            "mx_status": domain_rec.mx_status,
            "dns_records": dns_results["raw_records"],
            "last_checked_at": domain_rec.last_checked_at.isoformat(),
        }

    @classmethod
    def list_domains(cls, db: Session) -> List[Dict[str, Any]]:
        """List tracked email domains and DNS authentication states."""
        domains = db.query(EmailDomain).order_by(EmailDomain.created_at.desc()).all()
        return [
            {
                "id": str(d.id),
                "domain_name": d.domain_name,
                "spf_status": d.spf_status,
                "dkim_status": d.dkim_status,
                "dmarc_status": d.dmarc_status,
                "mx_status": d.mx_status,
                "dns_records": json.loads(d.dns_records_json) if d.dns_records_json else {},
                "last_checked_at": d.last_checked_at.isoformat() if d.last_checked_at else None,
            }
            for d in domains
        ]

    @classmethod
    def list_mailboxes(cls, db: Session) -> List[Dict[str, Any]]:
        """List connected mailboxes, health statuses, and quotas."""
        cls.seed_default_mailbox_if_empty(db)
        mailboxes = db.query(EmailAccount).order_by(EmailAccount.created_at.desc()).all()
        return [
            {
                "id": str(m.id),
                "email_address": m.email_address,
                "provider": m.provider,
                "oauth_status": m.oauth_status,
                "sending_permissions": m.sending_permissions,
                "daily_quota": m.daily_quota,
                "sent_today": m.sent_today,
                "health_status": m.health_status,
                "last_sync_at": m.last_sync_at.isoformat() if m.last_sync_at else None,
                "last_send_at": m.last_send_at.isoformat() if m.last_send_at else None,
                "last_error": m.last_error,
            }
            for m in mailboxes
        ]

    @classmethod
    def log_email_event(
        cls,
        event_type: str,
        recipient: str,
        campaign_id: Optional[str],
        email_account_id: Optional[str],
        payload: Dict[str, Any],
        db: Session,
    ) -> Dict[str, Any]:
        """
        Logs granular email lifecycle event (QUEUED, SENT, DELIVERED, BOUNCED, FAILED, REPLIED, UNSUBSCRIBED, COMPLAINED).
        Monitors bounce/complaint thresholds and automatically pauses unhealthy campaigns.
        """
        event = EmailEvent(
            event_type=event_type.upper(),
            recipient=recipient.lower().strip(),
            campaign_id=uuid.UUID(str(campaign_id)) if campaign_id else None,
            email_account_id=uuid.UUID(str(email_account_id)) if email_account_id else None,
            event_payload=json.dumps(payload),
        )
        db.add(event)

        # Update mailbox counter if SENT
        if event_type.upper() == "SENT" and email_account_id:
            mb = db.query(EmailAccount).filter(EmailAccount.id == uuid.UUID(str(email_account_id))).first()
            if mb:
                mb.sent_today += 1
                mb.last_send_at = datetime.utcnow()

        db.commit()

        # Check safety threshold if BOUNCE or COMPLAINT
        if campaign_id and event_type.upper() in ["BOUNCED", "COMPLAINED"]:
            cls._evaluate_campaign_health(campaign_id=str(campaign_id), db=db)

        return {"event_id": str(event.id), "event_type": event.event_type}

    @classmethod
    def _evaluate_campaign_health(cls, campaign_id: str, db: Session) -> None:
        """
        Pauses campaign if bounce rate > 5% or complaint rate > 0.1% to preserve domain reputation.
        """
        try:
            cid = uuid.UUID(str(campaign_id))
        except Exception:
            return

        total_sent = db.query(EmailEvent).filter(EmailEvent.campaign_id == cid, EmailEvent.event_type == "SENT").count()
        if total_sent < 10:
            return  # Need statistically meaningful volume before pausing

        total_bounces = db.query(EmailEvent).filter(EmailEvent.campaign_id == cid, EmailEvent.event_type == "BOUNCED").count()
        total_complaints = db.query(EmailEvent).filter(EmailEvent.campaign_id == cid, EmailEvent.event_type == "COMPLAINED").count()

        bounce_rate = total_bounces / total_sent
        complaint_rate = total_complaints / total_sent

        if bounce_rate > 0.05 or complaint_rate > 0.001:
            camp = db.query(OutreachCampaign).filter(OutreachCampaign.id == cid).first()
            if camp and camp.status != "PAUSED":
                camp.status = "PAUSED"
                logger.warning(f"CAMPAIGN PAUSED AUTOMATICALLY: High bounce/complaint rate on campaign {camp.name}")
                log = AuditLog(
                    action="CAMPAIGN_AUTO_PAUSED",
                    entity_type="campaign",
                    entity_id=str(camp.id),
                    details=json.dumps({
                        "reason": "Exceeded safe deliverability thresholds",
                        "bounce_rate": f"{bounce_rate * 100:.1f}%",
                        "complaint_rate": f"{complaint_rate * 100:.2f}%",
                    }),
                )
                db.add(log)
                db.commit()

    @classmethod
    def get_deliverability_stats(cls, db: Session) -> Dict[str, Any]:
        """Aggregate deliverability health metrics across all events."""
        total_sent = db.query(EmailEvent).filter(EmailEvent.event_type == "SENT").count()
        total_delivered = db.query(EmailEvent).filter(EmailEvent.event_type == "DELIVERED").count()
        total_bounced = db.query(EmailEvent).filter(EmailEvent.event_type == "BOUNCED").count()
        total_replied = db.query(EmailEvent).filter(EmailEvent.event_type == "REPLIED").count()
        total_unsub = db.query(EmailEvent).filter(EmailEvent.event_type == "UNSUBSCRIBED").count()
        total_complaints = db.query(EmailEvent).filter(EmailEvent.event_type == "COMPLAINED").count()

        bounce_rate = (total_bounced / total_sent * 100) if total_sent > 0 else 0.0
        reply_rate = (total_replied / total_sent * 100) if total_sent > 0 else 0.0

        return {
            "kill_switch_active": cls.get_kill_switch_status(),
            "total_sent": total_sent,
            "total_delivered": total_delivered,
            "total_bounced": total_bounced,
            "total_replied": total_replied,
            "total_unsubscribed": total_unsub,
            "total_complaints": total_complaints,
            "bounce_rate_percent": round(bounce_rate, 2),
            "reply_rate_percent": round(reply_rate, 2),
            "mailbox_count": db.query(EmailAccount).count(),
            "domain_count": db.query(EmailDomain).count(),
        }

    @classmethod
    def seed_default_mailbox_if_empty(cls, db: Session) -> None:
        """Ensure primary mailbox entry exists."""
        if db.query(EmailAccount).count() == 0:
            mb = EmailAccount(
                email_address="outreach@primary-sales.com",
                provider="GMAIL",
                oauth_status="CONNECTED",
                sending_permissions=True,
                daily_quota=50,
                sent_today=0,
                health_status="HEALTHY",
            )
            db.add(mb)
            db.commit()

