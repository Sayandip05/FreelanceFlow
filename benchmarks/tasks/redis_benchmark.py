"""
Redis & Broker Performance Benchmark
Measures round-trip network latency and throughput for Upstash Redis.
"""
import os
import sys
import time
import statistics
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.conf import settings
import redis


def run_redis_benchmark(iterations: int = 20):
    """
    Measures Upstash Redis connection ping and round-trip operations.
    """
    print("=" * 60)
    print("⚡ Running Upstash Redis Latency Benchmark")
    print("=" * 60)

    redis_url = getattr(settings, "CELERY_BROKER_URL", getattr(settings, "REDIS_URL", ""))
    if not redis_url:
        print("❌ No Redis URL configured in settings.")
        return {}

    try:
        import ssl
        import certifi
        client = redis.from_url(
            redis_url,
            socket_timeout=10,
            ssl_cert_reqs=ssl.CERT_REQUIRED,
            ssl_ca_certs=certifi.where(),
            retry_on_timeout=True
        )




        # 1. Ping Latency
        ping_times = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            client.ping()
            t1 = time.perf_counter()
            ping_times.append((t1 - t0) * 1000)

        # 2. SET / GET Roundtrip
        set_times = []
        get_times = []
        for i in range(iterations):
            key = f"benchmark:test:{i}"
            val = f"value_payload_{i}"

            t0 = time.perf_counter()
            client.set(key, val, ex=60)
            t1 = time.perf_counter()
            set_times.append((t1 - t0) * 1000)

            t0 = time.perf_counter()
            _ = client.get(key)
            t1 = time.perf_counter()
            get_times.append((t1 - t0) * 1000)

            client.delete(key)

        results = {
            "ping": {
                "avg_ms": round(statistics.mean(ping_times), 2),
                "p50_ms": round(statistics.median(ping_times), 2),
                "p95_ms": round(sorted(ping_times)[int(len(ping_times) * 0.95)], 2),
                "min_ms": round(min(ping_times), 2),
                "max_ms": round(max(ping_times), 2),
            },
            "set": {
                "avg_ms": round(statistics.mean(set_times), 2),
                "p95_ms": round(sorted(set_times)[int(len(set_times) * 0.95)], 2),
            },
            "get": {
                "avg_ms": round(statistics.mean(get_times), 2),
                "p95_ms": round(sorted(get_times)[int(len(get_times) * 0.95)], 2),
            },
        }

        print(f"  • Redis Ping:   Avg: {results['ping']['avg_ms']:>6.2f} ms | p50: {results['ping']['p50_ms']:>6.2f} ms | p95: {results['ping']['p95_ms']:>6.2f} ms")
        print(f"  • Redis SET:    Avg: {results['set']['avg_ms']:>6.2f} ms | p95: {results['set']['p95_ms']:>6.2f} ms")
        print(f"  • Redis GET:    Avg: {results['get']['avg_ms']:>6.2f} ms | p95: {results['get']['p95_ms']:>6.2f} ms")
        print("=" * 60)
        return results

    except Exception as e:
        print(f"❌ Redis benchmark error: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    run_redis_benchmark()
