# Email Deliverability & Mailbox Operations Guide

**System**: AI Sales, Lead Generation, Outreach & Marketing Operating System  
**Module**: `DeliverabilityService` & Email Infrastructure  
**Version**: 2.0.0  

---

## 1. Deliverability Overview & Objectives

In modern cold outreach and B2B email communication, deliverability is governed by sender reputation, domain authentication, sending volume velocity, and recipient interaction signals. 

This operating system implements an active defense deliverability architecture that:
1. Verifies DNS records (SPF, DKIM, DMARC, MX) using real DNS queries before initiating campaigns.
2. Monitors sending mailbox health and enforces conservative daily warm-up ramps.
3. Automatically pauses campaigns when bounce rates exceed 5.0% or complaint rates exceed 0.1%.
4. Provides an instant, emergency **Global Outbound Kill Switch** to stop all outgoing messages.
5. Guarantees deduplication to prevent embarrassing double-sends to the same lead.

---

## 2. Domain DNS Authentication Engine

The system uses `dnspython` in `DeliverabilityService.verify_domain_dns(domain_name)` to perform live DNS queries against system resolvers.

### Monitored DNS Records

| Record Type | Target Host | Purpose | Required Pattern / Value | Status Values |
|:---|:---|:---|:---|:---|
| **SPF** | `example.com` | Authorizes servers to send email on behalf of domain | TXT record starting with `v=spf1` | `VERIFIED`, `FAILED`, `UNAVAILABLE` |
| **DKIM** | `default._domainkey.example.com` | Cryptographic signature verifying message integrity | TXT record containing `v=DKIM1` or `p=` | `VERIFIED`, `FAILED`, `UNAVAILABLE` |
| **DMARC** | `_dmarc.example.com` | Policy instructs receiving servers how to handle failures | TXT record starting with `v=DMARC1` | `VERIFIED`, `FAILED`, `UNAVAILABLE` |
| **MX** | `example.com` | Directs inbound email to mail server | Valid MX records (e.g. Google Workspace, Outlook) | `VERIFIED`, `FAILED`, `UNAVAILABLE` |

### DNS Verification Logic & Fallback
- `VERIFIED`: The record was queried, found, and matched the required syntax.
- `FAILED`: An answer was returned from the DNS server, but the record was malformed or missing the required tags.
- `UNAVAILABLE`: The DNS server returned `NoAnswer` or `NXDOMAIN`, indicating the record does not exist or DNS could not be resolved.

### API Trigger
To run a live DNS health check for any domain:
```http
POST /api/v1/deliverability/domains/{domain_id}/verify
```

---

## 3. Mailbox Management & Warm-up Architecture

Sending accounts are tracked in the `email_accounts` table. Every account has an associated status:
- `ACTIVE`: Mailbox is fully warmed, authenticated, and authorized to send up to its daily limit.
- `WARMING`: Mailbox is in an automated warm-up progression with lower daily send limits.
- `PAUSED`: Mailbox is manually paused or auto-paused due to health alerts.
- `ERROR`: Mailbox failed authentication or experienced hard provider errors.

### Default Sending Quotas & Velocity Limits

| Stage | Daily Volume Limit | Minimum Delay Between Sends | Recommended Usage |
|:---|:---:|:---:|:---|
| **Week 1 (Warmup)** | 10 emails / day | 120 - 300 seconds | Initial seed testing |
| **Week 2 (Warmup)** | 25 emails / day | 90 - 180 seconds | Low-volume outreach |
| **Week 3+ (Mature)** | 50 emails / day | 60 - 120 seconds | Standard cold prospecting |
| **Production Cap** | **50 emails / day per mailbox** | Distributed across 8 hours | Prevents domain burnout |

> [!IMPORTANT]
> To scale outbound email safely, add multiple sending domains and secondary mailboxes rather than increasing the daily cap of a single inbox above 50 emails/day.

---

## 4. Safety Safeguards & Circuit Breakers

### 4.1. Global Outbound Kill Switch
The Global Outbound Kill Switch is an immediate, system-wide circuit breaker. When active:
- **Zero outbound emails or WhatsApp messages can be sent**.
- The `SequenceEngineService` halts all scheduled steps at Check 1.
- Staged approvals cannot be sent out.

**API Endpoint**:
```http
POST /api/v1/deliverability/kill-switch/toggle
Content-Type: application/json

{
  "active": true,
  "reason": "Sudden bounce spike detected on primary domain"
}
```

### 4.2. Automated Bounce & Spam Auto-Pause
The `DeliverabilityService` continuously evaluates bounce and complaint rates:
$$\text{Bounce Rate} = \frac{\text{Bounced Emails}}{\text{Total Sent Emails}} \times 100$$
$$\text{Complaint Rate} = \frac{\text{Spam Complaints}}{\text{Total Sent Emails}} \times 100$$

- **Bounce Threshold**: If Bounce Rate exceeds **5.0%**, the associated campaign is immediately transitioned to `PAUSED` and an alert is logged in the Centralized Exception Queue.
- **Complaint Threshold**: If Spam Complaint Rate exceeds **0.1%** (1 in 1,000), the mailbox is immediately transitioned to `PAUSED` and an emergency alert is triggered.

### 4.3. Duplicate Send Prevention
Before any message is transmitted, the system generates a deduplication fingerprint:
$$\text{Hash} = \text{SHA256}(\text{recipient\_email} + \text{subject\_line})$$
If an identical hash was recorded in `email_events` within the preceding 24 hours, the send is rejected with error code `DUPLICATE_SEND_BLOCKED`.

---

## 5. Deliverability Checklist for New Domains

Before launching any outreach sequence on a new sending domain, complete this checklist:

1. [ ] **Domain Age**: Ensure domain has been registered for at least 14 days.
2. [ ] **MX Records**: Set up Google Workspace or Microsoft 365 MX records.
3. [ ] **SPF Record**: Add TXT record `v=spf1 include:_spf.google.com ~all`.
4. [ ] **DKIM Key**: Generate 2048-bit DKIM key in workspace admin and add to DNS.
5. [ ] **DMARC Record**: Add TXT record at `_dmarc.domain.com`: `v=DMARC1; p=none; rua=mailto:dmarc@domain.com`.
6. [ ] **System Verification**: Run `POST /api/v1/deliverability/domains/{id}/verify` and confirm all 4 records display `VERIFIED`.
7. [ ] **Warm-up**: Keep daily limit under 20 emails for the first 14 days.
