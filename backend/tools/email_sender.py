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

    # 1. Load from JSON using the built-in method
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # IMPORTANT FOR DEPLOYMENT: InstalledAppFlow.run_local_server opens a local browser
            # for user authentication. This interactive flow WILL FAIL on headless cloud hosts
            # (such as Railway or Render).
            #
            # HOW TO DEPLOY:
            # 1. Run the app or email script LOCALLY once to trigger the interactive consent flow
            #    and generate the `token.json` file on your local machine.
            # 2. Convert the contents of the generated `token.json` into a base64 string.
            # 3. Set that base64 string as the GMAIL_TOKEN_JSON environment variable on the cloud host.
            # 4. Our `token_loader.py` helper will automatically decode and write the token file to
            #    disk on cloud startup, allowing this check to succeed without invoking `run_local_server`.
            flow = InstalledAppFlow.from_client_secrets_file(
                settings.GMAIL_CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)
            
        # 2. Save back to JSON (note: 'w' mode instead of 'wb')
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