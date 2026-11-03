"""Real-time Email Verification & Bounce Prevention Engine (Syntax, DNS MX, Disposable, Role & SMTP check)."""

import re
import socket
import smtplib
from typing import Dict, Any, List, Optional
import dns.resolver

DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "guerrillamail.com", "10minutemail.com",
    "trashmail.com", "yopmail.com", "sharklasers.com", "dispostable.com",
    "getairmail.com", "throwawaymail.com", "temp-mail.org", "fakeinbox.com",
}

FREE_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "icloud.com", "zoho.com", "protonmail.com", "mail.com", "gmx.com",
}

ROLE_PREFIXES = {
    "info", "support", "contact", "sales", "admin", "billing", "help",
    "office", "team", "hello", "inquiry", "enquiry", "service", "care",
}

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)


class EmailVerifierService:
    """Enterprise-grade Email Verification & Deliverability Checker."""

    @classmethod
    def verify_email(cls, email: str, check_smtp: bool = False) -> Dict[str, Any]:
        """
        Verify single email address for syntax, disposable provider, DNS MX records, and SMTP handshake.
        """
        email = (email or "").strip().lower()

        # 1. Syntax Check
        if not email or not EMAIL_REGEX.match(email):
            return {
                "email": email,
                "status": "undeliverable",
                "score": 0,
                "is_valid_format": False,
                "has_mx_records": False,
                "mx_records": [],
                "is_disposable": False,
                "is_free": False,
                "is_role_account": False,
                "reason": "Invalid email syntax format"
            }

        local_part, domain = email.split("@", 1)

        # 2. Disposable domain check
        is_disposable = domain in DISPOSABLE_DOMAINS
        if is_disposable:
            return {
                "email": email,
                "status": "undeliverable",
                "score": 10,
                "is_valid_format": True,
                "has_mx_records": True,
                "mx_records": [],
                "is_disposable": True,
                "is_free": False,
                "is_role_account": False,
                "reason": "Disposable / temporary email domain detected (high bounce risk)"
            }

        is_free = domain in FREE_DOMAINS
        is_role = local_part in ROLE_PREFIXES

        # 3. DNS MX Record Lookup
        has_mx = False
        mx_records = []
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 3.0
            resolver.lifetime = 3.0
            answers = resolver.resolve(domain, "MX")
            mx_records = [r.exchange.to_text().rstrip(".") for r in answers]
            has_mx = len(mx_records) > 0
        except Exception:
            has_mx = False

        if not has_mx:
            return {
                "email": email,
                "status": "undeliverable",
                "score": 15,
                "is_valid_format": True,
                "has_mx_records": False,
                "mx_records": [],
                "is_disposable": False,
                "is_free": is_free,
                "is_role_account": is_role,
                "reason": f"No active DNS MX mail exchange records found for domain '{domain}'"
            }

        # 4. Score Calculation
        score = 80
        if not is_role:
            score += 15  # Direct personal email
        if not is_free:
            score += 5   # Custom corporate/business domain

        status = "deliverable"
        reason = f"Active DNS MX servers verified ({mx_records[0]}). Format is authentic."

        # 5. Optional SMTP Handshake check (if enabled and ISP allows port 25)
        if check_smtp and mx_records:
            try:
                smtp_server = mx_records[0]
                with smtplib.SMTP(smtp_server, 25, timeout=4) as server:
                    server.helo("crm-lead-engine.local")
                    server.mail("verify@crm-lead-engine.local")
                    code, _ = server.rcpt(email)
                    if code == 250:
                        status = "deliverable"
                        score = 100
                        reason = "SMTP mailbox verified and accepted connection"
                    elif code >= 500:
                        status = "undeliverable"
                        score = 20
                        reason = f"Mail server rejected mailbox (Code {code})"
            except Exception:
                # If port 25 blocked by firewall/ISP, keep MX verified status
                pass

        return {
            "email": email,
            "status": status,
            "score": score,
            "is_valid_format": True,
            "has_mx_records": True,
            "mx_records": mx_records[:3],
            "is_disposable": is_disposable,
            "is_free": is_free,
            "is_role_account": is_role,
            "reason": reason,
        }

