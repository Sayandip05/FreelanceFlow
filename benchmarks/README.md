# 🚀 FreelanceFlow — Locust Performance Benchmark Suite

A reusable, production-grade load testing and performance benchmarking framework for **FreelanceFlow** built with **Locust**, measuring API throughput, latency percentiles (p50/p95/p99), database query counts, N+1 query patterns, WebSocket latency, Celery task queue turnaround, and AI/RAG inference.

---

## 📋 Features & Capabilities

- **Authenticated Multi-Persona Load Generation**:
  - `FreelancerUser` (Browsing, search, proposals, contracts, worklogs, profile)
  - `ClientUser` (Contract management, proposals review, deliverables inspection, escrow transactions)
  - `PublicUser` (Anonymous search, skills catalog, autocomplete)
  - `WebSocketChatUser` (Daphne ASGI real-time chat handshake, message echo, read receipts)
  - `AIRagUser` (Qdrant Vector Cloud context grounding & Groq LLaMA 3.3 70B inference)
- **Automated Database & N+1 Query Detection**:
  - Server-side `PerformanceProfilingMiddleware` intercepts requests and measures SQL query count, SQL execution time, slow queries (>20ms), and duplicate query signatures (N+1 regressions).
- **Asynchronous Infrastructure Profiling**:
  - Celery background queue dispatch times (`freelanceflow_default`, `freelanceflow_high_priority`, `freelanceflow_low_priority`)
  - Upstash Redis network ping and SET/GET throughput
- **Automated Reporting**:
  - Generates comprehensive Markdown benchmark report (`BENCHMARK_REPORT.md`)
  - Provides **Resume-Ready Metrics** tailored for software engineering profiles.

---

## ⚡ Quick Start

### 1. One-Command Headless Benchmark Run
Ensure the backend server is running, then run:

```bash
# Run benchmark with 20 users, 4 users/sec spawn rate, 30-sec duration
./benchmarks/run_benchmarks.sh 20 4 30s
```

Or using `make`:
```bash
make benchmark-headless
```

### 2. Interactive Locust Web UI
To run with Locust's real-time browser dashboard:

```bash
# Start Locust web server on http://localhost:8089
venv/bin/locust -f benchmarks/locustfile.py --host http://localhost:8000
```
Open `http://localhost:8089` in your browser, enter user count and spawn rate, and click **Start swarming**.

---

## ⚙️ Configuration & Environment Variables

Load parameters and target hosts can be customized via environment variables or CLI flags:

| Variable | Default | Description |
|---|---|---|
| `BENCHMARK_HOST` | `http://localhost:8000` | Target HTTP REST API base URL |
| `BENCHMARK_WS_HOST` | `ws://localhost:8000` | Target Daphne ASGI WebSocket URL |
| `LOCUST_USERS` | `20` | Default number of concurrent virtual users |
| `LOCUST_SPAWN_RATE` | `4` | Users spawned per second |
| `LOCUST_RUN_TIME` | `30s` | Test duration (e.g. `30s`, `2m`, `5m`) |
| `BENCHMARK_FREELANCER_EMAIL` | `freelancer@example.com` | Test freelancer email |
| `BENCHMARK_CLIENT_EMAIL` | `client@example.com` | Test client email |

---

## 📊 Output & Reports

After execution, the suite compiles metrics into:
- **`BENCHMARK_REPORT.md`**: Executive performance report containing:
  1. Executive Scorecard (RPS, Median Latency, p95, p99, Error Rate)
  2. Endpoint Latency & Throughput Table
  3. Database Query & N+1 Audit Table
  4. Daphne WebSocket & Real-Time Metrics
  5. Celery Task Queue & Upstash Redis Performance
  6. AI/RAG Vector Retrieval & Inference Times
  7. Resume-Ready Metric Bullet Points
- **`benchmarks/results/`**: Raw CSV data and full request history logs.
