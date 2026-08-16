#!/usr/bin/env bash
set -e

# ==============================================================================
# FreelanceFlow — Automated Performance & Load Benchmark Runner
# ==============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

VENV_PYTHON="${PROJECT_ROOT}/venv/bin/python"
LOCUST_BIN="${PROJECT_ROOT}/venv/bin/locust"

USERS="${1:-20}"
SPAWN_RATE="${2:-4}"
RUN_TIME="${3:-30s}"
HOST="${4:-http://localhost:8000}"
RESULTS_DIR="${PROJECT_ROOT}/benchmarks/results"

mkdir -p "$RESULTS_DIR"

echo "======================================================================"
echo "🚀 FreelanceFlow Performance Benchmark Suite (Locust)"
echo "======================================================================"
echo "  • Target Host:       $HOST"
echo "  • Concurrent Users:  $USERS"
echo "  • Spawn Rate:        $SPAWN_RATE users/sec"
echo "  • Duration:          $RUN_TIME"
echo "  • Results Directory: $RESULTS_DIR"
echo "======================================================================"

# 1. Run Celery Background Task Benchmark
echo ""
echo "[1/3] Benchmarking Celery Background Task Queues..."
$VENV_PYTHON benchmarks/tasks/celery_benchmark.py || true

# 2. Run Upstash Redis Latency Benchmark
echo ""
echo "[2/3] Benchmarking Upstash Redis Latency & Throughput..."
$VENV_PYTHON benchmarks/tasks/redis_benchmark.py || true

# 3. Run Headless Locust Load Test
echo ""
echo "[3/3] Running Headless Locust Load Test..."
$LOCUST_BIN \
    -f benchmarks/locustfile.py \
    --headless \
    --users "$USERS" \
    --spawn-rate "$SPAWN_RATE" \
    --run-time "$RUN_TIME" \
    --host "$HOST" \
    --csv "$RESULTS_DIR/benchmark_run" \
    --csv-full-history

# 4. Generate Final Markdown Report & Resume Summary
echo ""
echo "📊 Compiling Benchmark Report & Resume Summary..."
$VENV_PYTHON -c "
from benchmarks.reporting.report_generator import generate_benchmark_report
from benchmarks.tasks.redis_benchmark import run_redis_benchmark
from benchmarks.tasks.celery_benchmark import run_celery_benchmark

redis_res = run_redis_benchmark(iterations=10)
celery_res = run_celery_benchmark(iterations=3)

generate_benchmark_report(
    csv_prefix='${RESULTS_DIR}/benchmark_run',
    output_path='BENCHMARK_REPORT.md',
    redis_data=redis_res,
    celery_data=celery_res
)
"

echo "======================================================================"
echo "🎉 Benchmark Complete! Report saved to: BENCHMARK_REPORT.md"
echo "======================================================================"
