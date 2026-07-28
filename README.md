# FreelanceFlow

**AI-powered freelance marketplace connecting clients with skilled freelancers**

[![Django](https://img.shields.io/badge/Django-5.0-092E20?style=flat&logo=django)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF?style=flat&logo=vite)](https://vitejs.dev/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=flat&logo=docker)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Problem It Solves

Traditional freelance platforms suffer from opaque work tracking, delayed payments, and high fee structures. FreelanceFlow solves this with AI-assisted worklog generation, milestone-based escrow payments, real-time WebSocket communication, and automated weekly project proof reports—ensuring accountability and smooth project delivery for both clients and freelancers.

---

## 🛠️ Tech Stack

### **Backend**
- **Framework**: Django 5.0 (Modular Monolith)
- **Database**: PostgreSQL (Supabase)
- **Caching & Broker**: Local Redis 7 (Docker)
- **Task Queue**: Celery + Celery Beat (DatabaseScheduler)
- **WebSockets**: Django Channels + Daphne (ASGI)
- **Search Engine**: Elasticsearch 8.14 (django-elasticsearch-dsl)

### **Frontend**
- **Framework**: React 18 + Vite
- **Styling**: TailwindCSS + PostCSS + Lucide Icons
- **HTTP & State**: Axios, React Router v6

### **AI & Integrations**
- **LLM Engine**: Groq API (LangChain / LangGraph)
- **Payments**: Razorpay Escrow & Webhook Integration
- **PDF Generation**: WeasyPrint / ReportLab
### **Security & Auth**
- **Authentication**: SimpleJWT (Access + Refresh Rotation), Google OAuth2 Single Sign-On (SSO)
- **Protection**: Rate Throttling (Auth 5/min, OAuth 10/min), JWT Blacklisting, RBAC

### **DevOps & Infrastructure**
- **Deployment**: Targeted for **Azure Virtual Machine (VM)** (Linux / Nginx + Gunicorn / Daphne)
- **Cloud Storage**: **Azure Blob Storage** (for PDF proof reports, worklog screenshots, and invoices)
- **Containerization**: Docker Compose with Profile Support (`profiles: [app]`)
- **Database**: Supabase Managed Postgres

---

## ✨ Key Features

- 🤖 **AI Worklog Summaries** — Conversational AI assistant generates structured daily progress reports
- 💰 **Escrow Protection** — Secure milestone funding released only upon client work approval
- 🔍 **Smart Search** — Full-text vector/keyword search across projects and freelancer profiles via Elasticsearch
- 💬 **Live Chat** — Contract-scoped real-time messaging over WebSockets
- 📊 **PDF & Proof Reports** — Timestamped proof-of-delivery documents generated automatically
- 🔐 **OAuth & Role-Based Control** — Google OAuth2 SSO + JWT, dedicated Client and Freelancer workflows with rate throttling

---

## ⚡ Quick Start with `Makefile`

For convenient local development, a root `Makefile` provides shortcut commands:

```bash
# 1. Start Django Backend (Port 8000)
make backend

# 2. Start Frontend Dev Server (Port 3000)
make frontend-dev

# 3. Start Celery Worker
make worker

# 4. Run Auth Tests (--keepdb)
make test-auth

# 5. Show all available commands
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
# Clone the repository
git clone https://github.com/Sayandip05/FreelanceFlow.git
cd FreelanceFlow

# Start Redis and Elasticsearch in background
docker compose up -d
```

### 3. Backend Setup
```bash
# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run database migrations
python manage.py migrate

# Start Django development server (Port 8000)
python manage.py runserver
```

### 4. Celery Workers & Beat (Separate Terminal Tabs)
```bash
# Run Celery Worker
celery -A config worker -l info -Q freelanceflow,freelanceflow_high_priority,freelanceflow_low_priority

# Run Celery Beat Scheduler
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### 5. Frontend Setup
```bash
# In frontend/ directory
npm install
npm run dev
```


---

## 🐳 Running Full Stack via Docker

To run the entire platform (Postgres, Redis, Elasticsearch, Web, Celery, Daphne, Frontend) containerized:

```bash
# Spin up full stack using the app profile
docker compose --profile app up --build -d
```

| Service | Port | Endpoint / URL |
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
      ┌─────────────────┼─────────────────┬───────────────────────────┤
      │                 │                 │                           │
┌─────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐             ┌──────▼──────┐
│ PostgreSQL │   │   Redis 7   │   │Celery Worker│             │Elasticsearch│
│ (Supabase) │   │ (Local/Broker)  │   │  + Beat     │             │  (Search)   │
└────────────┘   └─────────────┘   └──────┬──────┘             └─────────────┘
                                          │
                                   ┌──────▼──────┐
                                   │  Groq LLM   │
                                   │ (AI Engine) │
                                   └─────────────┘
```

---

## 📚 Repository Structure

Detailed design docs are available in the repository:
- **[folderstructure.md](./folderstructure.md)** — Comprehensive file & app structural mapping
- **[docs/HLD.md](./docs/HLD.md)** — High-Level Architecture & System Design
- **[docs/LLD.md](./docs/LLD.md)** — Low-Level Component Specs & Schema Design

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Sayandip Bar**
- GitHub: [@Sayandip05](https://github.com/Sayandip05)
- Email: sayandipbar05@gmail.com
- Project Repository: [Sayandip05/FreelanceFlow](https://github.com/Sayandip05/FreelanceFlow)
