# System Architecture

## Overview

Perimeter is a stateless, high-performance security gateway that intercepts LLM API calls, applies enterprise-grade security controls, optimizes payloads, and forwards requests to frontier model providers.

## Core Components

### 1. Gateway Layer (`src/gateway/`)

**FastAPI Application** - Main entry point handling:
- HTTP request/response lifecycle
- Authentication & authorization
- Routing to security engines
- Metrics collection

**Key Files:**
- `main.py` - Application bootstrap and middleware
- `config.py` - Environment-based configuration
- `auth.py` - API key validation
- `llm_client.py` - LLM provider forwarding

### 2. BAML Type Guardrail Engine (`src/baml_engine/`)

**Purpose:** Runtime type validation and prompt injection inoculation

**Mechanism:**
- Parses `.baml` schema definitions
- Validates all inputs against strict types
- Treats user content as immutable variables
- Catches malformed LLM outputs and reconstructs valid responses

**Key Files:**
- `validator.py` - Schema validation logic

### 3. Headroom Compression & Caching (`src/headroom/`)

**Purpose:** Compress payloads 70-90% while maintaining context integrity

**Components:**

**ContentRouter** (`content_router.py`):
- Analyzes content type (code, JSON, prose)
- Routes to appropriate compression engine

**HeadroomCompressor** (`compressor.py`):
- **CodeCompressor**: AST-based function body collapse
- **SmartCrusher**: Kneedle algorithm for array filtering
- **Kompress**: Token-level prose optimization

**Compress-Cache-Retrieve (CCR) Cycle:**
1. Compress content using optimal algorithm
2. Cache original in Redis with 64-bit hash
3. Replace content with hash reference
4. Inject `headroom_retrieve` tool for LLM to request cached content

### 4. Cache Optimization (`src/cache/`)

**CacheAligner** (`cache_aligner.py`):
- Moves dynamic attributes (UUIDs, timestamps) to end of prompts
- Maximizes LLM provider KV cache hits
- Reduces latency and cost

**RedisClient** (`redis_client.py`):
- High-performance async Redis client
- Connection pooling
- Supports caching, rate limiting, usage tracking

### 5. Guardrails (`src/guardrails/`)

**PIIDetector** (`pii_detector.py`):
- Regex-based detection of SSNs, credit cards, emails, phone numbers, API keys
- Sanitizes by replacing with redaction markers
- 99.95%+ accuracy on structured identifiers

**PromptInjectionDetector** (`prompt_injection.py`):
- Pattern matching for instruction override attempts
- Delimiter injection detection
- Jailbreak signature recognition

### 6. Billing System (`src/billing/`)

**UsageTracker** (`usage_tracker.py`):
- Tracks tokens saved, compression ratios, cache hits
- Writes to Redis for fast increments
- Per-tenant isolation

**BillingSync** (`sync_worker.py`):
- Hourly worker that flushes Redis → PostgreSQL
- Reports usage to Stripe
- Resets Redis counters

## Request Flow

```
1. Client Request
   ↓
2. Authentication (verify API key)
   ↓
3. BAML Type Validation
   ↓
4. Prompt Injection Detection
   ↓
5. PII Sanitization
   ↓
6. Content Type Classification
   ↓
7. Headroom Compression
   ↓
8. Cache Alignment Optimization
   ↓
9. Tool Injection (headroom_retrieve)
   ↓
10. Forward to LLM Provider
   ↓
11. Response Validation
   ↓
12. Usage Tracking
   ↓
13. Return to Client
```

## Performance Targets

| Component | Target | Implementation |
|-----------|--------|----------------|
| Proxy Latency | <5ms | In-memory processing, no DB calls in request path |
| Cache Hydration | <3ms | Redis in same VPC, connection pooling |
| Compression Ratio | 70-90% | Multi-strategy routing based on content type |
| PII Detection | 99.95%+ | Regex + NER models |
| Uptime | 99.99% | Active-active multi-region, auto-scaling |

## Security Principles

1. **Spatial Isolation**: All processing within customer VPC
2. **Zero Plaintext Egress**: Only compressed/hashed data leaves VPC
3. **Immutable Variables**: User input never executed as instructions
4. **Type Safety**: Strict schemas prevent injection attacks
5. **Audit Trail**: All decisions logged to WORM storage

## Deployment Models

### SaaS (Shared Infrastructure)
- Multi-tenant Cloud Run deployment
- Shared Redis + PostgreSQL
- Per-tenant isolation via API keys
- Usage-based billing via Stripe

### Enterprise (Single-Tenant VPC)
- Dedicated GKE cluster or Cloud Run instance
- Customer-owned Redis + PostgreSQL
- Private GCP Marketplace deployment
- Draws on committed GCP spend

## Monitoring & Observability

- **Metrics**: Prometheus + Grafana
- **Logging**: Structured JSON logs
- **Tracing**: OpenTelemetry integration
- **Alerting**: PagerDuty integration for SLA violations

## Scaling Strategy

- Horizontal auto-scaling based on CPU/memory
- Redis cluster for cache distribution
- PostgreSQL read replicas for analytics
- Multi-region active-active for global latency
