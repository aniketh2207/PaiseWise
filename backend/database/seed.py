# this only runs once at the starting of the development
try:
    from backend.database.db import SessionLocal
    from backend.database.models import Category
except ModuleNotFoundError:
    from database.db import SessionLocal
    from database.models import Category

CATEGORIES = [
    ("Delivery",     "Food",          "#FF6B35"),
    ("Restaurant",   "Food",          "#FF6B35"),
    ("Grocery",      "Food",          "#FF6B35"),
    ("Canteen",      "Food",          "#FF6B35"),
    ("Auto/Cab",     "Travel",        "#4ECDC4"),
    ("Train",        "Travel",        "#4ECDC4"),
    ("Flight",       "Travel",        "#4ECDC4"),
    ("Fuel",         "Travel",        "#4ECDC4"),
    ("Bus",          "Travel",        "#4ECDC4"),
    ("Clothes",      "Shopping",      "#45B7D1"),
    ("Electronics",  "Shopping",      "#45B7D1"),
    ("Stationery",   "Shopping",      "#45B7D1"),
    ("General",      "Shopping",      "#45B7D1"),
    ("Phone",        "Utilities",     "#96CEB4"),
    ("Internet",     "Utilities",     "#96CEB4"),
    ("Electricity",  "Utilities",     "#96CEB4"),
    ("Movies",       "Entertainment", "#FFEAA7"),
    ("OTT",          "Entertainment", "#FFEAA7"),
    ("Games",        "Entertainment", "#FFEAA7"),
    ("Events",       "Entertainment", "#FFEAA7"),
    ("Books",        "Education",     "#DDA0DD"),
    ("Courses",      "Education",     "#DDA0DD"),
    ("Fees",         "Education",     "#DDA0DD"),
    ("Medicine",     "Health",        "#98D8C8"),
    ("Doctor",       "Health",        "#98D8C8"),
    ("Sent",         "Transfer",      "#B0B0B0"),
    ("Received",     "Transfer",      "#B0B0B0"),
    ("Split",        "Transfer",      "#B0B0B0"),
    ("Miscellaneous","Other",         "#D3D3D3"),
]

def seed_categories():
    db = SessionLocal()
    try:
        existing = db.query(Category).count()
        if existing > 0:
            print("Categories already seeded, skipping.")
            return
        for name, parent, color in CATEGORIES:
            db.add(Category(name=name, parent=parent, color_hex=color))
        db.commit()
        print(f"Seeded {len(CATEGORIES)} categories.")
    finally:
        db.close()