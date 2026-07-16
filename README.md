# PaiseWise 💸
> A 2-layer agentic personal finance system built for Indian UPI-heavy spending patterns.

Log expenses in real-time via the in-app mobile chat interface. Reconcile against bank statements monthly. Get a clean Excel report auto-emailed to your parents. Never write a manual expense report again.

---

## How It Works

### Layer 1 — Mobile Chat (Primary, Real-time)
Log expenses or query your spending directly inside the mobile app's Chat tab using casual natural language:

```
you: 150 auto to BITS gate
app: ✅ ₹150 → Travel/Auto | 'to BITS gate'

you: 80 canteen lunch
app: ✅ ₹80 → Food/Canteen | 'canteen lunch'

you: 500 sharad movie split
app: ✅ ₹500 → Transfer/Split | 'movie split with Sharad'

you: /summary
app: This month you've spent ₹4,230 across 18 transactions.
     Food is your biggest category at ₹1,800 (43%), mostly canteen
     and Zomato. Your top merchant is Zomato at ₹950. You're spending
     about ₹210/day on average this week.

you: /ask how much did i spend on travel this month?
app: You spent ₹1,100 on Travel in July — ₹800 on Auto/Cab and
     ₹300 on Bus.
```

### Layer 2 — Bank Statement PDF (Verification, Monthly)
Upload your bank statement PDF at month end. The reconciliation agent:
- Matches bank entries to your logged expenses by amount + date
- Auto-categorizes known business UPIs (Zomato, Swiggy, Amazon, etc.)
- Surfaces unmatched transactions in the Annotation Queue (mobile UI)
- Learns recurring UPI IDs so ## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Gemini 1.5 Flash (Google AI Studio) |
| Agent Framework | LangGraph |
| Backend | FastAPI |
| Database | PostgreSQL (Neon) |
| ORM | SQLAlchemy |
| PDF Parsing | pdfplumber |
| Excel Generation | openpyxl |
| Email | Gmail API |
| Scheduling | APScheduler |
| Frontend | Expo / React Native (TypeScript) |

---

## Project Structure

```
paisewise/
├── backend/
│   ├── main.py                       # FastAPI app entry point
│   ├── config.py                     # pydantic-settings config
│   ├── scheduler.py                  # APScheduler monthly report job
│   │
│   ├── database/
│   │   ├── db.py                     # SQLAlchemy engine + session
│   │   ├── models.py                 # ORM models
│   │   └── seed.py                   # Seed default categories
│   │
│   ├── agents/
│   │   ├── parsing_agent.py          # LangGraph: Mobile app message → logged_expense
│   │   ├── ingestion_agent.py        # LangGraph: PDF → bank_transactions
│   │   ├── reconciliation_agent.py   # LangGraph: match chat logs ↔ bank entries
│   │   ├── query_agent.py            # LangGraph: NL → SQL → answer
│   │   └── report_agent.py           # LangGraph: data → Excel → email
│   │
│   ├── tools/
│   │   ├── llm_client.py             # Gemini calls: parsing + extraction + summary
│   │   ├── pdf_parser.py             # pdfplumber: raw rows from PDF
│   │   ├── upi_classifier.py         # Known business UPI dictionary
│   │   ├── db_tools.py               # Query functions as agent tools
│   │   ├── excel_builder.py          # openpyxl: 5-sheet report + charts
│   │   └── email_sender.py           # Gmail API: attach + send
│   │
│   └── routers/
│       ├── upload.py
│       ├── transactions.py
│       ├── annotate.py
│       ├── query.py
│       ├── reports.py
│       ├── dashboard.py
│       └── recipients.py
│
├── frontend/
│   ├── src/
│   │   ├── app/                      # Expo Router App Pages
│   │   │   ├── (tabs)/
│   │   │   │   ├── dashboard.tsx     # Stats, charts & insights
│   │   │   │   ├── queue.tsx         # Annotation queue interface
│   │   │   │   ├── chat.tsx          # Real-time natural language query
│   │   │   │   ├── upload.tsx        # Upload bank statement PDF
│   │   │   │   └── reports.tsx       # Generate parent reports
│   │   │   └── _layout.tsx
│   │   ├── components/               # Custom UI Components
│   │   └── constants/                # Configuration & API endpoints
│   ├── app.json                  # Expo Config
│   ├── eas.json                  # EAS Build profile config
│   ├── package.json
│
├── .env                              # All secrets (gitignored)
├── requirements.txt
└── README.md
```

---

## Database Schema

Seven tables:

| Table | Purpose |
|---|---|
| `slack_logs` | Real-time expense logs from the mobile chat client (uses legacy slack_logs table name) |
| `bank_transactions` | Extracted rows from bank statement PDFs |
| `upi_patterns` | Learned UPI ID → category mappings |
| `categories` | Category + subcategory definitions with budget limits |
| `monthly_summaries` | Cached monthly aggregates + LLM insights |
| `report_recipients` | Email recipients for monthly reports |
| `upload_log` | Tracks processed PDFs (prevents double-processing) |

---

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google AI Studio API key (free tier)
- Neon account (free tier PostgreSQL)
- Gmail account with API enabled

### 1. Clone and install dependencies

```bash
git clone https://github.com/yourusername/paisewise.git
cd paisewise

pip install -r requirements.txt

cd frontend
npm install
```

### 2. Environment variables

Create a `.env` file in the project root:

```env
# LLM
GEMINI_API_KEY=your_gemini_key_here

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:password@host/dbname

# Gmail
GMAIL_CREDENTIALS_PATH=./credentials.json
GMAIL_TOKEN_PATH=./token.json
```

### 3. Initialize the database

```bash
cd backend
python -c "from database.db import init_db; from database.seed import seed_categories; init_db(); seed_categories()"
```

### 4. Run

**FastAPI Backend** (runs the API, routing agent, and parsing pipeline):
```bash
uvicorn backend.main:app --reload
```

**Frontend** (runs the mobile app locally):
```bash
cd frontend
npx expo start
```

---

## In-App Chat Usage

Inside the mobile app's Chat tab, you can use these commands:

| Input | What it does |
|---|---|
| `150 auto gate` | Logs ₹150 as Travel/Auto |
| `80 canteen lunch` | Logs ₹80 as Food/Canteen |
| `500 sharad split movie` | Logs ₹500 as Transfer/Split |
| `zomato 450` | Logs ₹450 as Food/Delivery |
| `/summary` | Get a spending summary for the current month |
| `/ask <question>` | Ask a natural language question about your transactions |

---

## Build Phases

- [x] **Phase 1** — Mobile chat integration: real-time expense logging, spending questions (`/summary`, `/ask`), Neon DB
- [x] **Phase 2** — Bank PDF ingestion + reconciliation agent
- [x] **Phase 3** — Dashboard + Annotation Queue (Expo / React Native mobile app)
- [x] **Phase 4** — Report agent: Excel generation + Gmail auto-send
- [x] **Phase 5** — Polish: pattern learning, correction system, budget alerts

---

## Why This Architecture

Indian bank statements for GPay/UPI users are structurally information-poor. A payment to "Suresh M (7890@oksbi)" tells you nothing about why you paid. The in-app chat interface captures the reason at the moment you actually know it — right when you pay. The bank statement then serves as the objective financial record to verify completeness against.

This is the same pattern used in production fintech apps, implemented here as an agentic system with LangGraph orchestration.

---

## Author

**Aniketh Korkonda Bhattar**
B.E. Electronics & Instrumentation, BITS Pilani
B.S. Data Science, IIT Madras