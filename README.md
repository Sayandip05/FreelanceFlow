# FreelanceFlow

**AI-Powered Freelance Marketplace with Milestone Escrow, Vector-Grounded Worklogs & Real-Time Collaboration**

[![Django](https://img.shields.io/badge/Django-4.2-092E20?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF?style=for-the-badge&logo=vite)](https://vitejs.dev/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_Cloud-DC2626?style=for-the-badge&logo=qdrant)](https://qdrant.tech/)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-F55036?style=for-the-badge)](https://groq.com/)
[![Gemini](https://img.shields.io/badge/Google_Gemini-2.0_Flash-4285F4?style=for-the-badge&logo=google)](https://ai.google.dev/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

---

## 🎯 Problem It Solves

Traditional freelance platforms suffer from three core trust failures:
1. **Clients pay upfront with zero delivery guarantee** or face opaque progress updates.
2. **Freelancers complete work but face payout delays**, scope creep, or non-payment.
3. **There is no tamper-evident audit trail** of tasks performed, hours logged, and milestone sign-offs.

**FreelanceFlow** solves all three through:
- 🛡️ **Milestone-Based Escrow**: Funds are locked in Razorpay Escrow before work begins and automatically released upon client deliverable sign-off.
- 🤖 **Vector-Grounded AI Worklog Assistant**: Conversational LangGraph AI grounded via **Qdrant Vector Cloud** (`gemini-embedding-001` 3072-dim embeddings) and **Groq LLaMA 3.3 70B** (with automated **Gemini 2.0 Flash** fallback) to synthesize structured weekly deliverables and compile PDF reports.
- ⚡ **Real-Time ASGI WebSockets**: In-memory channel communication powered by Daphne with live typing indicators and bi-directional read receipts (`✓` / `✓✓`).
- 🔔 **Instant Notification Hub**: Persistent header bell with live unread badge, hover auto-expansion, and multi-channel preferences (In-App, Email, Push).

---

## 🧭 Interactive Workflow Diagrams

### 1. 🧑‍💻 Freelancer Experience Journey

```mermaid
flowchart TD
    classDef startEnd fill:#4F46E5,stroke:#312E81,stroke-width:2px,color:#fff;
    classDef process fill:#EEF2FF,stroke:#6366F1,stroke-width:2px,color:#1E1B4B;
    classDef ai fill:#FDF4FF,stroke:#A855F7,stroke-width:2px,color:#581C87;
    classDef escrow fill:#ECFDF5,stroke:#10B981,stroke-width:2px,color:#064E3B;

    Start([Freelancer Sign Up / Google SSO]):::startEnd --> Onboard[Profile Setup: Skills, Hourly Rate, Bio]:::process
    Onboard --> Browse[Browse Marketplace & Submit Proposal / Bid]:::process
    Browse --> Hired{Client Accepts Bid?}
    
    Hired -- No --> Browse
    Hired -- Yes --> Contract[Contract Activated & Milestones Set]:::escrow
    
    Contract --> AIBot[Open AI Worklog Assistant]:::ai
    AIBot --> Context[Qdrant Semantic Grounding: Project Scope & Goals]:::ai
    Context --> Chat[Log Daily Tasks via Natural Language Chat]:::ai
    
    Chat --> GenDraft[AI Synthesizes Structured Deliverable & PDF]:::ai
    GenDraft --> Submit[Submit Milestone Deliverable with Proof]:::process
    
    Submit --> ClientReview{Client Approves Deliverable?}
    ClientReview -- Revisions Requested --> Chat
    ClientReview -- Approved --> EscrowRelease[Funds Released from Escrow]:::escrow
    
    EscrowRelease --> Review[Dual-Blind Client Review & Feedback]:::process
    Review --> End([Project Completed & Earnings Paid]):::startEnd
```

---

### 2. 🏢 Client Project & Escrow Journey

```mermaid
flowchart TD
    classDef startEnd fill:#0F172A,stroke:#020617,stroke-width:2px,color:#fff;
    classDef process fill:#F0F9FF,stroke:#0284C7,stroke-width:2px,color:#0C4A6E;
    classDef escrow fill:#ECFDF5,stroke:#059669,stroke-width:2px,color:#064E3B;
    classDef alert fill:#FFF1F2,stroke:#E11D48,stroke-width:2px,color:#881337;

    Start([Client Sign Up / Google SSO]):::startEnd --> PostJob[Create Project: Title, Scope, Budget in USD]:::process
    PostJob --> ReviewBids[Receive & Compare Freelancer Proposals]:::process
    ReviewBids --> Award[Award Contract to Chosen Freelancer]:::process
    
    Award --> EscrowDeposit[Deposit Milestone Funds into Escrow]:::escrow
    EscrowDeposit --> Secure[Funds Locked Securely in Razorpay Escrow]:::escrow
    
    Secure --> Collab[Live Chat & Progress Tracking via WebSockets]:::process
    Collab --> ReceiveDeliverable[Receive AI Deliverable & WeasyPrint PDF]:::process
    
    ReceiveDeliverable --> Inspect{Inspect Work Quality & Deliverable}
    Inspect -- Changes Needed --> RequestChanges[Request Revisions via Chat]:::process
    RequestChanges --> Collab
    Inspect -- Irreconcilable Dispute --> Dispute[Initiate Arbitration / Dispute]:::alert
    
    Inspect -- Approved --> ReleaseEscrow[Approve Milestone & Release Payment]:::escrow
    ReleaseEscrow --> Receipt[Download Payment Receipt & Release Payout]:::escrow
    Receipt --> Review[Submit Freelancer Rating & Dual-Blind Review]:::process
    Review --> End([Contract Successfully Completed]):::startEnd
```

---

### 3. 🏗️ Platform Core Architecture & Data Engine

```mermaid
graph TB
    subgraph Frontend ["Frontend Layer (React 18 + Vite)"]
        UI["Tailwind CSS 3 + Lucide Icons"]
        Router["AppRouter & Protected RBAC Routes"]
        Layout["Dynamic Hover Sidebar (h-11) + NotificationBell"]
        WSClient["WebSocket Client (Auto Reconnect & Read Receipts)"]
    end

    subgraph Gateway ["ASGI Application Server"]
        Daphne["Daphne ASGI Server (Port 8000)"]
        ChannelLayer["InMemoryChannelLayer (Zero Redis for Chat)"]
    end

    subgraph BackendServices ["Backend Modular Monolith (Django 4.2)"]
        UsersApp["apps/users: Google OAuth SSO, JWT & RBAC"]
        ProjectsApp["apps/projects: Job Listings & Skills Taxonomy"]
        BiddingApp["apps/bidding: Proposals & Contract State Machine"]
        PaymentsApp["apps/payments: Razorpay Escrow & Idempotency"]
        MessagingApp["apps/messaging: Real-Time Chat & Read Receipts"]
        WorklogsApp["apps/worklogs: AI Deliverables & PDF Reports"]
        NotifsApp["apps/notifications: Notification Hub & Preferences"]
        SearchApp["apps/search: Elasticsearch 8 Hybrid Engine"]
    end

    subgraph AIEngine ["AI & Vector Grounding Engine"]
        Qdrant[("Qdrant Vector Cloud\n(gemini-embedding-001 3072-dim)")]
        GroqLLM["Groq LLaMA 3.3 70B (Primary LLM)"]
        GeminiLLM["Google Gemini 2.0 Flash (Fallback LLM)"]
        LangGraph["3-Node Stateful LangGraph Pipeline"]
    end

    subgraph DataStorage ["Data & Background Task Layer"]
        PostgreSQL[("PostgreSQL\n(Composite B-Tree Indexes)")]
        UpstashRedis[("Upstash Redis\n(Celery Task Queues Exclusively)")]
        CeleryWorkers["Celery Workers & Beat Scheduler"]
        AzureBlob[("Azure Blob Storage\n(Time-Limited SAS URLs)")]
        Elasticsearch[("Elasticsearch 8.14\n(Dual Inverted Index)")]
    end

    Frontend -->|HTTP REST & JSON| Daphne
    Frontend <-->|WebSocket ws://| Daphne
    Daphne --> ChannelLayer
    Daphne --> BackendServices

    WorklogsApp --> LangGraph
    LangGraph --> Qdrant
    LangGraph --> GroqLLM
    GroqLLM -.->|Failover| GeminiLLM

    BackendServices --> PostgreSQL
    BackendServices --> Elasticsearch
    BackendServices -->|Queues Only| UpstashRedis
    UpstashRedis --> CeleryWorkers
    CeleryWorkers --> AzureBlob
```

---

## 🛠️ Tech Stack & Engineering Standards

| Layer | Technologies & Components |
|---|---|
| **Frontend** | React 18, Vite 6, Tailwind CSS, Lucide React, Axios, React Router v6 |
| **Backend Framework** | Django 4.2 (Modular Monolith architecture with `selectors.py` & `services.py`) |
| **Database** | PostgreSQL with composite cardinality-first B-Tree indexes and strict N+1 query elimination |
| **Vector Memory** | Qdrant Vector Cloud with Google Gemini 3072-dimensional normalized embeddings (`gemini-embedding-001`) |
| **LLM Inference** | Primary: **Groq LLaMA 3.3 70B** (`llama-3.3-70b-versatile`) · Fallback: **Google Gemini 2.0 Flash** (`gemini-flash-latest`) |
| **AI Orchestration** | LangGraph 3-Node Stateful State Machine (`context_assembler` → `report_generator` → `pdf_builder`) |
| **WebSockets** | Daphne ASGI + `InMemoryChannelLayer` (single process, zero worker involvement, zero Redis for chat) |
| **Task Queue** | Celery 5.3 + Celery Beat (`DatabaseScheduler`) backed exclusively by Upstash Redis |
| **Escrow & Payments** | Razorpay Milestone Escrow with HMAC-SHA256 signature verification & `PaymentEvent` idempotency |
| **Storage & Documents** | Azure Blob Storage (7-day SAS signed URLs) + WeasyPrint HTML-to-PDF rendering |
| **Search Engine** | Elasticsearch 8.14 with typo-tolerant fuzzy matching, field boosting, and autocomplete |
| **Authentication** | SimpleJWT with token blacklisting, Google OAuth2 SSO (`mode=login|register`), and TOTP 2FA |

---

## ✨ Key Platform Features

### 🤖 1. Vector-Grounded AI Worklog Assistant
- **Grounded Chat**: Ingests project scope, milestones, deliverables, and past reports into Qdrant Cloud.
- **Natural Language Work Logging**: Freelancers describe daily progress in plain English; the AI validates completed items and drafts client-ready deliverables.
- **Automated WeasyPrint PDF**: Generates branded, tamper-evident weekly progress PDFs with cryptographically verifiable report IDs.

### 💰 2. Milestone Escrow & Protection
- **Deposit before Work**: Clients deposit funds into escrow milestone-by-milestone.
- **Release upon Approval**: Funds are safely held until the client inspects and approves submitted work.
- **Freelancer Platform Wallet**: Upon milestone approval, funds (gross minus platform fee) are credited to the freelancer's wallet.
- **Option B Payout Details**: Freelancers can securely link and update their bank details (IFSC, Account Number, Holder Name) securely via RazorpayX directly from Payout Settings or on-demand when initiating their first withdrawal.
- **Universal USD Standard**: All financial values, budgets, invoices, and analytics formatted universally in USD (`$`).

### 💬 3. Real-Time Chat & Read Receipts
- **Bi-Directional Read Receipts**: Messages show single tick (`✓`) when sent and double blue tick (`✓✓`) when read by the recipient.
- **Low-Latency ASGI**: Directly routed within Daphne via `InMemoryChannelLayer` without Redis Pub/Sub overhead.

### 🎨 4. Zero-Layout-Shift Modern UI
- **Hover Auto-Expanding Sidebar**: Sidebars smoothly expand to full width (`w-64`) on cursor hover and collapse to `w-20` on mouse exit, keeping fixed `h-11` element heights and `space-y-2` spacing with zero vertical jumping.
- **Top Header Notification Hub**: Persistent bell icon with live unread badge, hover pop-down, and 180ms debounce for flicker-free inspection.

---

## ⚡ Quick Start with `Makefile`

```bash
# Start Django ASGI/WSGI Backend (Port 8000)
make backend

# Start Vite Frontend Dev Server (Port 3000)
make frontend-dev

# Start Celery Worker (Pre-configured queues)
make worker

# Run test suite
make test

# View all available management commands
make help
```

---

## 🚀 Manual Development Setup

### 1. Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### 2. Environment Configuration
Create a `.env` file in the project root:
```env
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_SETTINGS_MODULE=config.settings.local
DEBUG=True

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/freelanceflow

# Redis (Upstash for Celery queues only)
REDIS_URL=redis://localhost:6379/0

# AI Credentials
GROQ_API_KEY=gsk_...
GEMINI_API_KEY=AIzaSy...
GEMINI_EMBEDDING_MODEL=gemini-embedding-001

# Qdrant Vector Cloud
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=eyJ...

# Payments (Razorpay)
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
```

### 3. Backend Setup
```bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements/base.txt

python manage.py migrate
python manage.py runserver
```

### 4. Celery Worker (Separate Terminal)
```bash
celery -A config worker -l info -Q freelanceflow_default,freelanceflow_high_priority,freelanceflow_low_priority
```

### 5. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

---

## ⚡ Performance Benchmarking (Locust Suite)

FreelanceFlow includes an automated, modular **Locust Performance Benchmark Suite** that measures API throughput, p50/p95/p99 latencies, real-time WebSocket round-trips, Celery task dispatch times, Upstash Redis cache latency, and server-side SQL overhead (with automated N+1 detection).

### 🚀 Terminal Shortcut (One-Command Headless Benchmark)
To run the automated performance benchmark suite directly in your terminal:

```bash
# Shortcut 1: Run complete headless benchmark suite with default parameters
./benchmarks/run_benchmarks.sh

# Shortcut 2: Using Makefile target
make benchmark-headless

# Custom load profile: ./benchmarks/run_benchmarks.sh <users> <spawn_rate> <duration> <host>
./benchmarks/run_benchmarks.sh 15 3 20s http://127.0.0.1:8000
```

### 🌐 Interactive Web UI Mode
To launch the interactive Locust dashboard with real-time graphs at `http://localhost:8089`:
```bash
make benchmark-web
# Or directly via Locust CLI:
locust -f benchmarks/locustfile.py --host=http://127.0.0.1:8000
```

> 📄 **Benchmark Report**: The benchmark automatically generates an executive scorecard and saves it to [BENCHMARK_REPORT.md](./BENCHMARK_REPORT.md).

---

## 📚 Comprehensive Documentation

| Document | Description |
|---|---|
| **[docs/HLD.md](./docs/HLD.md)** | High-Level Architecture, Domain Boundaries, and System Topology |
| **[docs/FLOW.md](./docs/FLOW.md)** | Full Execution Flows, API Call Graphs, WebSocket & Signal Traces |
| **[docs/DECISIONS.md](./docs/DECISIONS.md)** | 20 Architectural Decision Records (ADRs) explaining technical choices & tradeoffs |
| **[docs/API.md](./docs/API.md)** | Complete REST API Reference with schema payloads and status codes |
| **[BENCHMARK_REPORT.md](./BENCHMARK_REPORT.md)** | Executive Performance Scorecard, Latency Breakdown, and SQL Query Telemetry |
| **[docs/folderstructure.md](./docs/folderstructure.md)** | Codebase file hierarchy and component index |

