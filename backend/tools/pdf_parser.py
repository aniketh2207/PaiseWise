import re
import io
import hashlib
import logging
import pdfplumber
from datetime import datetime
from typing import Optional

logging.getLogger("pdfminer").setLevel(logging.ERROR)


def extract_gpay_transactions(file_bytes: bytes) -> list[dict]:
    """
    Parses a Google Pay PDF statement from bytes and extracts all transactions.
    Uses text extraction (not table extraction) since GPay PDFs have no real
    table structure — columns are positioned via text alignment, not lines.

    Returns a list of dicts, one per transaction:
    {
        date, amount, type, upi_name, upi_id,
        upi_transaction_id, raw_description, month, year
    }
    """
    transactions = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")
            i = 0
            while i < len(lines):
                line = lines[i].strip()

                # Each transaction starts with:
                # "DDMon,YYYY Paidto/ReceivedfromNAME ₹AMOUNT"
                txn_match = re.match(
                    r"^(\d{2}\w+,\d{4})\s+((?:Paidto|Receivedfrom).+?)\s+(₹[\d,\.]+)$",
                    line,
                )

                if txn_match:
                    date_str       = txn_match.group(1)    # date
                    direction_name = txn_match.group(2)    # paid to?
                    amount_str     = txn_match.group(3)    # amount

                    # Next line always: "HH:MMAM/PM UPITransactionID:XXXXXXXXXX"
                    upi_txn_id = None
                    time_str = "12:00AM"  # Added default fallback time
                    
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        time_match = re.match(
                            # ADDED: parentheses around the time to create a capture group
                            r"^(\d{2}:\d{2}[AP]M)\s+UPITransactionID:(\d+)$",
                            next_line,
                        )
                        if time_match:
                            time_str = time_match.group(1)       # Extracted time
                            upi_txn_id = time_match.group(2)     # Shifted ID to group 2
                            i += 1  # skip the time/ID line

                    # Direction → type, and extract clean name
                    if direction_name.startswith("Paidto"):
                        txn_type = "debit"
                        raw_name = direction_name[6:]       # strip "Paidto"
                    else:
                        txn_type = "credit"
                        raw_name = direction_name[12:]      # strip "Receivedfrom"

                    # Parse amount (handle commas + decimals: ₹2,350 / ₹19.35)
                    amount = float(amount_str.replace("₹", "").replace(",", ""))

                    try:
                        txn_datetime = datetime.strptime(f"{date_str} {time_str}", "%d%b,%Y %I:%M%p")
                    except ValueError:
                        i += 1
                        continue

                    transactions.append({
                        "date":               txn_datetime.date(),
                        "time":               txn_datetime.time(),
                        "amount":             amount,
                        "type":               txn_type,
                        "upi_name":           raw_name,
                        "upi_id":             None,  # GPay PDF never includes UPI handles
                        "upi_transaction_id": upi_txn_id,
                        "raw_description":    f"{'Paid to' if txn_type == 'debit' else 'Received from'} {raw_name}",
                        "month":              txn_datetime.month,
                        "year":               txn_datetime.year,
                    })

                i += 1

    return transactions


def get_file_hash(file_bytes: bytes) -> str:
    """MD5 hash of file bytes — used to detect duplicate uploads."""
    return hashlib.md5(file_bytes).hexdigest()