"""
Example 2: Enterprise Webhook Receiver & HMAC-SHA256 Verification Server.
Demonstrates:
1. Starting a local HTTP Webhook receiver (e.g., in your external CRM, PHP app, or microservice).
2. Constant-time cryptographic HMAC-SHA256 signature verification (Timing attack resistant).
3. Parsing real-time events (`lead.discovered`, `email.opened`, `email.replied`).
4. Registering a test subscription with the backend and running a live test ping.
"""

import sys
import os
import json
import hmac
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

# Shared secret key configured between AI Sales CRM OS and your external CRM
SHARED_WEBHOOK_SECRET = "demo_webhook_secret_key_123456789"

class WebhookReceiverHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)

        # 1. Extract signature and metadata headers
        sig_header = self.headers.get("X-CRM-Signature", "")
        event_name = self.headers.get("X-CRM-Event", "unknown")
        delivery_id = self.headers.get("X-CRM-Delivery-Id", "unknown")

        print("\n" + "=" * 65)
        print(f"📥 [WEBHOOK INCOMING] Received Event: '{event_name}' (Delivery ID: {delivery_id})")
        print("=" * 65)

        # 2. Cryptographic HMAC-SHA256 Verification
        clean_sig = sig_header.replace("sha256=", "").strip()
        expected_sig = hmac.new(
            SHARED_WEBHOOK_SECRET.encode("utf-8"),
            raw_body,
            hashlib.sha256
        ).hexdigest()

        is_valid = hmac.compare_digest(expected_sig, clean_sig)

        if not is_valid:
            print("❌ SIGNATURE VERIFICATION FAILED: Rejecting forged or unauthorized webhook.")
            print(f"   Received Sig: {clean_sig}")
            print(f"   Expected Sig: {expected_sig}")
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Unauthorized signature"}).encode("utf-8"))
            return

        print("🔒 SIGNATURE VERIFICATION PASSED: Authentic payload from AI Sales CRM OS.")

        # 3. Parse JSON Body
        try:
            payload = json.loads(raw_body.decode("utf-8"))
            print("📦 Event Data:")
            print(json.dumps(payload, indent=2))
        except Exception as e:
            print(f"⚠️ Failed to parse JSON: {e}")

        # 4. Respond with 200 OK Fast
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "acknowledged"}).encode("utf-8"))
        print("✅ Acknowledged 200 OK back to dispatcher.")
        print("=" * 65 + "\n")

    def log_message(self, format, *args):
        # Suppress default server logs for cleaner demonstration output
        return


def start_demo_server(port: int = 9876):
    server = HTTPServer(("0.0.0.0", port), WebhookReceiverHandler)
    print(f"📡 Webhook Receiver Server listening on http://127.0.0.1:{port}/webhook")
    server.serve_forever()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Webhook Demonstration Server")
    parser.add_argument("--port", type=int, default=9876, help="Port to listen on (default 9876)")
    args = parser.parse_args()

    print("=" * 65)
    print("🚀 AI SALES & CRM OS — WEBHOOK RECEIVER PRACTICAL EXAMPLE")
    print(f"Shared Secret: {SHARED_WEBHOOK_SECRET}")
    print("=" * 65)

    start_demo_server(args.port)
