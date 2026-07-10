from backend.database.db import SessionLocal
from backend.database.models import SlackLog
from datetime import date, datetime

db = SessionLocal()

logs = [
    SlackLog(
        slack_message_id = "manual_001",   # unique fake ID
        raw_message      = "353.57 ratnadeep grocery",
        amount           = 353.57,
        category         = "Food",
        subcategory      = "Grocery",
        reason           = "grocery",
        merchant         = "Ratnadeep",
        log_date         = date(2026, 6, 1),   # actual June date
        created_at       = datetime(2026, 6, 1, 10, 15, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_002",   # unique fake ID
        raw_message      = "37 bike",
        amount           = 37.0,
        category         = "Travel",
        subcategory      = "Auto/Cab",
        reason           = "bike",
        merchant         = None,
        log_date         = date(2026, 6, 2),   # actual June date
        created_at       = datetime(2026, 6, 2, 9, 30, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_003",   # unique fake ID
        raw_message      = "92 bike",
        amount           = 92,
        category         = "Travel",
        subcategory      = "Auto/Cab",
        reason           = "bike",
        merchant         = None,
        log_date         = date(2026, 6, 2),   # actual June date
        created_at       = datetime(2026, 6, 2, 14, 45, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_004",   # unique fake ID
        raw_message      = "135 anish maruti",
        amount           = 135,
        category         = "Food",
        subcategory      = "Restaurant",
        reason           = "maruti",
        merchant         = None,
        log_date         = date(2026, 6, 2),   # actual June date
        created_at       = datetime(2026, 6, 2, 21, 15, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_005",   # unique fake ID
        raw_message      = "3000 cycle repair",
        amount           = 3000,
        category         = "Utilities",
        subcategory      = "Repairs",
        reason           = "cycle repair",
        merchant         = None,
        log_date         = date(2026, 6, 3),   # actual June date
        created_at       = datetime(2026, 6, 3, 11, 0, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_006",   # unique fake ID
        raw_message      = "245 karachi food",
        amount           = 245,
        category         = "Food",
        subcategory      = "Restaurant",
        reason           = "karachi",
        merchant         = None,
        log_date         = date(2026, 6, 4),   # actual June date
        created_at       = datetime(2026, 6, 4, 13, 20, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_007",   # unique fake ID
        raw_message      = "1850 racquet",
        amount           = 1850,
        category         = "Miscellaneous",
        subcategory      = "Other",
        reason           = "racquet",
        merchant         = None,
        log_date         = date(2026, 6, 5),   # actual June date
        created_at       = datetime(2026, 6, 5, 10, 5, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_008",   # unique fake ID
        raw_message      = "60 ratnadeep",
        amount           = 60,
        category         = "Food",
        subcategory      = "Grocery",
        reason           = "ratnadeep",
        merchant         = None,
        log_date         = date(2026, 6, 5),   # actual June date
        created_at       = datetime(2026, 6, 5, 19, 40, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_009",   # unique fake ID
        raw_message      = "415 vijetha",
        amount           = 415,
        category         = "Food",
        subcategory      = "Grocery",
        reason           = "vijetha",
        log_date         = date(2026, 6, 6),   # actual June date
        created_at       = datetime(2026, 6, 6, 12, 15, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_010",   # unique fake ID
        raw_message      = "106 bike",
        amount           = 106,
        category         = "Travel",
        subcategory      = "Auto/Cab",
        reason           = "bike",
        merchant         = None,
        log_date         = date(2026, 6, 9),   # actual June date
        created_at       = datetime(2026, 6, 9, 8, 45, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_011",   # unique fake ID
        raw_message      = "220 chat",
        amount           = 220,
        category         = "Food",
        subcategory      = "Restaurant",
        reason           = "chat",
        merchant         = None,
        log_date         = date(2026, 6, 9),   # actual June date
        created_at       = datetime(2026, 6, 9, 13, 10, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_012",   # unique fake ID
        raw_message      = "317 auto`",
        amount           = 317,
        category         = "Travel",
        subcategory      = "Auto/Cab",
        reason           = "bike",
        merchant         = None,
        log_date         = date(2026, 6, 9),   # actual June date
        created_at       = datetime(2026, 6, 9, 20, 30, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_013",   # unique fake ID
        raw_message      = "152 ratnadeep",
        amount           = 152,
        category         = "Food",
        subcategory      = "Grocery",
        reason           = "ratnadeep",
        merchant         = None,
        log_date         = date(2026, 6, 11),   # actual June date
        created_at       = datetime(2026, 6, 11, 9, 15, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_014",   # unique fake ID
        raw_message      = "83 bike",
        amount           = 83,
        category         = "Travel",
        subcategory      = "Auto/Cab",
        reason           = "bike",
        merchant         = None,
        log_date         = date(2026, 6, 11),   # actual June date
        created_at       = datetime(2026, 6, 11, 14, 50, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_015",   # unique fake ID
        raw_message      = "1080 cab",
        amount           = 1080,
        category         = "Travel",
        subcategory      = "Auto/Cab",
        reason           = "cab",
        merchant         = None,
        log_date         = date(2026, 6, 11),   # actual June date
        created_at       = datetime(2026, 6, 11, 22, 10, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_016",   # unique fake ID
        raw_message      = "220 karachi",
        amount           = 220,
        category         = "Food",
        subcategory      = "Restaurant",
        reason           = "karachi",
        merchant         = None,
        log_date         = date(2026, 6, 13),   # actual June date
        created_at       = datetime(2026, 6, 13, 17, 30, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_017",   # unique fake ID
        raw_message      = "160 notebooks",
        amount           = 160,
        category         = "Shopping",
        subcategory      = "Stationery",
        reason           = "notebooks",
        merchant         = None,
        log_date         = date(2026, 6, 19),   # actual June date
        created_at       = datetime(2026, 6, 19, 11, 20, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_018",   # unique fake ID
        raw_message      = "12 bananas",
        amount           = 12,
        category         = "Food",
        subcategory      = "Grocery",
        reason           = "bananas",
        merchant         = None,
        log_date         = date(2026, 6, 19),   # actual June date
        created_at       = datetime(2026, 6, 19, 21, 5, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_019",   # unique fake ID
        raw_message      = "20 chai",
        amount           = 20,
        category         = "Food",
        subcategory      = "Restaurant",
        reason           = "chai",
        merchant         = None,
        log_date         = date(2026, 6, 20),   # actual June date
        created_at       = datetime(2026, 6, 20, 8, 15, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_020",   # unique fake ID
        raw_message      = "59 ratnadeep",
        amount           = 59,
        category         = "Food",
        subcategory      = "Grocery",
        reason           = "ratnadeep",
        merchant         = None,
        log_date         = date(2026, 6, 20),   # actual June date
        created_at       = datetime(2026, 6, 20, 18, 45, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_021",   # unique fake ID
        raw_message      = "61 bike",
        amount           = 61,
        category         = "Travel",
        subcategory      = "Auto/Cab",
        reason           = "bike",
        merchant         = None,
        log_date         = date(2026, 6, 21),   # actual June date
        created_at       = datetime(2026, 6, 21, 7, 30, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_022",   # unique fake ID
        raw_message      = "273 cream stone",
        amount           = 273,
        category         = "Food",
        subcategory      = "Desserts",
        reason           = "cream stone",
        merchant         = None,
        log_date         = date(2026, 6, 21),   # actual June date
        created_at       = datetime(2026, 6, 21, 12, 15, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_023",   # unique fake ID
        raw_message      = "184 waffles",
        amount           = 184,
        category         = "Food",
        subcategory      = "Desserts",
        reason           = "waffles",
        merchant         = None,
        log_date         = date(2026, 6, 21),   # actual June date
        created_at       = datetime(2026, 6, 21, 16, 40, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_024",   # unique fake ID
        raw_message      = "74 bike",
        amount           = 74,
        category         = "Travel",
        subcategory      = "Auto/Cab",
        reason           = "bike",
        merchant         = None,
        log_date         = date(2026, 6, 21),   # actual June date
        created_at       = datetime(2026, 6, 21, 21, 50, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_025",   # unique fake ID
        raw_message      = "299 google play F1 tv",
        amount           = 299,
        category         = "Entertainment",
        subcategory      = "OTT",
        reason           = "F1 tv",
        merchant         = None,
        log_date         = date(2026, 6, 22),   # actual June date
        created_at       = datetime(2026, 6, 22, 10, 10, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_026",   # unique fake ID
        raw_message      = "20 lake",
        amount           = 20,
        category         = "Miscellaneous",
        subcategory      = "Other",
        reason           = "lake",
        merchant         = None,
        log_date         = date(2026, 6, 24),   # actual June date
        created_at       = datetime(2026, 6, 24, 9, 5, 0),
        channel_id       = "manual",
        parse_confidence = 1.0,
    ),
    SlackLog(
        slack_message_id = "manual_027",   # unique fake ID
        raw_message      = "325 ratnadeep",
        amount           = 325,
        category         = "Food",
        subcategory      = "Grocery",
        reason           = "ratnadeep",
        merchant         = None,
        log_date         = date(2026, 6, 24),   # actual June date
        created_at       = datetime(2026, 6, 24, 15, 30, 0),
        channel_id       = "manual",
        parse_confidence = 1
    ),
    SlackLog(
        slack_message_id = "manual_028",   # unique fake ID
        raw_message      = "1000 food split",
        amount           = 1000,
        category         = "Transfer",
        subcategory      = "Split",
        reason           = "food",
        merchant         = None,
        log_date         = date(2026, 6, 24),   # actual June date
        created_at       = datetime(2026, 6, 24, 19, 15, 0),
        channel_id       = "manual",
        parse_confidence = 1
    ),
    SlackLog(
        slack_message_id = "manual_029",   # unique fake ID
        raw_message      = "24 xerox",
        amount           = 24,
        category         = "Shopping",
        subcategory      = "Stationery",
        reason           = "xerox",
        merchant         = None,
        log_date         = date(2026, 6, 25),   # actual June date
        created_at       = datetime(2026, 6, 25, 11, 45, 0),
        channel_id       = "manual",
        parse_confidence = 1
    ),
    SlackLog(
        slack_message_id = "manual_030",   # unique fake ID
        raw_message      = "32 i dont remember",
        amount           = 32,
        category         = "Miscellaneous",
        subcategory      = "Other",
        reason           = "i dont remember",
        merchant         = None,
        log_date         = date(2026, 6, 27),   # actual June date
        created_at       = datetime(2026, 6, 27, 16, 25, 0),
        channel_id       = "manual",
        parse_confidence = 1
    ),
    SlackLog(
        slack_message_id = "manual_031",   # unique fake ID
        raw_message      = "923 dinner",
        amount           = 923,
        category         = "Food",
        subcategory      = "Restaurant",
        reason           = "dinner",
        merchant         = None,
        log_date         = date(2026, 6, 28),   # actual June date
        created_at       = datetime(2026, 6, 28, 20, 35, 0),
        channel_id       = "manual",
        parse_confidence = 1
    ),
    SlackLog(
        slack_message_id = "manual_032",   # unique fake ID
        raw_message      = "117.24 ratnadeep",
        amount           = 117.24,
        category         = "Food",
        subcategory      = "Grocery",
        reason           = "ratnadeep",
        merchant         = None,
        log_date         = date(2026, 6, 30),   # actual June date
        created_at       = datetime(2026, 6, 30, 14, 0, 0),
        channel_id       = "manual",
        parse_confidence = 1
    )
]

# Clear existing manual logs to avoid unique constraint errors
db.query(SlackLog).filter(SlackLog.slack_message_id.like("manual_%")).delete(synchronize_session=False)
db.commit()

db.add_all(logs)
db.commit()
db.close()