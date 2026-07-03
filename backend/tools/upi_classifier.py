# tools/upi_classifier.py

from typing import Optional
from sqlalchemy.orm import Session
from database.models import UpiPattern

BUSINESS_KEYWORDS = {
    "FOOD":         ("Food", "Restaurant"),
    "BAKERY":       ("Food", "Restaurant"),
    "RESTAURANT":   ("Food", "Restaurant"),
    "CAFE":         ("Food", "Restaurant"),
    "SWEETS":       ("Food", "Restaurant"),
    "SUPERMARKET":  ("Food", "Grocery"),
    "SUPER MARKET": ("Food", "Grocery"),
    "MARKETS":      ("Food", "Grocery"),
    "GROCERY":      ("Food", "Grocery"),
    "MART":         ("Food", "Grocery"),
    "RATNADEEP":    ("Food", "Grocery"),    
    "METRO":        ("Travel", "Train"),
    "RAILWAY":      ("Travel", "Train"),
    "IRCTC":        ("Travel", "Train"),
    "RAPIDO":       ("Travel", "Auto/Cab"),
    "OLA":          ("Travel", "Auto/Cab"),
    "UBER":         ("Travel", "Auto/Cab"),
    "PETROL":       ("Travel", "Fuel"),
    "FUEL":         ("Travel", "Fuel"),
    "AMAZON":       ("Shopping", "General"),
    "FLIPKART":     ("Shopping", "General"),
    "MYNTRA":       ("Shopping", "Clothes"),
    "GOOGLE PLAY":  ("Entertainment", "Apps"),
    "NETFLIX":      ("Entertainment", "OTT"),
    "SPOTIFY":      ("Entertainment", "OTT"),
    "HOTSTAR":      ("Entertainment", "OTT"),
    "BOOKMYSHOW":   ("Entertainment", "Movies"),
    "AIRTEL":       ("Utilities", "Phone"),
    "JIOMART":      ("Utilities", "Phone"),
    "INNOVIK":      ("Education", "Courses"),  
}

def classify_upi(upi_name: str, db: Session) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Returns (is_business, category, subcategory).
    Accepts an active DB session to prevent connection pooling limits.
    """
    name_upper = upi_name.upper()

    # Priority 1: Check pattern memory
    # Using upi_id since that is the actual unique identifier in models.py
    pattern = db.query(UpiPattern).filter(
        UpiPattern.upi_id == upi_name,
        UpiPattern.user_confirmed == True
    ).first()
    
    if pattern:
        return True, pattern.learned_category, pattern.learned_subcategory

    # Priority 2: Keyword scan
    sorted_keywords = sorted(
        BUSINESS_KEYWORDS.keys(),
        key=len,
        reverse=True
    )
    
    for keyword in sorted_keywords:
        if keyword in name_upper:
            category, subcategory = BUSINESS_KEYWORDS[keyword]
            return True, category, subcategory

    # Priority 3: Unknown -> falls back to LLM or annotation queue
    return False, None, None