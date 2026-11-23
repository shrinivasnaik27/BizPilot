# 🚀 BizPilot AI
### Intelligent Multi-Agent Business Automation Platform

> **One Instruction. Complete Business Execution.**

BizPilot AI transforms a single natural-language business instruction into a fully coordinated, multi-step business workflow — researching prospects, analyzing opportunities, generating personalized marketing content, managing approvals, and producing actionable business intelligence reports.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Problem Statement](#-problem-statement)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Installation Guide](#-installation-guide)
- [Environment Configuration](#-environment-configuration)
- [Running the Application](#-running-the-application)
- [Docker Deployment](#-docker-deployment)
- [API Documentation](#-api-documentation)
- [Example Workflow](#-example-workflow)
- [Human Approval System](#-human-approval-system)
- [Testing](#-testing)
- [Demo Mode](#-demo-mode)
- [Security](#-security)
- [Known Limitations](#-known-limitations)
- [Future Enhancements](#-future-enhancements)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔭 Overview

BizPilot AI is an end-to-end business automation platform powered by six specialized AI agents, coordinated by a central LangGraph orchestrator. Business owners provide one natural-language instruction, and the platform handles everything — from lead research to personalized outreach — with mandatory human approval before any external action.

---

## 🎯 Problem Statement

Modern businesses waste hundreds of hours on repetitive tasks:
- Manual prospect research across multiple sources
- Individually scoring and ranking leads
- Writing personalized outreach emails from scratch
- Updating CRM records manually
- Generating performance reports

BizPilot AI automates this entire pipeline while keeping humans in control of critical decisions.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🤖 **Multi-Agent Orchestration** | 6 specialized agents coordinated by LangGraph |
| 🔍 **Automated Research** | Finds and profiles business prospects automatically |
| 📊 **Lead Scoring** | Transparent 100-point scoring system |
| ✉️ **Personalized Marketing** | AI-generated email drafts tailored to each prospect |
| 👥 **CRM Integration** | Full CRUD with duplicate prevention |
| ✅ **Human Approval** | Mandatory review before any external action |
| 📈 **Business Reports** | Comprehensive analytics with CSV export |
| 🔬 **Demo Mode** | Fully functional without paid API credentials |
| 🐳 **Docker Ready** | One-command containerized deployment |
| 🔒 **Security First** | JWT auth, backend approval enforcement, audit logs |

---

## 🏗 Architecture

### Six-Agent Pipeline

```mermaid
flowchart TD
    U([👤 User]) -->|Natural Language Instruction| O[🧠 AI Orchestrator\nLangGraph]
    O -->|Research task| R[🔍 Research Agent\nFind Prospects]
    R -->|Structured prospects| A[📊 Analysis Agent\nScore & Rank]
    A -->|Scored prospects| M[✉️ Marketing Agent\nGenerate Drafts]
    M -->|Email drafts| C[👥 CRM Agent\nSave to Database]
    C -->|Draft IDs| AP[✅ Approval Agent\nCreate Requests]
    AP -->|PAUSED| H([👤 Human Review])
    H -->|Approve / Reject| AP
    AP -->|Resume| RP[📈 Reporting Agent\nGenerate Report]
    RP -->|Final Report| U

    style O fill:#6366f1,color:#fff
    style H fill:#fd7e14,color:#fff
    style AP fill:#198754,color:#fff
```

### System Architecture

```mermaid
flowchart LR
    subgraph Frontend
        ST[Streamlit Dashboard]
    end
    subgraph Backend
        FA[FastAPI REST API]
        ORC[LangGraph Orchestrator]
        subgraph Agents
            RA[Research]
            AA[Analysis]
            MA[Marketing]
            CA[CRM]
            APR[Approval]
            REP[Reporting]
        end
    end
    subgraph Data
        DB[(SQLite / PostgreSQL)]
    end
    subgraph External
        GROQ[Groq LLM API]
        SMTP[SMTP Email]
    end

    ST <-->|REST API| FA
    FA --> ORC
    ORC --> RA --> AA --> MA --> CA --> APR --> REP
    FA <--> DB
    ORC <--> GROQ
    APR --> SMTP
```

---

## 🛠 Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **AI Orchestration** | LangGraph, LangChain |
| **LLM** | Groq API (llama-3.3-70b-versatile) |
| **Frontend** | Streamlit, Plotly |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **ORM** | SQLAlchemy 2.0 |
| **Auth** | JWT (python-jose), bcrypt |
| **Email** | aiosmtplib (SMTP) |
| **Testing** | Pytest, FastAPI TestClient |
| **Containers** | Docker, Docker Compose |

---

## 📁 Project Structure

```
BizPilot/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application entry point
│   │   ├── config.py                # Pydantic Settings configuration
│   │   ├── database.py              # SQLAlchemy engine & session
│   │   ├── agents/                  # Six specialized AI agents
│   │   │   ├── research_agent.py
│   │   │   ├── analysis_agent.py
│   │   │   ├── marketing_agent.py
│   │   │   ├── crm_agent.py
│   │   │   ├── approval_agent.py
│   │   │   └── reporting_agent.py
│   │   ├── graph/                   # LangGraph orchestration
│   │   │   ├── state.py             # Shared workflow state
│   │   │   ├── nodes.py             # Graph node implementations
│   │   │   └── workflow.py          # Graph definition & orchestrator
│   │   ├── api/routes/              # FastAPI route handlers
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   └── services/                # Auth & email services
│   ├── tests/
│   │   └── test_main.py             # Comprehensive test suite
│   └── requirements.txt
├── frontend/
│   ├── app.py                       # Streamlit dashboard (9 pages)
│   ├── services/api_client.py       # Backend API client
│   └── components/ui.py             # Reusable UI components
├── scripts/
│   ├── init_db.py                   # Database initialization
│   └── seed_demo_data.py            # Demo data seeder
├── .env.example                     # Environment variable template
├── docker-compose.yml
├── Dockerfile
├── Dockerfile.frontend
└── pytest.ini
```

---

## ⚡ Quick Start

```powershell
# 1. Clone the repo
git clone https://github.com/shrinivasnaik27/BizPilot.git
cd BizPilot

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r backend\requirements.txt
pip install -r requirements.txt

# 4. Configure environment
Copy-Item .env.example .env
# Edit .env (see configuration section below)

# 5. Initialize database
python scripts\init_db.py

# 6. Seed demo data (optional)
python scripts\seed_demo_data.py

# 7. Start backend
uvicorn backend.app.main:app --reload --port 8000

# 8. Start frontend (new terminal)
streamlit run frontend\app.py
```

**Demo login:** `demo@bizpilot.ai` / `demo1234`

---

## 📦 Installation Guide

### Prerequisites

- Python 3.12+
- PostgreSQL 14+ (optional — SQLite works out of the box)
- Git

### Step 1 — Clone Repository

```powershell
git clone https://github.com/shrinivasnaik27/BizPilot.git
cd BizPilot
```

### Step 2 — Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3 — Install Dependencies

```powershell
# Backend
pip install -r backend\requirements.txt

# Frontend
pip install -r requirements.txt
```

### Step 4 — Configure Environment

```powershell
Copy-Item .env.example .env
notepad .env
```

---

## ⚙️ Environment Configuration

Edit `.env` with your values:

```env
# App
APP_NAME=BizPilot AI
APP_ENV=development
SECRET_KEY=your-super-secret-key-change-this-in-production

# Database (SQLite for dev, PostgreSQL for prod)
DATABASE_URL=sqlite:///./bizpilot.db
# DATABASE_URL=postgresql://bizpilot:password@localhost:5432/bizpilot_db

# Groq LLM (get free key at console.groq.com)
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=llama-3.3-70b-versatile

# Research Provider
RESEARCH_PROVIDER=mock   # Use 'mock' for demo, configure real provider for production

# Email (optional – leave empty for demo mode)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_USE_TLS=true

# Demo mode (auto-detects if GROQ_API_KEY is not set)
DEMO_MODE=true
```

### Getting a Groq API Key

1. Visit [console.groq.com](https://console.groq.com)
2. Create a free account
3. Generate an API key
4. Set `GROQ_API_KEY=your-key` in `.env`
5. Set `DEMO_MODE=false`

---

## 🚀 Running the Application

### Backend (PowerShell)

```powershell
# Activate venv first
.\venv\Scripts\Activate.ps1

# Initialize database
python scripts\init_db.py

# (Optional) seed demo data
python scripts\seed_demo_data.py

# Start API server
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

API available at: http://localhost:8000  
Swagger docs at: http://localhost:8000/docs

### Frontend (new PowerShell window)

```powershell
.\venv\Scripts\Activate.ps1
streamlit run frontend\app.py
```

Dashboard available at: http://localhost:8501

---

## 🐳 Docker Deployment

```powershell
# Copy and configure environment
Copy-Item .env.example .env
# Edit .env as needed

# Build and start all services
docker-compose up --build

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

Services:
- **PostgreSQL**: `localhost:5432`
- **Backend API**: `localhost:8000`
- **Frontend**: `localhost:8501`

---

## 📖 API Documentation

Full interactive API docs available at **http://localhost:8000/docs** (Swagger UI).

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Create account |
| `POST` | `/api/auth/login` | Sign in, get JWT |
| `GET` | `/api/auth/me` | Current user |
| `POST` | `/api/workflows` | Start new workflow |
| `GET` | `/api/workflows` | List all workflows |
| `GET` | `/api/workflows/{id}` | Get workflow status |
| `POST` | `/api/workflows/{id}/resume` | Resume paused workflow |
| `GET` | `/api/prospects` | List prospects (with search/filter) |
| `POST` | `/api/prospects` | Add prospect manually |
| `GET` | `/api/approvals` | List approvals |
| `POST` | `/api/approvals/{id}/approve` | Approve an action |
| `POST` | `/api/approvals/{id}/reject` | Reject an action |
| `POST` | `/api/approvals/{id}/send` | Send approved email |
| `GET` | `/api/reports` | List reports |
| `GET` | `/api/reports/{id}/export/csv` | Download CSV report |

---

## 💡 Example Workflow

**User Instruction:**
```
Find 10 healthcare startups in Bengaluru that need AI automation. 
Research their business, evaluate potential, generate personalized 
marketing emails, save to CRM, and produce a final report.
```

**What happens automatically:**

1. **Research Agent** finds 10 companies matching the criteria
2. **Analysis Agent** scores each on a 100-point scale (industry fit, business need, etc.)
3. **Marketing Agent** generates personalized email drafts for qualified leads (score ≥ 40)
4. **CRM Agent** saves all prospects and drafts to the database
5. **Approval Agent** creates pending approval requests — **workflow PAUSES**
6. **User reviews** each email draft in the Approval Center (approve/edit/reject)
7. After approvals, workflow **resumes** automatically
8. **Reporting Agent** generates a comprehensive business intelligence report

**Sample output:**
```json
{
  "total_prospects": 10,
  "high_priority": 3,
  "medium_priority": 5,
  "low_priority": 2,
  "drafts_generated": 8,
  "pending_approvals": 8,
  "recommendations": [
    "Focus immediate outreach on 3 HIGH priority prospects",
    "Review and approve 8 pending email drafts in Approval Center",
    "Nurture 5 MEDIUM priority prospects with follow-up content"
  ]
}
```

---

## 🔐 Human Approval System

BizPilot AI implements a **mandatory human-in-the-loop** control system.

### How It Works

1. Marketing drafts are generated but **never sent automatically**
2. The Approval Agent creates a `PENDING` approval for each email
3. The workflow **pauses** at `AWAITING_APPROVAL`
4. Users review each email in the Approval Center:
   - Preview the full email content
   - Edit subject or body if needed
   - Approve or Reject
5. After approval, emails can be sent via the **Send** button

### Security Guarantees

- ✅ **Backend enforcement**: The API independently verifies approval status before sending — hiding the Send button is not sufficient
- ✅ **Content hash check**: If email content changes after approval, re-approval is required
- ✅ **Audit log**: Every approval/rejection is timestamped with the reviewer's identity
- ✅ **Demo mode**: No emails are sent in demo mode under any circumstances
- ✅ **Status tracking**: `PENDING → APPROVED → EXECUTED` or `REJECTED`

---

## 🧪 Testing

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Run all tests
pytest -v

# Run specific test class
pytest backend/tests/test_main.py::TestApprovals -v

# Run with coverage
pytest --cov=backend/app --cov-report=term-missing
```

### Test Coverage

| Category | Tests |
|----------|-------|
| API Health | Root, health endpoint, docs |
| Authentication | Register, login, duplicate prevention, JWT |
| Business Profile | Create, read, update |
| Prospects | CRUD, duplicate prevention, search |
| Workflows | Create, list, cancel, instruction validation |
| Approvals | Approve, reject, double-approve prevention |
| Email Security | Backend blocks unapproved sends |
| Agents | Status, demo mode operation |
| Demo Mode | Research & analysis agents in mock mode |

---

## 🔬 Demo Mode

BizPilot AI runs fully in **Demo Mode** when no paid API credentials are configured.

| Feature | Demo Mode |
|---------|-----------|
| Research | ✅ Mock prospects (clearly labeled `[DEMO]`) |
| Analysis | ✅ Rule-based scoring |
| Marketing | ✅ Template-based email drafts |
| CRM | ✅ Full database operations |
| Approvals | ✅ Full approval workflow |
| Email Send | 🔬 Simulated (not actually sent) |
| Reports | ✅ Full report generation |

Demo mode is activated automatically when `GROQ_API_KEY` is not set or equals the placeholder value.

---

## 🔒 Security

- **JWT Authentication**: All API endpoints require a valid token
- **User isolation**: Users can only access their own data
- **Secret management**: All credentials via environment variables only
- **Input validation**: Pydantic validates all request bodies
- **SQL injection prevention**: SQLAlchemy ORM with parameterized queries
- **Approval enforcement**: Backend verifies approval before sending emails
- **Content hashing**: SHA-256 hash ensures content integrity after approval
- **Logging**: Sensitive values (API keys, passwords) masked in logs
- **No credential exposure**: API keys never returned in API responses

---

## ⚠️ Known Limitations

1. **Research**: LLM-based research may not find all companies or may have outdated info. Demo mode uses fixed mock data.
2. **Email sending**: Requires valid SMTP credentials. Demo mode simulates sending.
3. **Concurrency**: Background workflows use FastAPI BackgroundTasks — not suitable for high-scale production without a proper task queue (Celery/RQ).
4. **LangGraph checkpointing**: Persistent workflow checkpoints require additional setup with a database-backed checkpointer.
5. **Rate limiting**: Basic protection included; production deployments should add API gateway rate limiting.
6. **File uploads**: PDF report export requires additional configuration.

---

## 🔮 Future Enhancements

- [ ] Real-time WebSocket updates for workflow progress
- [ ] LinkedIn/Crunchbase research integration
- [ ] Multi-user team collaboration
- [ ] Email tracking (opens, clicks)
- [ ] Celery task queue for scalable background jobs
- [ ] LangGraph persistent checkpointing with Redis
- [ ] Mobile-responsive PWA frontend
- [ ] Webhook integrations (Zapier, n8n)
- [ ] Advanced analytics with custom dashboards
- [ ] AI-powered reply handling

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

Please ensure tests pass: `pytest -v`

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 📦 GitHub Upload Commands

```powershell
cd "c:\Users\Shrinivas Naik\OneDrive\Desktop\BizPilot"
git init
git add .
git commit -m "Initial commit: BizPilot AI v1.0.0"
git branch -M main
git remote add origin https://github.com/shrinivasnaik27/BizPilot.git
git push -u origin main
```

---

<div align="center">
  <strong>BizPilot AI</strong> — Built with LangGraph, FastAPI, and Streamlit<br>
  <em>One Instruction. Complete Business Execution.</em>
</div>
#   B i z P i l o t  
 