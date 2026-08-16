"""
FreelanceFlow Benchmark Configuration
Configurable load parameters, SLA thresholds, and test credentials.
"""
import os

# Target Server Configuration
HOST = os.getenv("BENCHMARK_HOST", "http://localhost:8000")
WS_HOST = os.getenv("BENCHMARK_WS_HOST", "ws://localhost:8000")

# Load Levels (Default: 20 concurrent users, spawn rate 4/sec, 30-sec test)
USERS = int(os.getenv("LOCUST_USERS", "20"))
SPAWN_RATE = int(os.getenv("LOCUST_SPAWN_RATE", "4"))
RUN_TIME = os.getenv("LOCUST_RUN_TIME", "30s")

# Test Accounts (Pre-seeded in Supabase database)
TEST_USERS = {
    "freelancer": {
        "email": os.getenv("BENCHMARK_FREELANCER_EMAIL", "freelancer@example.com"),
        "password": os.getenv("BENCHMARK_FREELANCER_PASSWORD", "password123"),
    },
    "freelancer_alt": {
        "email": os.getenv("BENCHMARK_FREELANCER_ALT_EMAIL", "fl1@ff.dev"),
        "password": os.getenv("BENCHMARK_FREELANCER_ALT_PASSWORD", "password123"),
    },
    "client": {
        "email": os.getenv("BENCHMARK_CLIENT_EMAIL", "client@example.com"),
        "password": os.getenv("BENCHMARK_CLIENT_PASSWORD", "password123"),
    },
    "client_alt": {
        "email": os.getenv("BENCHMARK_CLIENT_ALT_EMAIL", "cl1@ff.dev"),
        "password": os.getenv("BENCHMARK_CLIENT_ALT_PASSWORD", "password123"),
    },
}

# SLA Performance Thresholds
SLA_THRESHOLDS = {
    "p95_latency_ms": 300,        # 95th percentile latency must be under 300ms
    "p99_latency_ms": 600,        # 99th percentile latency must be under 600ms
    "error_rate_pct": 1.0,        # Error rate must be < 1%
    "max_queries_per_list": 6,    # List endpoints should not execute > 6 SQL queries
    "max_duplicate_queries": 0,   # Zero N+1 duplicate queries allowed
    "ws_handshake_ms": 150,       # WebSocket handshake under 150ms
    "ws_echo_ms": 50,             # WebSocket message round-trip under 50ms
}
