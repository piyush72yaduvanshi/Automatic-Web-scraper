"""IMAP Automated Inbound Reply Tracking Engine.

Connects to IMAP mailboxes (Gmail, Custom Mail Servers, Outlook, Zoho, etc.),
detects inbound prospect replies to cold outreach sequences via RFC 2822
In-Reply-To / References headers or recipient matching, logs replies,
triggers the Reply Intelligence classification engine, stops follow-up drips,
and dispatches real-time outbound webhooks.
"""

import imaplib
import email
from email.header import decode_header
import ssl
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import logging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.crm import Email, Activity
from app.models.outreach import Conversation, ConversationMessage
from app.services.reply_intelligence_service import ReplyIntelligenceService
from app.services.webhook_service import WebhookService
from app.services.provider_health_service import ProviderHealthService, IntegrationStatus

logger = logging.getLogger(__name__)


class IMAPReplyTrackerService:
    """Enterprise IMAP Inbound Reply Tracker and Thread Synchronizer."""

    provider_name: str = "imap"

    @classmethod
    def is_configured(cls) -> bool:
        """Returns True if minimum required IMAP configuration is present."""
        return bool(
            settings.IMAP_HOST
            and settings.IMAP_USER
            and settings.IMAP_PASSWORD
        )

    @classmethod
    def _decode_header_str(cls, header_val: Optional[str]) -> str:
        """Safely decode RFC 2047 MIME headers into standard Python string."""
        if not header_val:
            return ""
        try:
            decoded_parts = decode_header(header_val)
            result = []
            for text, encoding in decoded_parts:
                if isinstance(text, bytes):
                    result.append(text.decode(encoding or "utf-8", errors="replace"))
                else:
                    result.append(str(text))
            return " ".join(result).strip()
        except Exception:
            return str(header_val)

    @classmethod
    def _extract_body_text(cls, msg: email.message.Message) -> str:
        """Extract plain text or fallback HTML body from an email Message object."""
        body_text = ""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition") or "")
                    if "attachment" in content_disposition:
                        continue
                    if content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            body_text = payload.decode(charset, errors="replace")
                            break
                    elif content_type == "text/html" and not body_text:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            raw_html = payload.decode(charset, errors="replace")
                            # Simple tag strip for fallback
                            import re
                            body_text = re.sub(r"<[^>]+>", " ", raw_html).strip()
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    body_text = payload.decode(charset, errors="replace")
        except Exception as e:
            logger.warning(f"Error decoding email body: {e}")
            body_text = str(msg.get_payload() or "")

        return body_text.strip()

    @classmethod
    async def poll_replies(cls, db: Session, limit: int = 50) -> Dict[str, Any]:
        """
        Polls IMAP mailbox for UNSEEN replies, correlates with sent emails,
        and triggers AI reply intelligence + workflow stop actions.
        """
        if not cls.is_configured():
            logger.info("[IMAPReplyTracker DEV MODE] IMAP is not configured. Running safe simulation check.")
            return {
                "success": True,
                "mode": "dev_simulation",
                "message": "IMAP not configured. No mailbox polled.",
                "checked_messages": 0,
                "matched_replies": 0,
                "replies": [],
            }

        host = settings.IMAP_HOST
        port = settings.IMAP_PORT
        user = settings.IMAP_USER
        password = settings.IMAP_PASSWORD
        mailbox = settings.IMAP_MAILBOX or "INBOX"

        mail = None
        matched_results = []
        checked_count = 0

        try:
            if settings.IMAP_USE_SSL or port == 993:
                context = ssl.create_default_context()
                mail = imaplib.IMAP4_SSL(host, port, ssl_context=context)
            else:
                mail = imaplib.IMAP4(host, port)

            mail.login(user, password)
            status, _ = mail.select(mailbox)
            if status != "OK":
                raise RuntimeError(f"Failed to select IMAP mailbox '{mailbox}'. Status: {status}")

            # Search for unread messages
            typ, data = mail.search(None, "UNSEEN")
            if typ != "OK" or not data or not data[0]:
                logger.info("IMAP polling completed: No UNSEEN messages found.")
                ProviderHealthService.record_success(cls.provider_name)
                return {
                    "success": True,
                    "mode": "live",
                    "checked_messages": 0,
                    "matched_replies": 0,
                    "replies": [],
                }

            msg_nums = data[0].split()
            # Process newest first up to limit
            msg_nums = msg_nums[-limit:]
            checked_count = len(msg_nums)

            for num in msg_nums:
                typ, msg_data = mail.fetch(num, "(RFC822)")
                if typ != "OK" or not msg_data or not msg_data[0]:
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Extract headers
                sender_raw = msg.get("From", "")
                sender_name, sender_email = email.utils.parseaddr(sender_raw)
                sender_email = sender_email.lower().strip()
                subject = cls._decode_header_str(msg.get("Subject", ""))
                in_reply_to = (msg.get("In-Reply-To") or "").strip()
                references = (msg.get("References") or "").strip()
                body_text = cls._extract_body_text(msg)

                # Correlate with sent emails in database
                matched_email: Optional[Email] = None

                # 1. Match by Message-ID references
                if in_reply_to:
                    matched_email = db.query(Email).filter(
                        Email.sent_message_id == in_reply_to
                    ).first()

                if not matched_email and references:
                    for ref in references.split():
                        ref_clean = ref.strip()
                        if ref_clean:
                            matched_email = db.query(Email).filter(
                                Email.sent_message_id == ref_clean
                            ).first()
                            if matched_email:
                                break

                # 2. Fallback correlation: Match by recipient email where direction was OUTBOUND
                if not matched_email and sender_email:
                    matched_email = db.query(Email).filter(
                        Email.to_email == sender_email,
                        Email.direction == "OUTBOUND",
                        Email.status.in_(["sent", "delivered", "opened", "clicked"]),
                    ).order_by(Email.sent_at.desc()).first()

                if matched_email:
                    # Update email status in DB
                    matched_email.status = "replied"
                    matched_email.replied_at = datetime.utcnow()

                    # Find or initialize threaded Conversation
                    conv = None
                    if matched_email.contact_id:
                        conv = db.query(Conversation).filter(
                            Conversation.contact_id == matched_email.contact_id,
                            Conversation.channel == "EMAIL",
                        ).first()

                    if not conv:
                        conv = Conversation(
                            id=uuid.uuid4(),
                            channel="EMAIL",
                            contact_id=matched_email.contact_id,
                            company_id=matched_email.company_id,
                            subject=subject or matched_email.subject,
                            status="ACTIVE",
                            last_message_at=datetime.utcnow(),
                        )
                        db.add(conv)
                        db.flush()

                    # Trigger Reply Intelligence (Categorization, Stop Conditions, CRM alerts)
                    intel_result = await ReplyIntelligenceService.process_incoming_message(
                        conversation_id=str(conv.id),
                        sender=sender_email,
                        body_text=body_text,
                        db=db,
                    )

                    # Log CRM activity
                    activity = Activity(
                        contact_id=matched_email.contact_id,
                        company_id=matched_email.company_id,
                        deal_id=matched_email.deal_id,
                        activity_type="EMAIL",
                        title=f"Prospect replied: {subject[:100]}",
                        description=f"Intent: {intel_result.get('classification')} | Sentiment: {intel_result.get('sentiment')}\n\nSnippet: {body_text[:300]}",
                        created_at=datetime.utcnow(),
                    )
                    db.add(activity)
                    db.commit()

                    # Dispatch real-time outbound webhook
                    try:
                        WebhookService.dispatch("email.replied", {
                            "email_id": str(matched_email.id),
                            "sender_email": sender_email,
                            "subject": subject,
                            "classification": intel_result.get("classification"),
                            "sentiment": intel_result.get("sentiment"),
                            "suggested_reply": intel_result.get("suggested_reply"),
                            "replied_at": matched_email.replied_at.isoformat(),
                        })
                    except Exception as we:
                        logger.warning(f"Webhook dispatch error for email.replied: {we}")

                    matched_results.append({
                        "email_id": str(matched_email.id),
                        "sender": sender_email,
                        "subject": subject,
                        "classification": intel_result.get("classification"),
                        "sentiment": intel_result.get("sentiment"),
                    })

                    # Mark message as read on IMAP server
                    mail.store(num, "+FLAGS", "\\Seen")

            ProviderHealthService.record_success(cls.provider_name)
            logger.info(
                f"✅ IMAP reply check complete: {checked_count} scanned, {len(matched_results)} matched."
            )

            return {
                "success": True,
                "mode": "live",
                "checked_messages": checked_count,
                "matched_replies": len(matched_results),
                "replies": matched_results,
            }

        except Exception as exc:
            err_msg = str(exc)
            logger.error(f"❌ IMAP reply polling failed: {err_msg}")
            ProviderHealthService.record_failure(
                cls.provider_name,
                err_msg,
                IntegrationStatus.TEMPORARILY_UNAVAILABLE,
            )
            return {
                "success": False,
                "mode": "live_error",
                "error": err_msg,
                "checked_messages": checked_count,
                "matched_replies": 0,
                "replies": [],
            }

        finally:
            if mail:
                try:
                    mail.close()
                    mail.logout()
                except Exception:
                    pass
