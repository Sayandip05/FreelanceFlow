# FreelanceFlow

**AI-powered freelance marketplace connecting clients with skilled freelancers**

[![Django](https://img.shields.io/badge/Django-4.2-092E20?style=flat&logo=django)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF?style=flat&logo=vite)](https://vitejs.dev/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=flat&logo=docker)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Problem It Solves

Traditional freelance platforms suffer from three core trust failures: clients pay upfront with no delivery guarantee, freelancers complete work but never get paid, and there is no transparent audit trail of work performed. FreelanceFlow solves all three with AI-assisted worklog generation, milestone-based escrow payments, real-time WebSocket communication, and automated weekly proof-of-work reports — ensuring full accountability for both sides.

---

## 🛠️ Tech Stack

### **Backend**
- **Framework**: Django 4.2 — Modular Monolith
- **Database**: PostgreSQL (Supabase)
- **Caching & Broker**: Redis 7 (Docker)
- **Task Queue**: Celery + Celery Beat (`DatabaseScheduler`)
- **WebSockets**: Django Channels + Daphne (ASGI)
- **Search Engine**: Elasticsearch 8.14 (`django-elasticsearch-dsl`)

### **Frontend**
- **Framework**: React 18 + Vite
- **Styling**: TailwindCSS + PostCSS + Lucide Icons
- **HTTP & State**: Axios, React Router v6

### **AI & Integrations**
- **LLM**: Groq API — Llama 3.3 70B Versatile
- **Orchestration**: LangChain + LangGraph (two separate state-machine graphs)
- **Monitoring**: LangSmith — `@traceable` on every graph entrypoint
- **Payments**: Razorpay Escrow + RazorpayX Automated Payout + Webhook
- **PDF Generation**: WeasyPrint → bytes → Azure Blob Storage / S3

### **Security & Auth**
- **Authentication**: SimpleJWT (access 60 min / refresh 7 days, rotation, blacklist) + Google OAuth2 SSO
- **Protection**: Rate throttling (Auth 5/min, OAuth 10/min), JWT blacklisting, RBAC (CLIENT / FREELANCER)
- **Brute-force**: Django Axes — 5 failures → 5-min lockout

### **DevOps & Infrastructure**
- **Deployment**: Azure Virtual Machine (Linux / Nginx + Gunicorn / Daphne)
- **Cloud Storage**: Azure Blob Storage — PDFs, screenshots, invoices
- **Containerization**: Docker Compose with Profile Support (`profiles: [app]`)
- **Error tracking**: Sentry (production)

---

## ✨ Key Features

| Feature | Details |
|---|---|
| 🤖 **AI Chat Worklog** | Conversational assistant (LangGraph `ChatAgentState` graph) helps freelancers describe work in natural language → auto-generates a structured JSON deliverable. Async Django views + `sync_to_async` keep ASGI non-blocking. |
| 📅 **Report Schedules** | Clients configure report cadence (7 / 14 / 30 days). Celery Beat triggers AI weekly report + PDF automatically; freelancer is notified 3 days before each deadline. Manual trigger available (`POST report-schedule/{id}/generate-now/`, rate-limited 1/hr). |
| 📋 **Deliverable Lifecycle** | 6-state machine: DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED / REJECTED / REVISION_REQUESTED. Client approval automatically creates an associated WorkLog. |
| 💰 **Escrow Payments** | Razorpay order → HMAC-SHA256 signature verify → funds escrowed → client releases → RazorpayX payout to freelancer. Webhook idempotency via `PaymentEvent` unique constraint. |
| 📄 **PDF Proof Documents** | Weekly progress reports + tamper-evident delivery proof PDFs (WeasyPrint → S3 pre-signed 7-day URL). |
| 🔍 **Smart Search** | Full-text + keyword search across projects and freelancer profiles via Elasticsearch. Search history, saved searches, autocomplete suggestions. |
| 💬 **Live Chat** | Contract-scoped real-time messaging over WebSockets (Daphne + Django Channels, Redis group per contract). Online status updated via WebSocket. |
| 🔐 **Auth & RBAC** | Google OAuth2 SSO + JWT, role-based permissions throughout. Subscription tier field (FREE / PRO) — model exists, billing not yet wired. |
| 🔔 **Notifications** | In-app + email + push (FCM-ready). Per-user per-event toggles (21 boolean fields). Digest emails (DAILY / WEEKLY / MONTHLY). System announcements (role-targeted). |

---

## ⚡ Quick Start with `Makefile`

```bash
# Start Django Backend (Port 8000)
make backend

# Start Frontend Dev Server (Port 3000)
make frontend-dev

# Start Celery Worker
make worker

# Run Auth Tests (--keepdb)
make test-auth

# Show all available commands
make help
```

---

## 🚀 Manual Development Setup

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### 2. Start Infrastructure (Redis + Elasticsearch)
```bash
git clone https://github.com/Sayandip05/FreelanceFlow.git
cd FreelanceFlow

# Start Redis and Elasticsearch in background
docker compose up -d
```

### 3. Backend Setup
```bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements/base.txt

cp .env.example .env
# Fill in GROQ_API_KEY, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET,
# DATABASE_URL, AZURE_STORAGE_CONNECTION_STRING, etc.

python manage.py migrate
python manage.py runserver
```

### 4. Celery Workers & Beat (Separate Terminals)
```bash
# Worker
celery -A config worker -l info -Q freelanceflow,freelanceflow_high_priority,freelanceflow_low_priority

# Beat scheduler
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### 5. Frontend Setup
```bash
cd frontend/
npm install
npm run dev
```

---

## 🐳 Running Full Stack via Docker

```bash
docker compose --profile app up --build -d
```

| Service | Port | URL |
|---|---|---|
| **Frontend** | `5173` | `http://localhost:5173` |
| **Django REST API** | `8000` | `http://localhost:8000/api/` |
| **WebSocket Server** | `8001` | `ws://localhost:8001/ws/` |
| **Elasticsearch** | `9200` | `http://localhost:9200` |
| **Redis** | `6379` | `localhost:6379` |

---

## 📐 System Architecture

```
                              ┌─────────────────────────┐
                              │   React 18 + Vite UI    │
                              └────────────┬────────────┘
                                           │
                             HTTP / WS Proxy (Vite / Nginx)
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    │                                             │
           ┌────────▼────────┐                           ┌────────▼────────┐
           │  Django WSGI    │                           │  Daphne ASGI    │
           │ (REST API 8000) │                           │(WebSockets 8001)│
           └────────┬────────┘                           └────────┬────────┘
                    │                                             │
  ┌─────────────────┼──────────────┬──────────────────────────────┤
  │                 │              │                              │
┌─▼──────────┐  ┌───▼────┐  ┌─────▼──────┐              ┌───────▼──────┐
│ PostgreSQL │  │ Redis  │  │   Celery   │              │Elasticsearch │
│ (Supabase) │  │   7    │  │ Worker+Beat│              │   (Search)   │
└────────────┘  └────────┘  └─────┬──────┘              └──────────────┘
                                  │
                    ┌─────────────┴────────────┐
                    │                          │
             ┌──────▼──────┐          ┌────────▼────────┐
             │  Groq LLM   │          │  Azure Blob /   │
             │ (LangGraph) │          │   S3 Storage    │
             └─────────────┘          └─────────────────┘
```

---

## 🤖 AI Architecture Overview

Two independent LangGraph state-machine pipelines power the AI features:

**Graph 1 — Chat Agent** (`groq_service.py` · `GroqChatService`)  
Used by `POST /api/worklogs/ai-chat/message/`. Freelancer chats naturally about their work; the graph routes between asking follow-up questions (`continue`) and emitting a structured JSON report (`generate_report`). Both AI endpoints are **async** (`sync_to_async`) to keep the ASGI thread non-blocking.

**Graph 2 — Weekly Report Pipeline** (`ai_service.py`)  
Triggered by Celery Beat. Three sequential nodes: `gather_logs` → `build_prompt` → `generate_report`. Produces a 3-section Markdown report (SUMMARY / DETAILS / NEXT STEPS) stored in `WeeklyReport.ai_summary`, then rendered to PDF via WeasyPrint and uploaded to S3.

Both graphs fall back to a direct `groq.chat.completions.create()` call on any LangGraph failure, and further to a static template when `GROQ_API_KEY` is absent.

---

## 📚 Documentation

| Doc | Contents |
|---|---|
| [docs/HLD.md](./docs/HLD.md) | High-level architecture, data model, API surface, all data flows, AI pipeline details |
| [docs/API.md](./docs/API.md) | Full REST API reference with request/response examples |
| [docs/folderstructure.md](./docs/folderstructure.md) | Comprehensive file & app structural mapping |

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Sayandip Bar**
- GitHub: [@Sayandip05](https://github.com/Sayandip05)
- Email: sayandipbar05@gmail.com
- Repository: [Sayandip05/FreelanceFlow](https://github.com/Sayandip05/FreelanceFlow)
