# Perimeter AI Security Gateway - Repository Structure

## Directory Layout

```
perimeter/
├── .github/
│   └── workflows/
│       └── ci.yml                    # CI/CD pipeline
├── config/
│   ├── baml_src/
│   │   └── perimeter_schemas.baml   # BAML type schemas
│   └── environments/                 # Environment configs
├── docs/
│   ├── api/
│   │   └── README.md                # API reference
│   ├── architecture/
│   │   └── SYSTEM_DESIGN.md         # Architecture documentation
│   └── deployment/
│       └── README.md                # Deployment guide
├── examples/
│   ├── python/
│   │   ├── basic_usage.py           # Basic Python example
│   │   └── advanced_usage.py        # Advanced features demo
│   ├── typescript/
│   │   └── basic_usage.ts           # TypeScript example
│   └── enterprise/                   # Enterprise deployment examples
├── infra/
│   ├── kubernetes/
│   │   └── deployment.yaml          # K8s deployment manifests
│   ├── terraform/
│   │   ├── main.tf                  # Terraform main config
│   │   └── variables.tf             # Terraform variables
│   └── marketplace/                  # GCP Marketplace integration
├── scripts/
│   └── quickstart.sh                # Quick start script
├── src/
│   ├── baml_engine/
│   │   ├── __init__.py
│   │   └── validator.py             # BAML type validation
│   ├── billing/
│   │   ├── __init__.py
│   │   ├── usage_tracker.py         # Usage tracking
│   │   └── sync_worker.py           # Billing sync worker
│   ├── cache/
│   │   ├── __init__.py
│   │   ├── cache_aligner.py         # Cache optimization
│   │   └── redis_client.py          # Redis client
│   ├── gateway/
│   │   ├── __init__.py
│   │   ├── auth.py                  # Authentication
│   │   ├── config.py                # Configuration
│   │   ├── llm_client.py            # LLM provider client
│   │   ├── main.py                  # Main application
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py            # Health endpoints
│   │       └── proxy.py             # Proxy endpoints
│   ├── guardrails/
│   │   ├── __init__.py
│   │   ├── pii_detector.py          # PII detection
│   │   └── prompt_injection.py      # Injection detection
│   └── headroom/
│       ├── __init__.py
│       ├── compressor.py            # Compression engine
│       └── content_router.py        # Content routing
├── tests/
│   ├── integration/
│   │   └── test_api.py              # API integration tests
│   ├── performance/                  # Performance benchmarks
│   └── unit/
│       ├── test_baml_validator.py   # BAML tests
│       ├── test_compressor.py       # Compression tests
│       ├── test_pii_detector.py     # PII tests
│       └── test_prompt_injection.py # Injection tests
├── .dockerignore
├── .env.example                      # Environment template
├── .gitignore
├── CONTRIBUTING.md                   # Contributing guidelines
├── docker-compose.yml                # Docker Compose config
├── Dockerfile                        # Production Docker image
├── LICENSE                           # MIT License
├── pyproject.toml                    # Python project config
├── README.md                         # Main documentation
└── requirements.txt                  # Python dependencies
```

## Core Components

### Gateway Layer (`src/gateway/`)
- Main FastAPI application
- Request routing and middleware
- Authentication and authorization
- LLM provider integration

### BAML Engine (`src/baml_engine/`)
- Runtime type validation
- Prompt injection inoculation
- Output schema recovery

### Headroom (`src/headroom/`)
- Content-aware compression
- Code/JSON/Prose optimization
- Cache management

### Guardrails (`src/guardrails/`)
- PII detection and sanitization
- Prompt injection detection
- Security analysis

### Cache Layer (`src/cache/`)
- Redis client
- Cache alignment optimization
- Key-value store management

### Billing (`src/billing/`)
- Usage tracking
- Stripe integration
- Metrics synchronization

## Infrastructure

### Docker
- Production Dockerfile
- Docker Compose for local development
- Health checks and monitoring

### Kubernetes
- Deployment manifests
- Service definitions
- Horizontal pod autoscaling
- Health probes

### Terraform
- GCP Cloud Run deployment
- Redis (Memorystore)
- PostgreSQL (Cloud SQL)
- VPC networking

## Testing

### Unit Tests
- Component-level testing
- Mocked dependencies
- High coverage targets

### Integration Tests
- End-to-end API testing
- Real service integration
- Security validation

### Performance Tests
- Load testing
- Latency benchmarks
- Compression metrics

## Documentation

### API Reference
- OpenAI-compatible endpoints
- Perimeter-specific features
- Error handling

### Architecture
- System design
- Component interaction
- Data flow diagrams

### Deployment
- Local setup
- Cloud deployment
- Enterprise installation

## Examples

### Python
- Basic usage
- Advanced features
- SDK integration

### TypeScript
- OpenAI SDK compatibility
- Type definitions
- Best practices

### Enterprise
- VPC deployment
- Private marketplace
- Custom integrations
