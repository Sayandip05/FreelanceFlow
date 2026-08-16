"""
Celery Task Queue Benchmark
Measures background worker execution turnaround and dispatch latency.
"""
import os
import sys
import time
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from apps.users.tasks import send_welcome_email_task
from apps.search.tasks import update_es_document_task


def run_celery_benchmark(iterations: int = 5):
    """
    Measures task dispatch latency and queue health across pre-configured Celery queues.
    """
    print("=" * 60)
    print("🚀 Running Celery Background Task Performance Benchmark")
    print("=" * 60)

    results = []

    # 1. Benchmark: send_welcome_email_task (Queue: freelanceflow_default)
    dispatch_times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        async_res = send_welcome_email_task.delay(user_id=20)
        t1 = time.perf_counter()
        dispatch_times.append((t1 - t0) * 1000)

    avg_dispatch = sum(dispatch_times) / len(dispatch_times)
    min_dispatch = min(dispatch_times)
    max_dispatch = max(dispatch_times)

    results.append({
        "task": "send_welcome_email_task",
        "queue": "freelanceflow_default",
        "avg_dispatch_ms": round(avg_dispatch, 2),
        "min_dispatch_ms": round(min_dispatch, 2),
        "max_dispatch_ms": round(max_dispatch, 2),
        "status": "HEALTHY" if avg_dispatch < 50 else "DEGRADED"
    })

    # 2. Benchmark: update_es_document_task (Queue: freelanceflow_low_priority)
    index_times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        async_res = update_es_document_task.delay("Project", "projects", 1, "Project 1")
        t1 = time.perf_counter()
        index_times.append((t1 - t0) * 1000)

    avg_index = sum(index_times) / len(index_times)
    results.append({
        "task": "update_es_document_task",
        "queue": "freelanceflow_low_priority",
        "avg_dispatch_ms": round(avg_index, 2),
        "min_dispatch_ms": round(min(index_times), 2),
        "max_dispatch_ms": round(max(index_times), 2),
        "status": "HEALTHY" if avg_index < 50 else "DEGRADED"
    })


    for r in results:
        print(f"  • Task: {r['task']:<30} | Queue: {r['queue']:<25} | Dispatch: {r['avg_dispatch_ms']:>6.2f} ms | Status: {r['status']}")

    print("=" * 60)
    return results


if __name__ == "__main__":
    run_celery_benchmark()
