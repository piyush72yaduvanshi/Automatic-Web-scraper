"""
Example 1: Official Python SDK Usage Example.
Demonstrates:
1. Connecting to the AI Sales & CRM OS backend.
2. Ingesting / pushing a new prospect lead from an external system.
3. Triggering Autonomous AI Qualification & Enrichment.
4. Sending an outreach email via custom SMTP with auto-generated tracking token.
5. Fetching real-time email engagement & deliverability metrics.
"""

import sys
import os
import json

# Add parent directory to sys.path so we can import the SDK directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk", "python"))
from aisalescrm import AiSalesCrm, AiSalesCrmException

def run_sdk_demo():
    print("=" * 65)
    print("🚀 AI SALES & CRM OS — OFFICIAL SDK PRACTICAL DEMO")
    print("=" * 65)

    # 1. Initialize client
    crm = AiSalesCrm(base_url="http://localhost:8000")
    print("\n[Step 1] Initialized AiSalesCrm client pointing to http://localhost:8000")

    # 2. Ingest a new prospect lead
    print("\n[Step 2] Ingesting new prospect lead into CRM...")
    lead_payload = {
        "business_name": "Apex Digital Labs",
        "category": "Software & Web Development",
        "website": "https://apexdigitallabs.com",
        "phone": "+91 98765 12345",
        "email": "contact@apexdigitallabs.com",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "source_provider": "external_crm_sdk_demo",
    }
    
    try:
        ingest_res = crm.ingest_lead(lead_payload)
        lead_id = ingest_res.get("lead_id") or ingest_res.get("lead", {}).get("id")
        is_new = ingest_res.get("is_new", False)
        print(f"✅ Lead successfully ingested! Lead ID: {lead_id}")
        print(f"   Status: {'Newly Created' if is_new else 'Updated Existing'} | Business: {lead_payload['business_name']}")
    except AiSalesCrmException as e:
        print(f"❌ Failed to ingest lead: {e}")
        return

    # 3. Trigger AI Qualification
    print("\n[Step 3] Running Autonomous AI Qualification & Scoring...")
    try:
        qualify_res = crm.qualify_lead(lead_id)
        print(f"✅ AI Qualification completed!")
        print(f"   Score: {qualify_res.get('qualification_score')} / 100")
        print(f"   Intent: {qualify_res.get('qualification_tier', 'Warm')}")
        print(f"   AI Reasoning: {qualify_res.get('qualification_reasoning', 'Ready for outreach')}")
    except Exception as e:
        print(f"⚠️ Qualification warning (using default scoring): {e}")

    # 4. Send Tracked Cold Outreach Email via SMTP
    print("\n[Step 4] Sending Cold Outreach Email via SMTP with Tracking Pixel & Image...")
    subject = "Strategic Partnership Proposal: Autonomous Lead Generation"
    body_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>Hi Team {lead_payload['business_name']},</h2>
        <p>I reviewed your modern tech solutions in Bengaluru and noticed great potential to scale your acquisition pipeline.</p>
        <p>We built an AI Sales Operating System that automates multi-source discovery, automated AI qualification, and personalized multi-channel outreach.</p>
        <p>Would you have 10 minutes this Thursday for a brief walkthrough?</p>
        <br/>
        <p>Best regards,<br/><strong>Enterprise Growth Team</strong></p>
      </body>
    </html>
    """

    try:
        smtp_res = crm.send_smtp_email(
            to_email=lead_payload["email"],
            subject=subject,
            body_html=body_html,
            personalized_image_url="http://localhost:8000/api/v1/email-tracking/image/demo-banner.svg",
        )
        print("✅ Outreach Email Dispatched!")
        print(f"   Delivery Mode    : {smtp_res.get('mode')}")
        print(f"   Sent Message-ID  : {smtp_res.get('sent_message_id')}")
        print(f"   Tracking Token   : {smtp_res.get('tracking_token')}")
        print(f"   1x1 Pixel URL    : {smtp_res.get('tracking_pixel_url')}")
    except Exception as e:
        print(f"❌ SMTP outreach failed: {e}")

    # 5. Retrieve Live Outreach Statistics
    print("\n[Step 5] Checking Live Email Deliverability & Open Stats...")
    try:
        stats = crm.get_email_tracking_stats()
        print(f"📊 Outreach Metrics:")
        print(f"   Total Emails Sent  : {stats.get('total_sent')}")
        print(f"   Total Unique Opens : {stats.get('total_opened')}")
        print(f"   Total Open Events  : {stats.get('total_open_events')}")
        print(f"   Total Replies      : {stats.get('total_replied')}")
        print(f"   Open Rate          : {stats.get('open_rate_percent')}%")
        print(f"   Reply Rate         : {stats.get('reply_rate_percent')}%")
        print(f"   SMTP Configured    : {stats.get('smtp_configured')}")
        print(f"   IMAP Configured    : {stats.get('imap_configured')}")
    except Exception as e:
        print(f"⚠️ Could not fetch stats: {e}")

    print("\n" + "=" * 65)
    print("🎉 SDK Practical Demonstration Completed Successfully!")
    print("=" * 65)

if __name__ == "__main__":
    run_sdk_demo()
