"""
AI Sales CRM OS — Official Python SDK.
Zero external dependencies (uses standard library urllib and hmac).
Compatible with Python 3.8 through 3.12+.
"""

import hmac
import hashlib
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional


class AiSalesCrmException(Exception):
    """Custom exception for AI Sales CRM API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class AiSalesCrm:
    """Client for AI Sales CRM OS backend."""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    # 1. Lead Discovery & Maps Engine
    def discover_leads(self, query: str, location: str, limit: int = 10, provider: str = "local_maps") -> Dict[str, Any]:
        return self._post("/api/v1/discovery/search", {
            "query": query,
            "location": location,
            "limit": limit,
            "provider": provider,
        })

    def get_lead(self, lead_id: str) -> Dict[str, Any]:
        return self._get(f"/api/v1/leads/{lead_id}")

    # 2. Lead Ingestion
    def ingest_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/api/v1/webhooks/ingest", lead_data)

    # 3. AI Qualification & Enrichment
    def qualify_lead(self, lead_id: str) -> Dict[str, Any]:
        return self._post(f"/api/v1/leads/{lead_id}/qualify", {})

    def enrich_lead(self, lead_id: str) -> Dict[str, Any]:
        return self._post(f"/api/v1/leads/{lead_id}/enrich", {})

    # 4. Multi-Channel Outreach
    def send_outreach_email(self, lead_id: str, subject: str, body: Optional[str] = None) -> Dict[str, Any]:
        return self._post("/api/v1/outreach/send", {
            "lead_id": lead_id,
            "channel": "EMAIL",
            "subject": subject,
            "body": body,
        })

    # 5. Webhook Management
    def create_webhook_subscription(self, name: str, target_url: str, events: Optional[List[str]] = None, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        return self._post("/api/v1/webhooks/subscriptions", {
            "name": name,
            "target_url": target_url,
            "events": events or ["*"],
            "custom_headers": custom_headers or {},
        })

    def list_webhook_subscriptions(self) -> List[Dict[str, Any]]:
        return self._get("/api/v1/webhooks/subscriptions")

    def delete_webhook_subscription(self, subscription_id: str) -> bool:
        self._delete(f"/api/v1/webhooks/subscriptions/{subscription_id}")
        return True

    def test_webhook_subscription(self, subscription_id: str) -> Dict[str, Any]:
        return self._post(f"/api/v1/webhooks/subscriptions/{subscription_id}/test", {})

    # 6. Cryptographic HMAC Verification
    @staticmethod
    def verify_webhook_signature(raw_payload: bytes, signature_header: str, secret_key: str) -> bool:
        if not signature_header or not secret_key:
            return False
        clean_header = signature_header.replace("sha256=", "").strip()
        expected = hmac.new(secret_key.encode("utf-8"), raw_payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, clean_header)

    # Internal HTTP helper (zero third-party dependencies)
    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "AiSalesCrm-Python-SDK/1.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_text = resp.read().decode("utf-8")
                return json.loads(resp_text) if resp_text else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            try:
                decoded = json.loads(err_body)
            except Exception:
                decoded = {"raw": err_body}
            raise AiSalesCrmException(f"HTTP {e.code} Error: {err_body[:200]}", status_code=e.code, response_body=decoded)
        except urllib.error.URLError as e:
            raise AiSalesCrmException(f"Connection failed: {e.reason}")

    def _get(self, path: str) -> Any:
        return self._request("GET", path)

    def _post(self, path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("POST", path, payload)

    def _delete(self, path: str) -> Any:
        return self._request("DELETE", path)
