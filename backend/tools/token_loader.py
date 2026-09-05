import os
import json
import base64
import logging
from typing import Optional

try:
    from backend.config import settings
except ModuleNotFoundError:
    from config import settings

logger = logging.getLogger("uvicorn")

def parse_gmail_token_env(raw_val: str) -> Optional[dict]:
    """
    Safely parses GMAIL_TOKEN_JSON environment variable, which may be:
    - Base64-encoded string (with potential internal newlines/whitespace from web dashboards like Railway)
    - Raw JSON string
    """
    if not raw_val:
        return None

    # Remove all whitespace, newlines (\n, \r), and tabs
    cleaned = "".join(raw_val.strip().split())
    if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1].strip()

    json_str = None
    if cleaned.startswith("{"):
        json_str = cleaned
    else:
        try:
            missing_padding = len(cleaned) % 4
            if missing_padding:
                cleaned += "=" * (4 - missing_padding)
            decoded_bytes = base64.b64decode(cleaned)
            json_str = decoded_bytes.decode("utf-8")
        except Exception:
            pass

    if not json_str:
        return None

    try:
        data = json.loads(json_str)
        if isinstance(data, dict) and ("token" in data or "refresh_token" in data or "client_id" in data):
            return data
    except Exception:
        pass

    return None

def load_gmail_token():
    """
    Checks for GMAIL_TOKEN_JSON environment variable. If present,
    safely parses it into a valid JSON token dictionary and writes it to GMAIL_TOKEN_PATH.
    This avoids interactive OAuth authentication on headless cloud servers.
    """
    gmail_token_val = os.environ.get("GMAIL_TOKEN_JSON")
    if gmail_token_val:
        try:
            token_path = settings.GMAIL_TOKEN_PATH
            token_info = parse_gmail_token_env(gmail_token_val)

            if token_info:
                os.makedirs(os.path.dirname(os.path.abspath(token_path)), exist_ok=True)
                with open(token_path, "w", encoding="utf-8") as f:
                    json.dump(token_info, f, indent=2)
                logger.info(f"Successfully decoded and wrote valid Gmail token JSON to: {token_path}")
            else:
                logger.error("GMAIL_TOKEN_JSON environment variable is present but could not be parsed into a valid token JSON dictionary.")
        except Exception as e:
            logger.error(f"Failed to load Gmail token from GMAIL_TOKEN_JSON environment variable: {e}")
    else:
        logger.info("GMAIL_TOKEN_JSON environment variable not set. Skipping headless token loading.")

