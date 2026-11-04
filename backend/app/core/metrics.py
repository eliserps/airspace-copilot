from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)

REGISTRY = CollectorRegistry()

HTTP_REQUESTS = Counter(
    "http_requests_total", "HTTP requests.", ["method", "route", "status"], registry=REGISTRY
)
HTTP_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request latency.", ["method", "route"], registry=REGISTRY
)
LLM_CALLS = Counter("llm_calls_total", "LLM calls.", ["feature"], registry=REGISTRY)
LLM_TOKENS = Counter("llm_tokens_total", "LLM tokens.", ["feature", "kind"], registry=REGISTRY)
LLM_LATENCY = Histogram(
    "llm_call_duration_seconds",
    "LLM call latency.",
    ["feature"],
    buckets=(0.25, 0.5, 1, 2, 4, 8, 16, 32),
    registry=REGISTRY,
)
CACHE_LOOKUPS = Counter(
    "cache_lookups_total", "Cache lookups by outcome.", ["cache", "result"], registry=REGISTRY
)
UPSTREAM_ERRORS = Counter(
    "upstream_errors_total", "Failed calls to external services.", ["source"], registry=REGISTRY
)


def render() -> tuple[bytes, str]:
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
