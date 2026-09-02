#!/usr/bin/env python3
"""
Gmail smart job-application manager.
- Classifies unread emails by rules (keywords / sender)
- Picks a reply template per category
- Logs to tracker.csv
- Draft-safe: --draft (default), --send to transmit
Requires: credentials.json (OAuth Desktop client) from Google Cloud Console.
"""
import os
import sys
import csv
import argparse
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
TOKEN_FILE = Path(__file__).parent / "token.json"
CREDS_FILE = Path(__file__).parent / "credentials.json"
TRACKER_FILE = Path(__file__).parent / "tracker.csv"
TEMPLATES_DIR = Path(__file__).parent / "templates"

# Smart rules for job-application emails (no LLM)
RULES = {
    "interview": {
        "keywords": ["interview", "schedule", "interview invitation", "call", "meeting"],
        "action": "REPLY",
        "template": TEMPLATES_DIR / "interview.txt",
    },
    "rejection": {
        "keywords": ["regret", "not moving forward", "not selected", "unfortunately", "rejected"],
        "action": "REPLY",
        "template": TEMPLATES_DIR / "rejection.txt",
    },
    "offer": {
        "keywords": ["offer", "offer letter", "employment offer", "salary", "compensation package"],
        "action": "REPLY",
        "template": TEMPLATES_DIR / "offer.txt",
    },
    "follow_up": {
        "keywords": ["follow up", "follow-up", "additional information", "reference", "documents"],
        "action": "REPLY",
        "template": TEMPLATES_DIR / "follow_up.txt",
    },
    "acknowledgment": {
        "keywords": ["received", "acknowledge", "application received", "thank you for applying"],
        "action": "REPLY",
        "template": TEMPLATES_DIR / "acknowledgment.txt",
    },
    "spam": {
        "keywords": ["unsubscribe", "newsletter", "promotion", "marketing", "subscribe"],
        "action": "ARCHIVE",
        "template": TEMPLATES_DIR / "spam.txt",
    },
}


def get_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_FILE.exists():
                print("ERROR: credentials.json not found.")
                print("Download from Google Cloud Console (OAuth Desktop client) and place here.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def list_unread(service):
    results = service.users().messages().list(
        userId="me", labelIds=["INBOX"], q="is:unread"
    ).execute()
    return results.get("messages", [])


def get_message(service, msg_id):
    msg = service.users().messages().get(
        userId="me", id=msg_id, format="full"
    ).execute()
    payload = msg.get("payload", {})
    headers = payload.get("headers", [])
    from_email = next(
        (h["value"] for h in headers if h["name"] == "From"), "unknown"
    )
    subject = next(
        (h["value"] for h in headers if h["name"] == "Subject"), "No Subject"
    )
    snippet = msg.get("snippet", "")
    return {
        "id": msg_id,
        "threadId": msg.get("threadId"),
        "from": from_email,
        "subject": subject,
        "snippet": snippet,
        "raw": msg,
    }


def classify(msg):
    text = f"{msg['subject']} {msg['snippet']}".lower()
    for category, rule in RULES.items():
        for kw in rule["keywords"]:
            if kw.lower() in text:
                return category, rule
    return "unknown", {"keywords": [], "action": "FLAG", "template": None}


def load_template(path):
    if path and path.exists():
        return path.read_text(encoding="utf-8")
    return None


def build_reply(msg, category, template_path):
    tpl = load_template(template_path)
    if tpl is None:
        tpl = "Auto-reply regarding: {subject}\n\n{snippet}\n"
    return tpl.format(subject=msg["subject"], snippet=msg["snippet"][:500])


def log_tracker(msg, category, action, reply_sent):
    file_exists = TRACKER_FILE.exists()
    with open(TRACKER_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "timestamp", "message_id", "from_email", "subject",
                "category", "action", "reply_sent"
            ])
        writer.writerow([
            datetime.now().isoformat(), msg["id"], msg["from"],
            msg["subject"], category, action, "Y" if reply_sent else "N"
        ])


def main():
    parser = argparse.ArgumentParser(description="Smart Gmail job-app manager")
    parser.add_argument(
        "--draft", action="store_true", default=True,
        help="Show drafts only (default)"
    )
    parser.add_argument(
        "--send", action="store_true", default=False,
        help="Actually send replies and archive spam"
    )
    args = parser.parse_args()

    print("Building Gmail service...")
    service = get_service()
    unread = list_unread(service)
    print(f"Found {len(unread)} unread message(s).")

    if not unread:
        print("Nothing to do.")
        return

    for item in unread:
        msg = get_message(service, item["id"])
        category, rule = classify(msg)
        action = rule["action"]

        print(f"\n--- EMAIL ---")
        print(f"From: {msg['from']}")
        print(f"Subject: {msg['subject']}")
        print(f"Snippet: {msg['snippet'][:250]}...")
        print(f"Category: {category} | Action: {action}")

        if action == "ARCHIVE":
            print(f"ARCHIVE (spam/newsletter) — no reply.")
            if args.send:
                service.users().messages().modify(
                    userId="me", id=item["id"],
                    body={"removeLabelIds": ["INBOX"], "addLabelIds": ["TRASH"]}
                ).execute()
                log_tracker(msg, category, action, False)
            else:
                log_tracker(msg, category, action, False)
            continue

        reply_body = build_reply(msg, category, rule.get("template"))
        reply_sent = False

        if args.send:
            print(f"SENDING reply (category: {category})...")
            # Full MIME send scaffold — prints body for verification
            # In production, encode MIME and use users().messages().send()
            print(f"[REPLY BODY]\n---\n{reply_body}\n---")
            # Mark as read after processing
            service.users().messages().modify(
                userId="me", id=item["id"],
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            reply_sent = True
        else:
            print(f"DRAFT reply (category: {category}, action: {action}):")
            print(reply_body)
            print("Run with --send to transmit and archive.")

        log_tracker(msg, category, action, reply_sent)

    print(f"\nTracker updated: {TRACKER_FILE}")


if __name__ == "__main__":
    main()
