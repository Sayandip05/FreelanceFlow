# CI/CD Pipeline Configuration

This directory contains CI/CD pipeline configurations for automated deployment of FreelanceFlow to Azure.

## 📁 Directory Structure

```
deployment/cicd/
├── README.md                    # This file
├── github-actions/              # GitHub Actions workflows
│   ├── deploy-production.yml    # Production deployment pipeline
│   ├── deploy-staging.yml       # Staging deployment pipeline
│   ├── run-tests.yml           # Automated testing
│   └── security-scan.yml       # Security vulnerability scanning
└── scripts/                     # Deployment helper scripts
    ├── deploy.sh               # Main deployment script
    ├── rollback.sh             # Rollback to previous version
    ├── health-check.sh         # Post-deployment health check
    └── backup-db.sh            # Pre-deployment database backup
```

---

## 🚀 Planned CI/CD Features

### 1. **Automated Testing**
- Run pytest suite on every commit (227 tests)
- Integration tests on pull requests
- Code coverage reporting

### 2. **Multi-Environment Deployment**
- **Development**: Auto-deploy on push to `develop` branch
- **Staging**: Auto-deploy on push to `staging` branch
- **Production**: Manual approval required for `main` branch

### 3. **Azure Deployment Strategy**
- Zero downtime deployment on Azure Virtual Machine / App Service
- Automatic rollback on health check failure
- Database migration automation (`python manage.py migrate`)

### 4. **Security & Quality Gates**
- Dependency vulnerability scanning (Dependabot)
- Secret scanning
- Code quality checks

---

## 🔧 Azure Cloud Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Azure Cloud (VNet)                      │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Azure Application Gateway / Load Balancer             │ │
│  │  - SSL Termination                                     │ │
│  │  - Health Checks                                       │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                 │
│  ┌────────────────────────▼──────────────────────────────┐  │
│  │  Azure Linux VM / App Service (Gunicorn + Daphne)     │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                 │
│  ┌────────────────────────▼──────────────────────────────┐  │
│  │  PostgreSQL (Supabase / Azure Database)               │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Azure Blob Storage (PDFs, Media & Attachments)       │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Required Secrets (GitHub Actions Example)

Add these secrets to your GitHub repository:

```yaml
# Azure Credentials
AZURE_STORAGE_CONNECTION_STRING
AZURE_CONTAINER_NAME

# Database & Celery
DATABASE_URL
REDIS_URL
UPSTASH_REDIS_REST_URL
UPSTASH_REDIS_REST_TOKEN

# Application Secrets
SECRET_KEY
RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET
RAZORPAY_WEBHOOK_SECRET
GROQ_API_KEY
```
