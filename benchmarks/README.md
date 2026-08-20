# FreelanceFlow — Performance Benchmarks

This folder contains **Locust** load tests for every app in the project.

## Structure

```
benchmarks/
├── locustfile.py          # Master file — all apps mixed, realistic traffic
├── test_users.py          # Users app: auth, profile, status
├── test_projects.py       # Projects app: listing, creation, bookmarks
├── test_bidding.py        # Bidding app: bids, contracts, reviews
├── test_payments.py       # Payments app: history, milestones, escrow
├── test_messaging.py      # Messaging app: conversations, send message
├── test_notifications.py  # Notifications app: unread count, mark read
├── test_search.py         # Search app: Elasticsearch queries, autocomplete
├── test_worklogs.py       # Worklogs app: logs, reports, AI chat
└── README.md
```

---

## Setup

```bash
pip install locust
```

---

## How to Run

### 1. Web UI (Recommended to start with)
Opens a browser at `http://localhost:8089` where you can set users and spawn rate interactively.

```bash
# Full platform mixed traffic
locust -f benchmarks/locustfile.py --host=http://localhost:8000

# Single app only
locust -f benchmarks/test_search.py --host=http://localhost:8000
```

### 2. Headless — Quick Smoke Test (50 users, 60 seconds)
```bash
locust -f benchmarks/locustfile.py --host=http://localhost:8000 \
    --headless --users 50 --spawn-rate 5 --run-time 60s \
    --html benchmarks/report.html --csv benchmarks/results
```

### 3. Headless — Full Load Test (200 users, 5 minutes)
```bash
locust -f benchmarks/locustfile.py --host=http://localhost:8000 \
    --headless --users 200 --spawn-rate 10 --run-time 300s \
    --html benchmarks/report.html --csv benchmarks/results
```

---

## What Each File Tests

| File | Endpoints Covered | Key Metric to Watch |
|---|---|---|
| `test_users.py` | login, me, token/refresh, activity, status | P95 < 200ms |
| `test_projects.py` | list, detail, bids, bookmark | P95 < 300ms |
| `test_bidding.py` | bids, contracts, counter-offers, reviews | P95 < 300ms |
| `test_payments.py` | history, escrow, milestones, fund | P95 < 500ms |
| `test_messaging.py` | conversations, messages, send | P95 < 200ms |
| `test_notifications.py` | unread_count (polled often!) | P95 < 100ms |
| `test_search.py` | Elasticsearch queries, autocomplete | P95 < 400ms |
| `test_worklogs.py` | logs, reports, AI chat | AI: P95 < 5s |

---

## Performance Targets

| Response Time | Status |
|---|---|
| < 200ms | ✅ Excellent |
| 200–500ms | ⚠️ Acceptable |
| 500ms–1s | 🟠 Needs attention |
| > 1s | 🔴 Fix immediately |
| > 3s (non-AI) | 💀 Critical |

---

## Output Files

After a headless run, you'll get:
- `benchmarks/report.html` — visual HTML report with charts
- `benchmarks/results_stats.csv` — per-endpoint stats (avg, P50, P95, P99)
- `benchmarks/results_failures.csv` — any failed requests

Open `report.html` in your browser after the run to analyze.
