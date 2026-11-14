from prometheus_client import CollectorRegistry, Counter, Histogram

REGISTRY = CollectorRegistry()

http_requests = Counter(
    "http_requests_total", "Requests served",
    labelnames=("method", "path", "status"), registry=REGISTRY,
)

http_duration = Histogram(
    "http_request_duration_seconds", "Request duration",
    labelnames=("method", "path", "outcome"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.5, 5.0),
    registry=REGISTRY,
)
