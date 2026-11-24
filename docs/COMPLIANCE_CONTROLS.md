# Global Compliance & Privacy Controls Manual

**System**: AI Sales, Lead Generation, Outreach & Marketing Operating System  
**Module**: `ComplianceService`, `ConsentRecord`, and `DataDeletionRequest`  
**Regulations Covered**: GDPR (EU), CAN-SPAM (US), CCPA/CPRA (California), CASL (Canada)  
**Version**: 2.0.0  

---

## 1. Compliance Architecture & Philosophy

Automated outreach and lead generation operating systems carry significant legal and reputational responsibilities. Operating without rigorous consent and privacy safeguards exposes organizations to severe penalties and permanent domain blacklisting.

This system enforces compliance as an **active code-level gate**, not a policy afterthought:
1. Every outreach channel (`EMAIL`, `WHATSAPP`, `PHONE`) requires an active, documented **Lawful Basis**.
2. Leads must pass an automated **Pre-Flight Compliance Check** before being enrolled in any campaign or sequence.
3. Full compliance with **GDPR Article 17 (Right to be Forgotten)** via automated, irreversible anonymization and permanent suppression.
4. Comprehensive audit trails tracking consent history and deletion requests.

---

## 2. Lawful Basis & Consent Tracking

Under GDPR (General Data Protection Regulation), processing personal data for outreach requires an established legal basis. The `consent_records` table tracks:

| Lawful Basis | Legal Criteria | Applicable Channel | Standard Operating Procedure |
|:---|:---|:---|:---|
| **LEGITIMATE_INTERESTS** | B2B outreach where the communication is highly relevant to the recipient's professional role and company. | B2B Email | Lead research must verify professional relevance (ICP score >= 70). Opt-out mechanism must be present in every message. |
| **CONSENT** | Recipient explicitly opted in via web form, demo request, or double-opt-in email. | Email, WhatsApp, Newsletters | Time, IP address, and form URL are logged in `consent_records`. |
| **CONTRACT** | Processing necessary for fulfilling an active contract or service agreement. | Direct Communications | Active customer communication. |

### Recording Consent via API
```http
POST /api/v1/compliance/consent
Content-Type: application/json

{
  "lead_id": "lead_981247",
  "channel": "EMAIL",
  "lawful_basis": "LEGITIMATE_INTERESTS",
  "notes": "Verified B2B VP of Engineering at logistics software company; relevance to AI routing."
}
```

---

## 3. Pre-Flight Compliance Check Engine

Before a lead can be enrolled in a campaign or have an outreach message drafted, `ComplianceService.preflight_check(lead_id, channel)` evaluates eligibility:

```
[Target Lead & Channel]
           |
           v
  +-------------------------------------------------------------+
  | STEP 1: Global Suppression List Evaluation                  |
  | Is lead email or phone in suppression_list?                 |
  | -> If Yes: REJECT (Reason: SUPPRESSED_RECIPIENT)            |
  +-------------------------------------------------------------+
           | Passed
           v
  +-------------------------------------------------------------+
  | STEP 2: Previous Opt-Out / Erasure Evaluation               |
  | Has lead requested deletion under GDPR Art 17?              |
  | -> If Yes: REJECT (Reason: DATA_ERASURE_REQUESTED)          |
  +-------------------------------------------------------------+
           | Passed
           v
  +-------------------------------------------------------------+
  | STEP 3: Lawful Basis Verification                           |
  | Is there a valid ConsentRecord for this channel?            |
  | -> If None: Fallback check if B2B legitimate interest meets  |
  |    strict ICP criteria (Score >= 70 and verified business)   |
  +-------------------------------------------------------------+
           | Passed
           v
[Compliance Verified: Proceed to Campaign/Sequence]
```

---

## 4. GDPR Article 17: Right to be Forgotten (Data Erasure)

When a prospect exercises their Right to be Forgotten (or when requested by an operator), `ComplianceService.process_gdpr_deletion(lead_id, requester_email)` executes an irreversible erasure procedure.

### The 4-Step Erasure Pipeline

```
1. ANONYMIZE LEAD RECORD
   - first_name -> "[ERASED - GDPR ARTICLE 17]"
   - last_name  -> "[ERASED]"
   - phone      -> NULL
   - notes      -> NULL
   - custom_fields -> {}

2. CASCADE TO RELATED RECORDS
   - Contact records -> Anonymized & unlinked
   - Activity logs   -> Stripped of personal identifiable information
   - Unsent approvals-> Deleted from outreach_approvals

3. ADD TO PERMANENT SUPPRESSION LIST
   - Recipient email is hashed and stored in suppression_list
   - reason = "GDPR_DELETION_REQUEST"
   - Guarantees the lead can NEVER be re-scraped, re-imported, or re-contacted

4. LOG AUDIT ENTRY
   - Record created in data_deletion_requests table
   - Timestamps and requesting entity preserved for legal auditing
```

### Triggering Data Erasure via API
```http
POST /api/v1/compliance/gdpr-deletion
Content-Type: application/json

{
  "lead_id": "lead_12345",
  "reason": "Direct user request via email opt-out"
}
```

**Response**:
```json
{
  "status": "COMPLETED",
  "lead_id": "lead_12345",
  "anonymized_fields": ["first_name", "last_name", "phone", "notes"],
  "suppression_added": true,
  "deletion_request_id": "del_87234234"
}
```

---

## 5. Regulatory Compliance Checklist

- **Physical Address Requirement**: Every outbound email template must include the physical mailing address of the sender in the footer (CAN-SPAM).
- **Clear Opt-Out**: Every email must include a functional one-click unsubscribe link or clear instruction *(e.g. "Reply 'stop' to opt out")*.
- **Accurate Headers**: From, To, Reply-To, and routing information must accurately identify the sender. Deceptive headers are strictly prohibited.
- **Respecting Stop Requests**: Unsubscribe requests must be honored immediately (this system processes them instantaneously upon receipt).

