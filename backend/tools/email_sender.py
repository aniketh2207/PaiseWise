import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle

try:
    from backend.config import settings
except ModuleNotFoundError:
    from config import settings

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def _get_gmail_service():
    creds = None
    token_path = settings.GMAIL_TOKEN_PATH

    # 1. Load from GMAIL_TOKEN_JSON env var if available
    if getattr(settings, "GMAIL_TOKEN_JSON", None):
        import json
        try:
            token_info = json.loads(settings.GMAIL_TOKEN_JSON)
            creds = Credentials.from_authorized_user_info(token_info, SCOPES)
        except Exception as e:
            print(f"Failed to parse GMAIL_TOKEN_JSON env var: {e}")

    # 2. Fall back to JSON file on disk
    if not creds and os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Failed to refresh Gmail OAuth token ({e}). Invalidating stale token.")
                if os.path.exists(token_path):
                    try:
                        os.remove(token_path)
                    except Exception:
                        pass
                creds = None

        if not creds:
            if not os.path.exists(settings.GMAIL_CREDENTIALS_PATH):
                raise RuntimeError(
                    f"Gmail credentials file not found at '{settings.GMAIL_CREDENTIALS_PATH}'. "
                    "Your OAuth token has expired/revoked. Please re-authenticate locally to generate a new token.json "
                    "or set GMAIL_TOKEN_JSON in environment variables."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                settings.GMAIL_CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save back to JSON
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)

def send_report_email(
    recipient_emails: list[str],
    subject: str,
    body_text: str,
    excel_bytes: bytes,
    filename: str,
):
    service = _get_gmail_service()

    message = MIMEMultipart()
    message["to"] = ", ".join(recipient_emails)
    message["subject"] = subject

    message.attach(MIMEText(body_text, "plain"))

    attachment = MIMEApplication(excel_bytes, _subtype="xlsx")
    attachment.add_header(
        "Content-Disposition", "attachment", filename=filename
    )
    message.attach(attachment)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()