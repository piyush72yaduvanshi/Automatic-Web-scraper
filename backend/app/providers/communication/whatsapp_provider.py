"""Meta WhatsApp Business Cloud API Provider.

Compliant with Meta WhatsApp Business Platform policies:
- Human approved outbound messages
- Incoming webhook event ingestion
- Opt-out suppression handling (STOP / UNSUBSCRIBE)
- Zero-crash fallback when credentials are not configured
"""

from typing import Dict, Any, List, Optional
import logging
import httpx

from app.core.config import settings
from app.services.provider_health_service import ProviderHealthService, IntegrationStatus

logger = logging.getLogger(__name__)


class WhatsAppProvider:
    """Official Meta WhatsApp Business Cloud API provider."""

    provider_name: str = "whatsapp"

    @classmethod
    def is_configured(cls) -> bool:
        return bool(settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID)

    @classmethod
    async def send_message(
        cls,
        to_phone: str,
        message_body: str,
    ) -> Dict[str, Any]:
        """Send message via WhatsApp Cloud API or simulated development mode."""
        if not cls.is_configured():
            logger.info(f"[WhatsAppProvider DEV MODE] Simulated message to {to_phone}: {message_body[:60]}...")
            return {
                "success": True,
                "mode": "dev_simulation",
                "message": "WhatsApp API is not configured. Logged in development simulation mode.",
                "message_id": f"sim_wa_{to_phone[-4:]}_999",
            }

        phone_id = settings.WHATSAPP_PHONE_NUMBER_ID
        url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        # Clean phone to digits
        clean_phone = "".join(filter(str.isdigit, to_phone))

        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "text",
            "text": {"body": message_body},
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    ProviderHealthService.record_success(cls.provider_name)
                    data = resp.json()
                    wa_id = data.get("messages", [{}])[0].get("id")
                    return {"success": True, "message_id": wa_id}
                elif resp.status_code in [401, 403]:
                    ProviderHealthService.record_failure(cls.provider_name, "Invalid token", IntegrationStatus.INVALID_CREDENTIALS)
                    return {"success": False, "error": "WhatsApp access token invalid or expired"}
                else:
                    ProviderHealthService.record_failure(cls.provider_name, f"HTTP {resp.status_code}")
                    return {"success": False, "error": resp.text}
        except Exception as e:
            logger.error(f"WhatsApp send error: {e}")
            ProviderHealthService.record_failure(cls.provider_name, str(e))
            return {"success": False, "error": str(e)}

    @classmethod
    def process_webhook_payload(cls, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse incoming Meta WhatsApp Cloud API webhook messages."""
        events = []
        try:
            entry = payload.get("entry", [])
            for ent in entry:
                changes = ent.get("changes", [])
                for change in changes:
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    contacts = value.get("contacts", [])
                    contact_map = {c.get("wa_id"): c.get("profile", {}).get("name") for c in contacts}

                    for m in messages:
                        from_number = m.get("from")
                        sender_name = contact_map.get(from_number, "WhatsApp User")
                        msg_text = m.get("text", {}).get("body", "")

                        is_opt_out = msg_text.strip().upper() in ["STOP", "UNSUBSCRIBE", "CANCEL", "OPT OUT", "QUIT"]

                        events.append({
                            "sender_phone": from_number,
                            "sender_name": sender_name,
                            "body": msg_text,
                            "timestamp": m.get("timestamp"),
                            "is_opt_out": is_opt_out,
                            "raw_message_id": m.get("id"),
                        })
        except Exception as e:
            logger.warning(f"Error parsing WhatsApp webhook payload: {e}")
        return events

