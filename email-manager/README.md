# email-manager

Standalone Gmail auto-read + reply tool.

## What I need from you

1. **Gmail API credentials** (`credentials.json`):
   - Go to [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials → Create OAuth 2.0 Client ID (Desktop app) → Download JSON.
   - Rename to `credentials.json` and place in this folder.

2. **Enable Gmail API**:
   - In Google Cloud Console → APIs & Services → Enabled APIs → Enable "Gmail API".

3. **First run authorization**:
   - `python email_manager.py` will open a browser to authorize Gmail access. It creates `token.json` locally.

4. **Reply templates** (`templates/reply.txt`):
   - Edit the template file. The tool inserts the original subject/body context.

## Best-practice defaults

- **Draft mode (`--draft`)** is the default. Replies are printed to console but NOT sent.
- **Send mode (`--send`)** requires the explicit flag. Never run `--send` without reviewing output first.
- Reads **unread** messages from INBOX only (avoids spam/archive noise).
- Template-based replies (not AI-generated) to prevent unintended messages.

## Setup

```powershell
pip install -r requirements.txt
# Place your Google credentials.json here
python email_manager.py --draft
```

After first auth, run with send (only after reviewing drafts):

```powershell
python email_manager.py --send
```
