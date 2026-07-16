import os
import base64
import logging

try:
    from backend.config import settings
except ModuleNotFoundError:
    from config import settings

logger = logging.getLogger("uvicorn")

def load_gmail_token():
    """
    Checks for GMAIL_TOKEN_JSON environment variable. If present,
    decodes the base64-encoded string and writes it to GMAIL_TOKEN_PATH.
    This avoids interactive OAuth authentication on headless cloud servers.
    """
    gmail_token_b64 = os.environ.get("GMAIL_TOKEN_JSON")
    if gmail_token_b64:
        try:
            token_path = settings.GMAIL_TOKEN_PATH
            # Ensure the directory exists
            os.makedirs(os.path.dirname(os.path.abspath(token_path)), exist_ok=True)
            
            # Decode the base64 encoded token
            decoded_bytes = base64.b64decode(gmail_token_b64.strip().encode("utf-8"))
            
            with open(token_path, "wb") as f:
                f.write(decoded_bytes)
            
            logger.info(f"Successfully decoded and wrote Gmail token to: {token_path}")
        except Exception as e:
            logger.error(f"Failed to load Gmail token from GMAIL_TOKEN_JSON environment variable: {e}")
    else:
        logger.info("GMAIL_TOKEN_JSON environment variable not set. Skipping headless token loading.")
