# PaiseWise 💸
> A 2-layer agentic personal finance system built for Indian UPI-heavy spending patterns.

Log expenses in real-time via Slack. Reconcile against bank statements monthly. Get a clean Excel report auto-emailed to your parents. Never write a manual expense report again.

---

## How It Works

### Layer 1 — Slack Bot (Primary, Real-time)
DM the PaiseWise bot on Slack with casual natural language the moment you spend:

```
you: 150 auto to BITS gate
bot: ✅ ₹150 → Travel/Auto | 'to BITS gate'

you: 80 canteen lunch
bot: ✅ ₹80 → Food/Canteen | 'canteen lunch'

you: 500 sharad movie split
bot: ✅ ₹500 → Transfer/Split | 'movie split with Sharad'

you: /summary
bot: This month you've spent ₹4,230 across 18 transactions.
     Food is your biggest category at ₹1,800 (43%), mostly canteen
     and Zomato. Your top merchant is Zomato at ₹950. You're spending
     about ₹210/day on average this week.

you: /ask how much did i spend on travel this month?
bot: You spent ₹1,100 on Travel in July — ₹800 on Auto/Cab and
     ₹300 on Bus.
```

### Layer 2 — Bank Statement PDF (Verification, Monthly)
Upload your bank statement PDF at month end. The reconciliation agent:
- Matches bank entries to your Slack logs by amount + date
- Auto-categorizes known business UPIs (Zomato, Swiggy, Amazon, etc.)
- Surfaces unmatched transactions in the Annotation Queue (web UI)
- Learns recurring UPI IDs so the queue shrinks every month

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Gemini 1.5 Flash (Google AI Studio) |
| Agent Framework | LangGraph |
| Slack Bot | Slack Bolt for Python (Socket Mode) |
| Backend | FastAPI |
| Database | PostgreSQL (Neon) |
| ORM | SQLAlchemy |
| PDF Parsing | pdfplumber |
| Excel Generation | openpyxl |
| Email | Gmail API |
| Scheduling | APScheduler |
| Frontend | React (Vite) + Tailwind CSS |

---

## Project Structure

```
paisewise/
├── backend/
│   ├── main.py                       # FastAPI app entry point
│   ├── config.py                     # pydantic-settings config
│   ├── scheduler.py                  # APScheduler monthly report job
│   ├── slack_client.py               # Slack Bolt app (run independently)
│   │
│   ├── database/
│   │   ├── db.py                     # SQLAlchemy engine + session
│   │   ├── models.py                 # ORM models
│   │   └── seed.py                   # Seed default categories
│   │
│   ├── agents/
│   │   ├── parsing_agent.py          # LangGraph: Slack message → slack_log
│   │   ├── ingestion_agent.py        # LangGraph: PDF → bank_transactions
│   │   ├── reconciliation_agent.py   # LangGraph: match logs ↔ bank entries
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
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx         # Charts + stat cards
│   │   │   ├── Transactions.jsx      # Filterable transaction table
│   │   │   ├── Annotate.jsx          # Annotation queue
│   │   │   └── Reports.jsx           # Generate + email reports
│   │   └── components/
│   │       ├── StatCard.jsx
│   │       ├── TransactionRow.jsx
│   │       ├── SourceBadge.jsx
│   │       ├── AnnotateCard.jsx
│   │       ├── DonutChart.jsx
│   │       └── LineChart.jsx
│   ├── package.json
│   └── tailwind.config.js
│
├── reports/                          # Generated Excel files (gitignored)
├── uploads/                          # Temp PDF storage (gitignored)
├── .env                              # All secrets (gitignored)
├── requirements.txt
└── README.md
```

---

## Database Schema

Seven tables:

| Table | Purpose |
|---|---|
| `slack_logs` | Real-time expense logs from Slack bot |
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
- A Slack workspace (free)
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

# Slack
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:password@host/dbname

# Gmail
GMAIL_CREDENTIALS_PATH=./credentials.json
GMAIL_TOKEN_PATH=./token.json
SENDER_EMAIL=your@gmail.com

# App
UPLOADS_DIR=./uploads
REPORTS_DIR=./reports
FRONTEND_ORIGIN=http://localhost:5173

# Scheduler
REPORT_DAY_OF_MONTH=1
REPORT_HOUR=9
```

### 3. Slack App Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → Create New App → From Scratch
2. **Socket Mode** → Enable → Generate App-Level Token with `connections:write` scope → copy as `SLACK_APP_TOKEN`
3. **OAuth & Permissions** → Bot Token Scopes → add:
   - `chat:write`, `im:history`, `im:read`, `im:write`, `reactions:read`
4. **Event Subscriptions** → Enable → Subscribe to bot events:
   - `message.im`, `reaction_added`
5. **Slash Commands** → Create:
   - `/summary` — Get this month's spending summary
   - `/ask` — Ask a question about your spending
6. **Install to Workspace** → copy Bot Token as `SLACK_BOT_TOKEN`

### 4. Initialize the database

```bash
cd backend
python -c "from database.db import init_db; from database.seed import seed_categories; init_db(); seed_categories()"
```

### 5. Run

**Slack Bot** (run this always — logs your expenses):
```bash
python backend/slack_client.py
```

**FastAPI Backend** (run when using the web dashboard):
```bash
uvicorn backend.main:app --reload
```

**Frontend** (run when using the web dashboard):
```bash
cd frontend
npm run dev
```

The Slack bot and backend are independent processes. The bot does not require the backend to be running.

---

## Slack Bot Usage

| Input | What it does |
|---|---|
| `150 auto gate` | Logs ₹150 as Travel/Auto |
| `80 canteen lunch` | Logs ₹80 as Food/Canteen |
| `500 sharad split movie` | Logs ₹500 as Transfer/Split |
| `zomato 450` | Logs ₹450 as Food/Delivery |
| `/summary` | Monthly spending summary for current month |
| `/ask <question>` | Natural language query over your transactions |
| ✏️ reaction | Edit the logged entry |
| 🗑️ reaction | Delete the logged entry |

---

## Build Phases

- [x] **Phase 1** — Slack bot: real-time expense logging, `/summary`, `/ask`, Neon DB
- [ ] **Phase 2** — Bank PDF ingestion + reconciliation agent
- [ ] **Phase 3** — Dashboard + Annotation Queue (React frontend)
- [ ] **Phase 4** — Report agent: Excel generation + Gmail auto-send
- [ ] **Phase 5** — Polish: pattern learning, correction system, budget alerts

---

## Why This Architecture

Indian bank statements for GPay/UPI users are structurally information-poor. A payment to "Suresh M (7890@oksbi)" tells you nothing about why you paid. The Slack bot captures the reason at the moment you actually know it — right when you pay. The bank statement then serves as the objective financial record to verify completeness against.

This is the same pattern used in production fintech apps, implemented here as an agentic system with LangGraph orchestration.

---

## Author

**Aniketh Korkonda Bhattar**
B.E. Electronics & Instrumentation, BITS Pilani
B.S. Data Science, IIT Madras