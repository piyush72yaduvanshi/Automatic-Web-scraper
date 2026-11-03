# KPI Definitions & Metric Formulas Manual

**System**: AI Sales, Lead Generation, Outreach & Marketing Operating System  
**Module**: `ReportingService`, `AnalyticsService`, and Data Warehousing  
**Core Principle**: ZERO Fabricated Metrics — 100% Derived from Real Database Queries  
**Version**: 2.0.0  

---

## 1. Overview & Data Integrity Principle

In an autonomous sales and outreach operating system, business decisions depend on accurate data. Many automation platforms display mock metrics or fabricated open rates that mask underlying deliverability failures.

In this operating system:
1. **Zero Fabricated Metrics**: All metrics are computed dynamically using SQLAlchemy 2.0 aggregate queries against the primary relational database.
2. **Deterministic Formulas**: Every KPI has a precise mathematical formula and a corresponding SQL query definition.
3. **Snapshot Archiving**: Historical performance is preserved in `report_snapshots` (Daily, Weekly, Monthly) to enable trend analysis.

---

## 2. Lead Discovery & Research KPIs

### 1. ICP Pass Rate
The percentage of discovered leads that meet or exceed the qualification threshold (Default: ICP Score $\ge 70$).
$$\text{ICP Pass Rate} = \left( \frac{\text{Count of Leads with ICP Score} \ge 70}{\text{Total Leads Scored}} \right) \times 100$$
```sql
SELECT 
  ROUND((COUNT(*) FILTER (WHERE icp_score >= 70)::float / NULLIF(COUNT(*), 0)) * 100, 2) AS icp_pass_rate
FROM leads 
WHERE icp_score IS NOT NULL;
```

### 2. Contact Enrichment Rate
The percentage of discovered leads successfully enriched with a verified corporate email and verified phone number.
$$\text{Enrichment Rate} = \left( \frac{\text{Leads with Email and Phone}}{\text{Total Scanned Leads}} \right) \times 100$$
```sql
SELECT 
  ROUND((COUNT(*) FILTER (WHERE email IS NOT NULL AND phone IS NOT NULL)::float / NULLIF(COUNT(*), 0)) * 100, 2) AS enrichment_rate
FROM leads;
```

---

## 3. Email Deliverability & Mailbox Health KPIs

### 3. Bounce Rate
The proportion of outbound emails rejected by recipient mail servers (hard or soft bounce).
$$\text{Bounce Rate} = \left( \frac{\text{Email Events where event\_type = 'BOUNCE'}}{\text{Total Emails Sent}} \right) \times 100$$
```sql
SELECT 
  ROUND((COUNT(*) FILTER (WHERE event_type = 'BOUNCE')::float / NULLIF(COUNT(*) FILTER (WHERE event_type = 'SENT'), 0)) * 100, 2) AS bounce_rate
FROM email_events;
```
> [!WARNING]
> If Bounce Rate exceeds **5.0%**, the `DeliverabilityService` automatically triggers an alert and pauses the offending campaign.

### 4. Spam Complaint Rate
The proportion of recipients who flagged the email as spam.
$$\text{Complaint Rate} = \left( \frac{\text{Email Events where event\_type = 'COMPLAINT'}}{\text{Total Emails Sent}} \right) \times 100$$
> [!CAUTION]
> If Complaint Rate exceeds **0.1%** (1 in 1,000), sending mailboxes are paused immediately to prevent domain reputation death.

### 5. Mailbox Quota Utilization
The percentage of the daily sending limit consumed across all active mailboxes.
$$\text{Quota Utilization} = \left( \frac{\sum \text{emails\_sent\_today}}{\sum \text{daily\_limit}} \right) \times 100$$
```sql
SELECT 
  ROUND((SUM(sent_today)::float / NULLIF(SUM(daily_limit), 0)) * 100, 2) AS quota_utilization
FROM email_accounts 
WHERE status = 'ACTIVE';
```

---

## 4. Outreach, Sequence & Conversion KPIs

### 6. Sequence Reply Rate
The percentage of contacted leads who replied to any step within a sequence.
$$\text{Reply Rate} = \left( \frac{\text{Sequences with status = 'REPLIED'}}{\text{Total Sequences Activated}} \right) \times 100$$
```sql
SELECT 
  ROUND((COUNT(*) FILTER (WHERE status = 'REPLIED')::float / NULLIF(COUNT(*), 0)) * 100, 2) AS reply_rate
FROM followup_sequences;
```

### 7. Positive Sentiment (Interest) Rate
The proportion of inbound replies classified as expressing positive commercial intent (`INTERESTED` or `MEETING_REQUESTED`).
$$\text{Positive Sentiment Rate} = \left( \frac{\text{Inbound Messages where intent } \in (\text{'INTERESTED'}, \text{'MEETING\_REQUESTED'})}{\text{Total Inbound Replies}} \right) \times 100$$
```sql
SELECT 
  ROUND((COUNT(*) FILTER (WHERE intent_category IN ('INTERESTED', 'MEETING_REQUESTED'))::float / NULLIF(COUNT(*), 0)) * 100, 2) AS positive_sentiment_rate
FROM conversation_messages 
WHERE direction = 'INBOUND';
```

### 8. Opportunity Conversion Rate
The ratio of contacted leads that successfully resulted in a qualified deal created in the sales pipeline.
$$\text{Conversion Rate} = \left( \frac{\text{Deals Created}}{\text{Leads Contacted in Outbound Campaigns}} \right) \times 100$$

---

## 5. Sales Pipeline & Deal Velocity KPIs

### 9. Total Active Pipeline Value
The gross currency value of all open deals across all active pipeline stages.
$$\text{Pipeline Value} = \sum \text{deal.value} \quad \forall \quad \text{stage} \notin (\text{'WON'}, \text{'LOST'})$$
```sql
SELECT 
  COALESCE(SUM(value), 0.0) AS active_pipeline_value
FROM deals 
WHERE stage NOT IN ('WON', 'LOST');
```

### 10. Win Rate
The percentage of closed deals that converted into paying customers (`WON`).
$$\text{Win Rate} = \left( \frac{\text{Deals Won}}{\text{Deals Won} + \text{Deals Lost}} \right) \times 100$$
```sql
SELECT 
  ROUND((COUNT(*) FILTER (WHERE stage = 'WON')::float / 
  NULLIF(COUNT(*) FILTER (WHERE stage IN ('WON', 'LOST')), 0)) * 100, 2) AS win_rate
FROM deals;
```

---

## 6. Automation & Agent Telemetry KPIs

### 11. Workflow Success Rate
The proportion of workflow executions that ran to completion without unhandled exceptions.
$$\text{Workflow Success Rate} = \left( \frac{\text{Executions with status = 'COMPLETED'}}{\text{Total Executions}} \right) \times 100$$
```sql
SELECT 
  ROUND((COUNT(*) FILTER (WHERE status = 'COMPLETED')::float / NULLIF(COUNT(*), 0)) * 100, 2) AS workflow_success_rate
FROM workflow_executions;
```

### 12. Human Approval Rate
The percentage of AI-generated outreach drafts accepted by the human operator without outright rejection.
$$\text{Approval Rate} = \left( \frac{\text{Approvals with status } \in (\text{'APPROVED'}, \text{'MODIFIED'})}{\text{Total Approvals Reviewed}} \right) \times 100$$
