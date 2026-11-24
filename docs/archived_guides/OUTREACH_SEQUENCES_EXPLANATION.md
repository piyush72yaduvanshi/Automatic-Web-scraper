# 📧 Follow-Up & Cadence Sequences - Complete Explanation

**Date:** November 12, 2026  
**System:** B2B Prospecting Outreach Automation

---

## 🎯 What Is This System?

Yeh ek **AUTOMATED EMAIL SEQUENCE** system hai jo qualified leads ko automatically follow-up emails bhejta hai.

**Purpose:**
- Cold outreach automation
- Multi-touch nurture campaigns
- Systematic follow-up without manual work

**Example:**
```
Lead qualified hota hai
    ↓
Automatic sequence start hota hai
    ↓
Day 0: Intro email
Day 3: Value proposition
Day 7: Case study
Day 14: Breakup email
    ↓
Reply aata hai? → Stop sequence
No reply? → Continue until Day 14
```

---

## 📝 B2B_PROSPECTING Sequence

Yeh ek **4-Touch, 14-Day Cadence** hai specifically B2B prospecting ke liye:

### Step 1: Day 0 (Initial Contact)
**Subject:** Quick question regarding inbound operations for {{company_name}}

**Purpose:** Introduction aur interest generate karna

**Content Template:**
```
Hi [First Name],

I noticed [company_name] is growing in [industry]. 

Quick question: Are you currently facing challenges with 
inbound lead management or booking operations?

We help similar businesses reduce response time by 60%.

Worth a 15-min call?

Best,
[Your Name]
```

**Status:** ⏸️ **Staged to Approval Queue**

---

### Step 2: Day +3 (Value Follow-Up)
**Subject:** Idea for {{company_name}} — reducing inbound booking bottlenecks

**Purpose:** Value proposition aur solution highlight karna

**Content Template:**
```
Hi [First Name],

Following up on my previous email about [company_name].

I had an idea: Most businesses in [industry] lose 30% of 
inbound leads due to slow response times.

We built a solution that:
• Responds to inquiries in under 2 minutes
• Qualifies leads automatically
• Books meetings 24/7

Interested in seeing a quick demo?

Best,
[Your Name]
```

**Status:** ⏸️ **Staged to Approval Queue**

---

### Step 3: Day +7 (Social Proof)
**Subject:** How similar businesses scaled pipeline without ad spend

**Purpose:** Case studies aur credibility establish karna

**Content Template:**
```
Hi [First Name],

Wanted to share a quick win:

[Similar Company] in [industry] increased their pipeline by 
3x in 90 days using our automated lead response system.

They were struggling with:
• Slow response times
• Manual qualification
• Lost opportunities

Now they:
✓ Respond instantly to every inquiry
✓ Qualify 100% of leads automatically
✓ Convert 2.5x more prospects

Worth exploring for [company_name]?

Best,
[Your Name]
```

**Status:** ⏸️ **Staged to Approval Queue**

---

### Step 4: Day +14 (Breakup Email)
**Subject:** Closing the loop — {{company_name}}

**Purpose:** Last attempt aur graceful exit

**Content Template:**
```
Hi [First Name],

I've reached out a few times about helping [company_name] 
improve inbound lead response.

I understand timing might not be right, so I'll close the 
loop here.

If things change in the future, feel free to reach out.

Best of luck!
[Your Name]

P.S. If you know anyone else who might benefit, I'd 
appreciate the introduction.
```

**Status:** ⏸️ **Staged to Approval Queue**

---

## 🛡️ 7 Mandatory Safety Checks

Har email send hone se **PEHLE** yeh 7 checks automatically run hote hain:

### 1. ✅ Eligibility Check
**What It Checks:**
- Lead qualified hai ya nahi?
- Email address valid hai?
- Lead status = "Active"?
- Sequence already completed toh nahi?

**Why It Matters:**
- Unqualified leads ko email nahi jaana chahiye
- Invalid emails = bounce rate badh jata hai
- Completed sequences repeat nahi hone chahiye

**Pass Condition:** Lead must be qualified and active

---

### 2. ✅ Suppression Check
**What It Checks:**
- Email global suppression list mein hai ya nahi?
- Previously unsubscribed?
- Bounced emails?
- Complained as spam?

**Why It Matters:**
- Legal compliance (CAN-SPAM Act)
- Reputation protection
- Avoid spam complaints

**Pass Condition:** Email NOT in suppression list

---

### 3. ✅ Reply Pause Check
**What It Checks:**
- Lead ne reply kiya hai ya nahi?
- Last reply kab aaya?
- Conversation active hai?

**Why It Matters:**
- Agar lead ne reply kiya hai, toh automated emails annoying hote hain
- Manual follow-up better hai engaged prospects ke liye
- Customer experience maintain karna

**Pass Condition:** No recent reply (last 7 days)

**If Reply Detected:**
```
Automatic sequence → PAUSED
Manual follow-up → REQUIRED
Sales rep → NOTIFIED
```

---

### 4. ✅ Campaign Active Check
**What It Checks:**
- Sequence paused toh nahi?
- Campaign enabled hai?
- Schedule within active hours?

**Why It Matters:**
- Paused sequences nahi chalane chahiye
- Business hours respect karna
- Campaign lifecycle management

**Pass Condition:** Campaign status = "ACTIVE"

---

### 5. ✅ Human Approval Check ⚠️
**What It Checks:**
- Email approved hai ya nahi?
- Approval queue mein pending?
- Manual review completed?

**Why It Matters:**
- **Content review before sending**
- Typo/error prevention
- Legal compliance verification
- Brand voice consistency

**Pass Condition:** Email status = "APPROVED"

**Current Status:**
```
❌ FAILING - All emails in approval queue
⏸️ Emails staged but NOT SENT
🚨 Manual approval REQUIRED
```

---

### 6. ✅ Kill Switch Check
**What It Checks:**
- Global kill switch OFF hai?
- Emergency stop activated?
- System-wide pause?

**Why It Matters:**
- Emergency situations (deliverability issues, spam reports)
- Quick stop for all outreach
- System maintenance

**Pass Condition:** Kill switch = OFF

**How to Activate:**
```
Emergency situations only:
- Spam complaint surge
- Deliverability issues
- System maintenance
- Legal/compliance issue
```

---

### 7. ✅ Anti-Duplicate Check
**What It Checks:**
- Same email recently sent?
- Within 24-hour window?
- Duplicate sequence enrollment?

**Why It Matters:**
- Same email 2 baar bhejne se annoying lagta hai
- Professional image maintain karna
- Avoid spam filters

**Pass Condition:** No duplicate send in last 24 hours

---

## ⚠️ Current Problem

### Issue: ALL EMAILS STAGED BUT NOT SENT

**What's Happening:**
```
Step 1 → ⏸️ Staged to Approval Queue
Step 2 → ⏸️ Staged to Approval Queue
Step 3 → ⏸️ Staged to Approval Queue
Step 4 → ⏸️ Staged to Approval Queue
```

**Root Cause:** Check #5 (Human Approval) FAILING

**Reason:**
- Emails generated hain ✓
- Safety checks (1-4, 6-7) pass hain ✓
- BUT... Manual approval pending ❌
- System waiting for human review

**Is This a Bug?**
❌ **NO! This is a SAFETY FEATURE!**

**Why Is This Good?**
- Prevents automated spam
- Content review before sending
- Legal compliance
- Brand protection

---

## 💡 Solutions

### Option 1: APPROVE EMAILS MANUALLY (RECOMMENDED)

**Best for:** Production, real outreach

**Steps:**
1. Open approval queue page:
   ```
   http://localhost:5173/outreach
   ```

2. Navigate to "Approval Queue" section

3. Review each pending email:
   - Check recipient
   - Read email content
   - Verify personalization ({{company_name}} filled?)
   - Check for typos/errors

4. Click "Approve" button for each email

5. System automatically sends approved emails at scheduled time

**Benefits:**
- ✅ Full control
- ✅ Review before sending
- ✅ Error prevention
- ✅ Legal compliance
- ✅ Professional quality

**Drawbacks:**
- Manual work required
- Time consuming for large campaigns

---

### Option 2: AUTO-APPROVE (Skip Review)

**Best for:** Testing, trusted templates only

**⚠️ HIGH RISK - Use with caution!**

**How to Enable:**

**Method 1: Database Setting**
```sql
-- Enable auto-approval for sequence
UPDATE followup_sequences 
SET auto_approve = true 
WHERE name = 'B2B_PROSPECTING';

-- Or globally
UPDATE campaign_settings 
SET require_approval = false 
WHERE campaign_id = 'your-campaign-id';
```

**Method 2: Environment Variable**
```env
# In .env file
OUTREACH_AUTO_APPROVE=true
SKIP_HUMAN_REVIEW=true  # DANGEROUS!
```

**Method 3: UI Setting**
```
Settings → Outreach → Approval Settings → 
☑ Auto-approve sequence emails
```

**⚠️ RISKS:**
- ❌ No review before sending
- ❌ Typos automatically sent
- ❌ Personalization errors not caught
- ❌ Potential spam complaints
- ❌ Legal liability
- ❌ Reputation damage

**When to Use:**
- Internal testing only
- Trusted, proven templates
- Low-volume campaigns
- Non-critical outreach

**Never Use For:**
- Cold outreach to prospects
- High-value opportunities
- Untested templates
- Large-scale campaigns

---

### Option 3: TEST MODE (Recommended for Learning)

**Best for:** Testing system, learning flow

**Steps:**

1. **Keep approval system enabled** ✓

2. **Create test campaign with fake emails:**
```sql
INSERT INTO business_leads (
  company_name, 
  email, 
  status
) VALUES (
  'Test Company ABC',
  'test@yourdomain.com',  -- Your own email
  'qualified'
);
```

3. **Trigger sequence:**
```
Go to: Outreach → Sequences
Select: B2B_PROSPECTING
Click: "Add Lead to Sequence"
Choose: Test Company ABC
```

4. **Review approval queue:**
```
Go to: Outreach → Approval Queue
See: 4 pending emails
Review: Content with your test data
```

5. **Approve and test:**
```
Click: "Approve All"
Wait: Emails sent to your test address
Verify: Content, timing, personalization
```

**Benefits:**
- ✅ Safe testing
- ✅ No risk to real prospects
- ✅ Verify system working
- ✅ Learn approval workflow
- ✅ Test email content

---

## 🎯 How It's Supposed to Work

### Ideal Flow (After Approval)

```
Day 0 (Today):
  09:00 AM → Lead qualified
  09:05 AM → Sequence enrolled
  09:10 AM → Step 1 scheduled
  02:00 PM → Email staged to approval queue
  02:30 PM → 👤 HUMAN REVIEWS & APPROVES
  03:00 PM → ✉️ EMAIL SENT

Day 3:
  03:00 PM → Step 2 auto-staged
  03:15 PM → 👤 HUMAN APPROVES
  03:30 PM → ✉️ EMAIL SENT

Day 7:
  03:00 PM → Step 3 auto-staged
  03:15 PM → 👤 HUMAN APPROVES
  03:30 PM → ✉️ EMAIL SENT

Day 14:
  03:00 PM → Step 4 auto-staged
  03:15 PM → 👤 HUMAN APPROVES
  03:30 PM → ✉️ EMAIL SENT
  
  OR
  
  Prospect replied on Day 5?
  → Sequence AUTO-PAUSED
  → Manual follow-up required
```

### If Auto-Approve Enabled (Risky!)

```
Day 0:
  09:00 AM → Lead qualified
  09:05 AM → Sequence enrolled
  09:10 AM → Step 1 scheduled
  02:00 PM → Email staged
  02:00 PM → ⚠️ AUTO-APPROVED (no review!)
  03:00 PM → ✉️ EMAIL SENT (potentially with errors)

Day 3, 7, 14: Same automatic flow
```

---

## 📊 Database Tables Involved

### 1. `followup_sequences`
```sql
SELECT * FROM followup_sequences WHERE name = 'B2B_PROSPECTING';

Columns:
- id
- name: "B2B_PROSPECTING"
- description: "4-touch cadence"
- is_active: true
- auto_approve: false  ← KEY SETTING!
- created_at
```

### 2. `sequence_steps`
```sql
SELECT * FROM sequence_steps WHERE sequence_id = 'B2B_PROSPECTING_id';

4 rows:
- step_order: 1, delay_days: 0, template: "Intro"
- step_order: 2, delay_days: 3, template: "Value"
- step_order: 3, delay_days: 7, template: "Case Study"
- step_order: 4, delay_days: 14, template: "Breakup"
```

### 3. `sequence_enrollments`
```sql
-- Leads enrolled in sequence
SELECT * FROM sequence_enrollments WHERE sequence_id = 'B2B_id';

Columns:
- lead_id
- sequence_id
- current_step: 1
- status: "ACTIVE"
- enrolled_at
- paused_reason: null
```

### 4. `outreach_queue`
```sql
-- Pending emails waiting for approval
SELECT * FROM outreach_queue WHERE status = 'PENDING_APPROVAL';

Columns:
- id
- lead_id
- sequence_step_id
- subject: "Quick question regarding..."
- body: "Hi {{first_name}}..."
- scheduled_for: "2026-11-12 15:00:00"
- status: "PENDING_APPROVAL"  ← Stuck here!
- approved_by: null
- approved_at: null
```

---

## 🎉 Conclusion

### Is System Working?

**YES! ✅ System is working PERFECTLY!**

**What's Working:**
- ✅ Sequence creation
- ✅ Step scheduling
- ✅ Email generation
- ✅ Personalization
- ✅ Safety checks (7/7 implemented)
- ✅ Approval queue

**What's "Not Working":**
- ❌ Emails not sending
- **Reason:** Manual approval required (by design!)
- **This is CORRECT behavior**

### What You Need to Do

**For Testing:**
```
1. Go to: http://localhost:5173/outreach
2. Find: Approval Queue section
3. Review: 4 pending emails
4. Click: "Approve" for each
5. Wait: Emails will be sent at scheduled time
```

**For Production:**
```
1. Keep approval system enabled
2. Assign team member to review queue daily
3. Approve qualified emails
4. Reject/edit problematic ones
5. Monitor deliverability and responses
```

**Never Do This (Unless Testing):**
```sql
-- DON'T enable auto-approve in production!
UPDATE followup_sequences SET auto_approve = true;
```

---

## 📚 Related Documentation

- Sequence Configuration: Database table `followup_sequences`
- Approval Queue: UI at `/outreach`
- Safety Checks: Code at `app/services/outreach/safety_checks.py`
- Email Templates: Database table `email_templates`

---

**System Status:** ✅ **WORKING AS DESIGNED**  
**Action Required:** Manual approval for production safety  
**Emails Pending:** 4 (all staged, waiting for review)

---

**Last Updated:** November 12, 2026  
**System:** B2B Prospecting Outreach Automation v1.0
