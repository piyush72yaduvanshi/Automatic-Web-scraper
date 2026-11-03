# Campaign Management & Sequence Engine Documentation

**System**: AI Sales, Lead Generation, Outreach & Marketing Operating System  
**Module**: `CampaignEngineService`, `SequenceEngineService`, and Campaign Models  
**Version**: 2.0.0  

---

## 1. Executive Overview

Outreach in this operating system is structured around **Outreach Campaigns** and **Followup Sequences**. Unlike naive blasting tools, this engine:
1. Enforces **5 distinct campaign architectures**, each tailored to a specific GTM scenario.
2. Gates lead enrollment behind a strict **Compliance Pre-Flight Check** that validates consent and suppression status.
3. Automatically advances multi-day sequence cadences while enforcing the **7 Mandatory Pre-Execution Checks** before any message is drafted or staged.
4. Requires explicit **human operator approval** before sending any outbound communication.

---

## 2. The 5 Distinct Campaign Types

Every campaign created in the system belongs to one of five archetypes:

```
+---------------------------------------------------------------------------------+
|                               CAMPAIGN TYPES                                    |
+-------------------+-------------------+-------------------+---------------------+
| 1. B2B Prospecting| 2. Newsletters    | 3. Nurture        | 4. Re-engagement   |
| High-touch cold   | Periodic updates  | Educational value | Stalled pipeline   |
| outbound to net-  | to opted-in       | for qualified     | or closed-lost     |
| new ICP leads.    | subscribers.      | pipeline leads.   | recovery.          |
+-------------------+-------------------+-------------------+---------------------+
                    | 5. Inbound Follow-up                                        |
                    | Rapid (<15m) multi-touch response to website demo requests.  |
                    +-------------------------------------------------------------+
```

### 1. B2B Prospecting
- **Target Audience**: Net-new leads discovered via Google Maps, SerpAPI, or website scraping matching the ICP threshold (Score >= 70).
- **Default Cadence**: 4 steps over 14 days (Day 0 intro, Day 3 value proposition, Day 7 customer proof, Day 14 polite breakup).
- **Channel**: Personalized 1-to-1 Email and WhatsApp.
- **Goal**: Discovery call booking or exploratory meeting.

### 2. Newsletters
- **Target Audience**: Consented contacts with lawful basis `CONSENT`.
- **Default Cadence**: Single broadcast or bi-weekly cadence.
- **Channel**: Formatted email with company insights and product updates.
- **Goal**: Brand authority, audience retention, and product adoption.

### 3. Nurture
- **Target Audience**: Leads who expressed interest previously or fit the ICP but aren't currently ready to buy.
- **Default Cadence**: 3 steps over 30 days (Bi-weekly educational articles, industry benchmarks, whitepapers).
- **Channel**: Educational email.
- **Goal**: Keeping brand top-of-mind until the buying window opens.

### 4. Re-engagement
- **Target Audience**: Inactive accounts, lost deals (>90 days old), or cold conversations.
- **Default Cadence**: 2 steps over 7 days (New feature update, special pilot program offer).
- **Channel**: Email and WhatsApp.
- **Goal**: Reactivating dormant leads into active sales pipeline.

### 5. Inbound Follow-up
- **Target Audience**: Inbound demo requests, contact form submissions, or trial signups.
- **Default Cadence**: Immediate (<15m) confirmation, Day 1 follow-up, Day 3 value-add.
- **Channel**: High-priority Email & WhatsApp.
- **Goal**: Converting warm inbound intent into scheduled discovery calls.

---

## 3. Audience Segmentation & Pre-Flight Enrollment

Lead enrollment is managed by `CampaignEngineService.enroll_leads_in_campaign(campaign_id, lead_ids)`.

### Enrollment Validation Pipeline
When a list of leads is submitted for enrollment:
1. **Deduplication Check**: Ensures the lead is not already an active member of this campaign.
2. **Global Suppression Check**: Queries `SuppressionList` by email and domain. If suppressed, enrollment is rejected with status `SUPPRESSED`.
3. **Pre-Flight Compliance Gate**: Calls `ComplianceService.preflight_check(lead_id, channel)`. Validates lawful basis under GDPR/CCPA. If unconsented or invalid, enrollment is blocked with reason `COMPLIANCE_FAILED`.
4. **Member Creation**: Valid leads are inserted into `campaign_members` with initial status `ENROLLED`.

---

## 4. Multi-Step Follow-up Sequences

Campaigns are powered by `FollowupSequence` containing ordered `FollowupStep` entities.

### Default 14-Day Cadence Structure

| Step Number | Delay After Previous | Step Archetype | Focus & Personalization Triggers |
|:---:|:---:|:---|:---|
| **Step 1** | Day 0 (Immediate) | Problem Hook & Relevance | Specific pain point derived from enriched website tech stack and industry. |
| **Step 2** | Day 3 (+72 hours) | Value Proposition & Case Study | Brief 2-sentence case study demonstrating quantifiable ROI in their sector. |
| **Step 3** | Day 7 (+96 hours) | Social Proof & Resource Share | Benchmark report, video teardown, or customer testimonial. |
| **Step 4** | Day 14 (+168 hours) | Polite Breakup & Open Door | Respectful conclusion offering to reconnect whenever the timing is right. |

---

## 5. The 7 Mandatory Pre-Execution Checks

Before any sequence step executes, `SequenceEngineService.evaluate_and_stage_step(sequence_id, step_id)` enforces seven non-negotiable checks:

```
[Sequence Step Scheduled]
           |
           v
  +-------------------------------------------------------------+
  | CHECK 1: Global Outbound Kill Switch Inactive?             |
  | -> If Active: Abort with KILL_SWITCH_ACTIVE                 |
  +-------------------------------------------------------------+
           | Passed
           v
  +-------------------------------------------------------------+
  | CHECK 2: Recipient NOT on Global Suppression List?          |
  | -> If Suppressed: Abort with RECIPIENT_SUPPRESSED           |
  +-------------------------------------------------------------+
           | Passed
           v
  +-------------------------------------------------------------+
  | CHECK 3: Sequence Status is ACTIVE?                         |
  | -> If Paused/Completed: Abort with SEQUENCE_NOT_ACTIVE      |
  +-------------------------------------------------------------+
           | Passed
           v
  +-------------------------------------------------------------+
  | CHECK 4: Zero Inbound Replies Received from Lead?           |
  | -> If Replied: Abort with STOP_CONDITION_REPLIED            |
  +-------------------------------------------------------------+
           | Passed
           v
  +-------------------------------------------------------------+
  | CHECK 5: Sending Mailbox Active & Within Daily Quota?       |
  | -> If Exceeded: Defer with MAILBOX_QUOTA_EXCEEDED           |
  +-------------------------------------------------------------+
           | Passed
           v
  +-------------------------------------------------------------+
  | CHECK 6: Lawful Basis & GDPR Consent Verified?             |
  | -> If Invalid: Abort with COMPLIANCE_FAILED                 |
  +-------------------------------------------------------------+
           | Passed
           v
  +-------------------------------------------------------------+
  | CHECK 7: Step Draft Staged in outreach_approvals Queue?     |
  | -> NEVER SEND DIRECTLY: Stage for human operator review     |
  +-------------------------------------------------------------+
           | Passed
           v
[Stage Approved by Operator -> Transmission]
```

---

## 6. Real Database Campaign Performance Metrics

Campaign metrics are aggregated directly from PostgreSQL database records:

$$\text{Enrollment Count} = \sum \text{campaign\_members}$$
$$\text{Contacted Rate} = \frac{\text{Members with Step 1 Sent}}{\text{Total Enrolled}} \times 100$$
$$\text{Reply Rate} = \frac{\text{Members who Replied}}{\text{Total Contacted}} \times 100$$
$$\text{Bounce Rate} = \frac{\text{Bounced Events}}{\text{Total Emails Sent}} \times 100$$
$$\text{Conversion Rate} = \frac{\text{Deals Created / Meetings Booked}}{\text{Total Contacted}} \times 100$$

All rates update automatically in the Campaigns View in real time.

