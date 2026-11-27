"""SMTP Outbound Communication Provider.

Provides enterprise-grade direct SMTP email delivery with:
1. RFC 2822 compliant unique Message-ID generation and threading headers.
2. Automatic 1x1 transparent tracking pixel injection.
3. Dynamic personalized image link injection.
4. TLS/SSL security negotiation (ports 587, 465, 25).
5. Safe development simulation fallback when credentials are unconfigured.
"""

import smtplib
import ssl
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid, formatdate
from typing import Dict, Any, Optional
import uuid
import logging
import re

from app.core.config import settings
from app.services.provider_health_service import ProviderHealthService, IntegrationStatus

logger = logging.getLogger(__name__)


class SMTPProvider:
    """Enterprise SMTP Provider with open/click tracking injection and safe dev fallback."""

    provider_name: str = "smtp"

    @classmethod
    def is_configured(cls) -> bool:
        """Returns True if minimum required SMTP credentials are set."""
        return bool(
            settings.SMTP_HOST
            and settings.SMTP_USER
            and settings.SMTP_PASSWORD
        )

    @classmethod
    def generate_tracking_token(cls) -> str:
        """Generates a secure unique tracking token for an outbound email."""
        return uuid.uuid4().hex

    @classmethod
    def generate_message_id(cls, domain: Optional[str] = None) -> str:
        """Generates a compliant RFC 2822 Message-ID."""
        clean_domain = domain or "crm.internal"
        if settings.SMTP_FROM_EMAIL and "@" in settings.SMTP_FROM_EMAIL:
            clean_domain = settings.SMTP_FROM_EMAIL.split("@")[1]
        elif settings.SMTP_USER and "@" in settings.SMTP_USER:
            clean_domain = settings.SMTP_USER.split("@")[1]
        return make_msgid(domain=clean_domain)

    @classmethod
    def inject_tracking_elements(
        cls,
        html_content: str,
        tracking_token: str,
        personalized_image_url: Optional[str] = None,
    ) -> str:
        """
        Injects:
        1. A 1x1 transparent tracking pixel at the bottom of the HTML body.
        2. A personalized image banner if requested.
        """
        base_url = settings.TRACKING_BASE_URL.rstrip("/")
        open_pixel_url = f"{base_url}/api/v1/email-tracking/open/{tracking_token}.png"
        pixel_tag = (
            f'<img src="{open_pixel_url}" width="1" height="1" '
            f'alt="" style="display:none !important; width:1px; height:1px; border:0;" />'
        )

        content = html_content or ""

        # If a personalized image URL is provided and not already in HTML, embed it at top
        if personalized_image_url and personalized_image_url not in content:
            img_tag = (
                f'<div style="margin: 12px 0; text-align: center;">'
                f'<img src="{personalized_image_url}" alt="Personalized Graphic" '
                f'style="max-width: 100%; height: auto; border-radius: 8px;" /></div>'
            )
            content = f"{img_tag}\n{content}"

        # Insert tracking pixel before </body> or append at end
        if "</body>" in content.lower():
            pattern = re.compile(r"(</body>)", re.IGNORECASE)
            content = pattern.sub(f"{pixel_tag}\n\\1", content, count=1)
        else:
            content = f"{content}\n{pixel_tag}"

        return content

    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_email: Optional[str] = None,
        tracking_token: Optional[str] = None,
        personalized_image_url: Optional[str] = None,
        custom_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Sends an email via SMTP.
        If SMTP credentials are not configured, runs in safe simulation mode.
        """
        sender = from_email or settings.SMTP_FROM_EMAIL or settings.SMTP_USER or "outreach@crm.internal"
        token = tracking_token or cls.generate_tracking_token()
        message_id = cls.generate_message_id()

        # Inject tracking pixel and personalized image
        tracked_html = cls.inject_tracking_elements(
            html_content=body_html,
            tracking_token=token,
            personalized_image_url=personalized_image_url,
        )
        plain_text = body_text or "Please view this email in an HTML-compatible client."

        if not cls.is_configured():
            logger.info(
                f"[SMTPProvider DEV MODE] Simulated email sent to {to_email} | "
                f"Subject: '{subject}' | Message-ID: {message_id} | Token: {token}"
            )
            return {
                "success": True,
                "mode": "dev_simulation",
                "message": "SMTP not configured. Email logged in simulation mode.",
                "message_id": message_id,
                "tracking_token": token,
                "sender": sender,
                "recipient": to_email,
            }

        try:
            # Build MIME multipart message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = to_email
            msg["Date"] = formatdate(localtime=True)
            msg["Message-ID"] = message_id
            msg["X-Entity-Ref-ID"] = token

            if custom_headers:
                for k, v in custom_headers.items():
                    msg[k] = v

            # Attach plain text and HTML alternatives
            msg.attach(MIMEText(plain_text, "plain", "utf-8"))
            msg.attach(MIMEText(tracked_html, "html", "utf-8"))

            host = settings.SMTP_HOST
            port = settings.SMTP_PORT
            user = settings.SMTP_USER
            password = settings.SMTP_PASSWORD

            if settings.SMTP_USE_SSL or port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(host, port, context=context, timeout=25.0) as server:
                    if user and password:
                        server.login(user, password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(host, port, timeout=25.0) as server:
                    if settings.SMTP_USE_TLS:
                        server.starttls(context=ssl.create_default_context())
                    if user and password:
                        server.login(user, password)
                    server.send_message(msg)

            ProviderHealthService.record_success(cls.provider_name)
            logger.info(f"✅ SMTP email successfully delivered to {to_email} (MsgID: {message_id})")

            return {
                "success": True,
                "mode": "live",
                "message_id": message_id,
                "tracking_token": token,
                "sender": sender,
                "recipient": to_email,
            }

        except Exception as exc:
            err_msg = str(exc)
            logger.error(f"❌ SMTP delivery failed to {to_email}: {err_msg}")
            ProviderHealthService.record_failure(
                cls.provider_name,
                err_msg,
                IntegrationStatus.TEMPORARILY_UNAVAILABLE,
            )
            return {
                "success": False,
                "mode": "live_error",
                "error": err_msg,
                "message_id": message_id,
                "tracking_token": token,
            }
