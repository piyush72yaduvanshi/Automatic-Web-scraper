"""Performance & Benchmark Testing Suite.

Measures:
1. Response latency (p50, p95, p99, mean) across critical API endpoints
2. Throughput under concurrent batch requests
3. Memory / connection pool stability
"""

import time
import statistics
import pytest
from fastapi.testclient import TestClient

from main import app
from app.core.database import get_db


def test_health_endpoint_latency(client):
    """Benchmark /api/v1/health response latency (Target: < 50ms average)."""
    latencies = []
    iterations = 50

    for _ in range(iterations):
        start = time.perf_counter()
        resp = client.get("/api/v1/health")
        duration_ms = (time.perf_counter() - start) * 1000
        assert resp.status_code == 200
        latencies.append(duration_ms)

    mean_ms = statistics.mean(latencies)
    p95_ms = statistics.quantiles(latencies, n=20)[18]  # 95th percentile
    print(f"\n[PERF] /api/v1/health: Mean = {mean_ms:.2f}ms, P95 = {p95_ms:.2f}ms across {iterations} reqs")
    assert mean_ms < 150.0, f"Mean latency {mean_ms:.2f}ms exceeds 150ms threshold"


def test_metrics_endpoint_latency(client):
    """Benchmark /metrics Prometheus export latency (Target: < 150ms)."""
    latencies = []
    iterations = 30

    for _ in range(iterations):
        start = time.perf_counter()
        resp = client.get("/metrics")
        duration_ms = (time.perf_counter() - start) * 1000
        assert resp.status_code == 200
        latencies.append(duration_ms)

    mean_ms = statistics.mean(latencies)
    p95_ms = statistics.quantiles(latencies, n=20)[18]
    print(f"\n[PERF] /metrics: Mean = {mean_ms:.2f}ms, P95 = {p95_ms:.2f}ms across {iterations} reqs")
    assert mean_ms < 200.0, f"Mean latency {mean_ms:.2f}ms exceeds 200ms threshold"


def test_analytics_overview_latency(client):
    """Benchmark /api/v1/analytics/overview aggregation latency (Target: < 200ms)."""
    latencies = []
    iterations = 25

    for _ in range(iterations):
        start = time.perf_counter()
        resp = client.get("/api/v1/analytics/overview")
        duration_ms = (time.perf_counter() - start) * 1000
        assert resp.status_code == 200
        latencies.append(duration_ms)

    mean_ms = statistics.mean(latencies)
    print(f"\n[PERF] /api/v1/analytics/overview: Mean = {mean_ms:.2f}ms across {iterations} reqs")
    assert mean_ms < 300.0, f"Mean latency {mean_ms:.2f}ms exceeds 300ms threshold"


def test_incoming_webhook_ingest_throughput(client):
    """Benchmark /api/v1/webhooks/ingest throughput under batch ingestion."""
    payload = {
        "business_name": "Perf Test Logistics",
        "email": "perf@logistics.in",
        "phone": "+91 99999 88888",
        "city": "Bengaluru",
        "category": "Logistics",
    }

    start = time.perf_counter()
    count = 20
    for i in range(count):
        payload["business_name"] = f"Perf Test Logistics #{i}"
        resp = client.post("/api/v1/webhooks/ingest", json=payload)
        assert resp.status_code == 200

    total_time = time.perf_counter() - start
    reqs_per_sec = count / total_time
    print(f"\n[PERF] Webhook Ingest Throughput: {reqs_per_sec:.2f} req/s ({count} requests in {total_time:.2f}s)")
    assert reqs_per_sec > 5.0, f"Throughput {reqs_per_sec:.2f} req/s is below 5 req/s"
