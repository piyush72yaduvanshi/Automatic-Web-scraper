"""Gmail / Google Workspace OAuth and Messaging Provider.

Implements compliant email sending and thread synchronization.
When credentials are not configured, runs safely in dev/demo mode without crashing.
"""

from typing import Dict, Any, List, Optional
import logging
import httpx

from app.core.config import settings
from app.services.provider_health_service import ProviderHealthService, IntegrationStatus

logger = logging.getLogger(__name__)


class GmailProvider:
    """Official Gmail API provider with safe mock/dev fallback."""

    provider_name: str = "gmail"

    @classmethod
    def is_configured(cls) -> bool:
        return bool(settings.GMAIL_CLIENT_ID and (settings.GMAIL_REFRESH_TOKEN or settings.GMAIL_CLIENT_SECRET))

    @classmethod
    async def send_email(
        cls,
        to_email: str,
        subject: str,
        body_content: str,
        sender_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an email via Gmail API or safe development logger.
        Human approval must be granted before calling this method.
        """
        if not cls.is_configured():
            logger.info(f"[GmailProvider DEV MODE] Simulated email sent to {to_email} | Subject: {subject}")
            return {
                "success": True,
                "mode": "dev_simulation",
                "message": "Gmail OAuth is not configured. Email logged in simulation mode.",
                "message_id": f"sim_{to_email.split('@')[0]}_123",
            }

        # If refresh token is present, get access token from Google OAuth
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                token_resp = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": settings.GMAIL_CLIENT_ID,
                        "client_secret": settings.GMAIL_CLIENT_SECRET,
                        "refresh_token": settings.GMAIL_REFRESH_TOKEN,
                        "grant_type": "refresh_token",
                    },
                )
                if token_resp.status_code != 200:
                    ProviderHealthService.record_failure(cls.provider_name, "OAuth token refresh failed", IntegrationStatus.EXPIRED)
                    return {"success": False, "error": "Google OAuth token expired or invalid"}

                access_token = token_resp.json().get("access_token")

                # Send message via Gmail REST API
                import base64
                from email.mime.text import MIMEText

                message = MIMEText(body_content)
                message["to"] = to_email
                message["from"] = sender_email or settings.GMAIL_SENDER_EMAIL or "me"
                message["subject"] = subject
                raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

                send_resp = await client.post(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={"raw": raw},
                )

                if send_resp.status_code == 200:
                    ProviderHealthService.record_success(cls.provider_name)
                    return {"success": True, "message_id": send_resp.json().get("id")}
                else:
                    ProviderHealthService.record_failure(cls.provider_name, f"HTTP {send_resp.status_code}")
                    return {"success": False, "error": send_resp.text}

        except Exception as e:
            logger.error(f"Gmail send exception: {e}")
            ProviderHealthService.record_failure(cls.provider_name, str(e))
            return {"success": False, "error": str(e)}
