# Perimeter AI Security Gateway
# Production Deployment Checklist
# October 23, 2026

---

# PRE-DEPLOYMENT CHECKLIST

## ☑️ Code Quality & Testing

### Unit Tests
- [ ] All unit tests passing (pytest tests/unit/)
  ```bash
  pytest tests/unit/ -v --cov=src --cov-report=html
  ```
  **Target:** >85% code coverage

- [ ] BAML validator tests (20 tests)
  ```bash
  pytest tests/unit/test_baml_validator.py -v
  ```

- [ ] PII detector tests (30 tests)
  ```bash
  pytest tests/unit/test_pii_detector.py -v
  ```

- [ ] Authentication tests (25 tests)
  ```bash
  pytest tests/unit/test_auth.py -v
  ```

- [ ] Rate limiter tests (15 tests)
  ```bash
  pytest tests/unit/test_rate_limiter.py -v
  ```

### Integration Tests
- [ ] E2E pipeline test passing
  ```bash
  PYTHONPATH=/workspace python3 tests/e2e_test.py
  ```

- [ ] API endpoint tests passing
  ```bash
  pytest tests/test_api_validation.py -v
  ```

### Code Quality
- [ ] No linting errors
  ```bash
  ruff check src/ tests/
  black --check src/ tests/
  ```

- [ ] Type checking passes
  ```bash
  mypy src/ --ignore-missing-imports
  ```

- [ ] No high-severity security issues
  ```bash
  bandit -r src/ -ll
  ```

---

## ☑️ Dependencies & Environment

### Python Dependencies
- [ ] All dependencies installed
  ```bash
  pip install -r requirements.txt
  ```

- [ ] spaCy models downloaded
  ```bash
  python -m spacy download en_core_web_sm
  ```

- [ ] No conflicting versions
  ```bash
  pip check
  ```

### Infrastructure Dependencies
- [ ] Redis accessible
  ```bash
  redis-cli ping
  ```
  **Expected:** PONG

- [ ] PostgreSQL accessible
  ```bash
  psql $DATABASE_URL -c "SELECT version();"
  ```
  **Expected:** PostgreSQL 15.x

- [ ] LLM provider APIs reachable
  ```bash
  curl -H "Authorization: Bearer $OPENAI_API_KEY" \
    https://api.openai.com/v1/models
  ```

---

## ☑️ Configuration & Secrets

### Environment Variables

**Critical (Must Set):**
- [ ] `JWT_SECRET` - Generate with `openssl rand -hex 32`
- [ ] `SECRET_KEY` - Generate with `openssl rand -hex 32`
- [ ] `OPENAI_API_KEY` - From OpenAI dashboard
- [ ] `ANTHROPIC_API_KEY` - From Anthropic dashboard
- [ ] `STRIPE_API_KEY` - From Stripe dashboard
- [ ] `STRIPE_WEBHOOK_SECRET` - From Stripe webhook settings
- [ ] `DATABASE_URL` - PostgreSQL connection string
- [ ] `REDIS_URL` - Redis connection string

**Optional (But Recommended):**
- [ ] `CLERK_SECRET_KEY` - For SaaS platform auth
- [ ] `GCP_PROJECT_ID` - For GCP deployment
- [ ] `SENTRY_DSN` - For error tracking
- [ ] `DATADOG_API_KEY` - For monitoring

### Verify Configuration
```bash
# Check all required env vars are set
python3 << 'EOF'
import os
required = [
    'JWT_SECRET',
    'SECRET_KEY',
    'OPENAI_API_KEY',
    'DATABASE_URL',
    'REDIS_URL'
]
missing = [var for var in required if not os.getenv(var)]
if missing:
    print(f"❌ Missing: {', '.join(missing)}")
    exit(1)
else:
    print("✅ All required env vars set")
EOF
```

---

## ☑️ Database Migrations

### PostgreSQL
- [ ] Database schema created
  ```bash
  alembic upgrade head
  ```

- [ ] Test data seeded (staging only)
  ```bash
  python scripts/seed_test_data.py
  ```

- [ ] Database backups configured
  ```bash
  # GCP: Automated backups enabled in Cloud SQL
  # AWS: RDS automated backups enabled
  ```

### Redis
- [ ] Redis persistence configured
  ```bash
  redis-cli CONFIG GET save
  ```
  **Expected:** `save 900 1 300 10 60 10000`

- [ ] Redis maxmemory policy set
  ```bash
  redis-cli CONFIG GET maxmemory-policy
  ```
  **Expected:** `allkeys-lru`

---

## ☑️ Security Hardening

### Network Security
- [ ] VPC firewall rules configured
  - Allow: Your IPs → Gateway (port 8000)
  - Allow: Gateway → Redis (port 6379)
  - Allow: Gateway → PostgreSQL (port 5432)
  - Allow: Gateway → OpenAI/Anthropic APIs
  - Deny: All other inbound traffic

- [ ] TLS/SSL certificates configured
  ```bash
  curl -I https://your-domain.com/health
  ```
  **Check:** Certificate valid and not self-signed

- [ ] API rate limiting enabled
  ```python
  # Verify in src/gateway/main.py
  # app.state.rate_limiter is initialized
  ```

### Application Security
- [ ] No default/test credentials in production
  ```bash
  # Check for test keys
  grep -r "test_key\|example\|changeme" src/ config/
  ```
  **Expected:** No matches

- [ ] CORS configured correctly
  ```bash
  # Verify ALLOWED_ORIGINS in .env
  # Should NOT be ["*"] in production
  ```

- [ ] Security headers configured
  - [ ] X-Frame-Options: DENY
  - [ ] X-Content-Type-Options: nosniff
  - [ ] Strict-Transport-Security (HSTS)

### Secret Management
- [ ] Secrets stored in secret manager (not .env file)
  ```bash
  # GCP: Secret Manager
  # AWS: Secrets Manager or Parameter Store
  ```

- [ ] Secrets rotated within last 90 days

- [ ] No secrets in git history
  ```bash
  git log --all --full-history -- "*secret*" "*key*"
  ```

---

## ☑️ Monitoring & Observability

### Logging
- [ ] Structured logging configured
  ```python
  # Verify JSON logging in production
  LOG_FORMAT=json python -c "import logging; logging.basicConfig()"
  ```

- [ ] Log aggregation configured
  - GCP: Cloud Logging
  - AWS: CloudWatch Logs
  - Self-hosted: ELK/Loki

- [ ] Log retention policy set (30-90 days)

### Metrics
- [ ] Prometheus metrics endpoint accessible
  ```bash
  curl http://localhost:9090/metrics
  ```
  **Expected:** Prometheus-formatted metrics

- [ ] Key metrics tracked:
  - [ ] Request rate (requests/sec)
  - [ ] Error rate (errors/sec)
  - [ ] Request latency (p50, p95, p99)
  - [ ] PII detection rate
  - [ ] Compression ratio
  - [ ] Token usage

### Alerting
- [ ] Alerts configured for:
  - [ ] Error rate > 1%
  - [ ] Latency p99 > 500ms
  - [ ] Redis unavailable
  - [ ] PostgreSQL unavailable
  - [ ] LLM API errors > 5%
  - [ ] Rate limit abuse detected

### Tracing
- [ ] Distributed tracing enabled (optional)
  ```bash
  # OpenTelemetry configured
  # Jaeger/Zipkin/Datadog APM
  ```

---

## ☑️ Performance & Scalability

### Load Testing
- [ ] Load test completed
  ```bash
  # Example with locust
  locust -f tests/load_test.py --host=https://staging.example.com
  ```
  **Target:**
  - 100 RPS without errors
  - p99 latency < 500ms
  - No memory leaks

- [ ] Stress test completed (2x expected load)

- [ ] Spike test completed (10x sudden spike)

### Resource Limits
- [ ] Memory limit configured (2GB per instance)
  ```yaml
  # Kubernetes: resources.limits.memory
  # Cloud Run: --memory=2Gi
  # ECS: memoryReservation
  ```

- [ ] CPU limit configured (1-2 vCPU per instance)

- [ ] Auto-scaling configured
  - Min replicas: 2
  - Max replicas: 10
  - Target CPU: 70%
  - Target memory: 80%

### Caching
- [ ] Redis caching configured
  - TTL: 1 hour for compression cache
  - Max keys: 1M

- [ ] HTTP caching headers set
  ```bash
  curl -I https://your-domain.com/health
  ```
  **Check:** Cache-Control header present

---

## ☑️ Disaster Recovery

### Backups
- [ ] Database backups automated
  - Frequency: Daily
  - Retention: 30 days
  - Tested recovery: Last 7 days

- [ ] Configuration backups
  ```bash
  # Backup .env, k8s configs, terraform state
  ```

### Rollback Plan
- [ ] Previous version image tagged and available
  ```bash
  # GCR: gcr.io/PROJECT/perimeter:v1.0.0
  # ECR: ACCOUNT.dkr.ecr.REGION.amazonaws.com/perimeter:v1.0.0
  ```

- [ ] Rollback procedure documented
  ```bash
  # Kubernetes: kubectl rollout undo deployment/perimeter-gateway
  # Cloud Run: gcloud run services update --image=OLD_IMAGE
  # ECS: aws ecs update-service --task-definition=OLD_TASK_DEF
  ```

- [ ] Rollback tested in staging

### Incident Response
- [ ] On-call rotation configured

- [ ] Runbooks created:
  - [ ] High error rate
  - [ ] High latency
  - [ ] Database failure
  - [ ] Redis failure
  - [ ] PII leak incident

- [ ] Contact list maintained
  - [ ] Engineering leads
  - [ ] Security team
  - [ ] Legal team (for PII incidents)

---

# DEPLOYMENT STEPS

## 🚀 Staging Deployment

### 1. Pre-Deployment Validation
```bash
# Run all tests
pytest tests/ -v --cov=src

# Check environment
./scripts/check_environment.sh staging

# Verify secrets
./scripts/verify_secrets.sh staging
```

### 2. Deploy to Staging

**Option A: GCP Cloud Run**
```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/perimeter:v2.0.0

# Deploy to Cloud Run
gcloud run deploy perimeter-gateway \
  --image gcr.io/PROJECT_ID/perimeter:v2.0.0 \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "$(cat .env.staging)" \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10
```

**Option B: AWS ECS**
```bash
# Build and push image
aws ecr get-login-password | docker login --username AWS \
  --password-stdin ACCOUNT.dkr.ecr.REGION.amazonaws.com

docker build -t perimeter:v2.0.0 .
docker tag perimeter:v2.0.0 ACCOUNT.dkr.ecr.REGION.amazonaws.com/perimeter:v2.0.0
docker push ACCOUNT.dkr.ecr.REGION.amazonaws.com/perimeter:v2.0.0

# Update ECS service
aws ecs update-service \
  --cluster perimeter-staging \
  --service perimeter-gateway \
  --task-definition perimeter-gateway-v2 \
  --force-new-deployment
```

**Option C: Kubernetes**
```bash
# Build and push image
docker build -t perimeter:v2.0.0 .
docker tag perimeter:v2.0.0 YOUR_REGISTRY/perimeter:v2.0.0
docker push YOUR_REGISTRY/perimeter:v2.0.0

# Update deployment
kubectl set image deployment/perimeter-gateway \
  gateway=YOUR_REGISTRY/perimeter:v2.0.0

# Monitor rollout
kubectl rollout status deployment/perimeter-gateway
```

### 3. Post-Deployment Verification (Staging)
```bash
# Health check
curl https://staging.your-domain.com/health
# Expected: {"status": "healthy"}

# Readiness check
curl https://staging.your-domain.com/ready
# Expected: {"status": "ready", "dependencies": {...}}

# Test chat completions endpoint
curl -X POST https://staging.your-domain.com/v1/chat/completions \
  -H "X-Perimeter-API-Key: pmtr_test_..." \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Test email@example.com"}]
  }'
# Expected: PII sanitized response

# Check metrics
curl https://staging.your-domain.com/metrics
# Expected: Prometheus metrics

# Monitor logs
# GCP: gcloud logging read "resource.type=cloud_run_revision"
# AWS: aws logs tail /aws/ecs/perimeter-gateway --follow
# K8s: kubectl logs -f deployment/perimeter-gateway
```

### 4. Staging Smoke Tests
- [ ] Authentication works (API key + JWT)
- [ ] PII detection sanitizes data
- [ ] Compression reduces payload size
- [ ] Rate limiting triggers correctly
- [ ] Type validation rejects invalid input
- [ ] Error responses are properly formatted
- [ ] Metrics are being collected

### 5. Staging Soak Test (24-48 hours)
- [ ] No memory leaks (memory stable over time)
- [ ] No connection leaks (DB/Redis connections stable)
- [ ] Error rate < 0.1%
- [ ] Latency p99 < 500ms
- [ ] No crashes or restarts

---

## 🚀 Production Deployment

### 1. Production Readiness Review
- [ ] All staging tests passed
- [ ] Soak test completed (24-48 hours)
- [ ] Load test passed (2x expected traffic)
- [ ] Security review completed
- [ ] All checklist items above completed
- [ ] Deployment window scheduled (off-peak hours)
- [ ] Rollback plan documented and tested
- [ ] On-call team notified

### 2. Pre-Deployment Steps
```bash
# Tag production release
git tag -a v2.0.0 -m "Production release: Technical debt fixes"
git push origin v2.0.0

# Create database backup
# GCP: gcloud sql backups create --instance=INSTANCE
# AWS: aws rds create-db-snapshot

# Verify rollback image is available
# GCP: gcloud container images list --repository=gcr.io/PROJECT_ID/perimeter
# AWS: aws ecr describe-images --repository-name perimeter

# Announce deployment (Slack, email, status page)
```

### 3. Deploy to Production

**Blue-Green Deployment (Recommended)**
```bash
# Deploy to "green" environment
# Run health checks
# Switch traffic gradually (10% → 50% → 100%)
# Monitor metrics at each step
# Keep "blue" running for quick rollback
```

**Rolling Deployment**
```bash
# Update instances one at a time
# Wait for health check before next instance
# Monitor error rate and latency
```

### 4. Production Verification

**Immediately After Deployment:**
```bash
# Health check
curl https://api.your-domain.com/health

# Test authenticated endpoint
curl -X POST https://api.your-domain.com/v1/chat/completions \
  -H "X-Perimeter-API-Key: pmtr_live_..." \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4", "messages": [...]}'

# Check error rate (should be < 0.1%)
# Check latency (p99 should be < 500ms)
# Check PII detection (should be sanitizing)
```

**Within First Hour:**
- [ ] No increase in error rate
- [ ] No increase in latency
- [ ] No customer complaints
- [ ] Metrics look normal
- [ ] Logs show no errors
- [ ] PII detection working
- [ ] Rate limiting working

**Within First 24 Hours:**
- [ ] Monitor for memory leaks
- [ ] Monitor for connection leaks
- [ ] Check backup success
- [ ] Review security logs
- [ ] Check for any abuse patterns

### 5. Post-Deployment Communication
- [ ] Update status page (deployment complete)
- [ ] Notify stakeholders (success/issues)
- [ ] Update documentation (if API changes)
- [ ] Post-mortem if issues occurred

---

# POST-DEPLOYMENT MONITORING

## 📊 Key Metrics to Monitor (First Week)

### Application Metrics
- **Request Rate:** Requests/second per endpoint
- **Error Rate:** Errors/second (target: < 0.1%)
- **Latency:**
  - p50 (median): < 50ms
  - p95: < 200ms
  - p99: < 500ms
- **PII Detection Rate:** % of requests with PII detected
- **Compression Ratio:** Average % reduction
- **Token Usage:** Tokens saved per request

### Infrastructure Metrics
- **CPU Usage:** < 70% average
- **Memory Usage:** < 80% average
- **Redis Hit Rate:** > 80%
- **Database Connections:** Stable (no leaks)
- **Network Bandwidth:** Within budget

### Business Metrics
- **Active Tenants:** Number using the service
- **API Key Usage:** Distribution by tier
- **Rate Limit Hits:** # of rate limit rejections
- **Abuse Incidents:** # of abuse pattern detections

---

## 🚨 Rollback Triggers

**Immediate Rollback If:**
- Error rate > 5%
- Latency p99 > 2000ms (2 seconds)
- PII leaking to LLM providers (critical security issue)
- Critical dependency failure (Redis, Database)
- Data loss or corruption

**Consider Rollback If:**
- Error rate > 1% for > 15 minutes
- Latency p99 > 1000ms for > 15 minutes
- Memory leak detected (memory constantly increasing)
- Connection leak detected
- More than 3 critical bugs reported

---

## 🔄 Rollback Procedure

### Automated Rollback
```bash
# GCP Cloud Run
gcloud run services update-traffic perimeter-gateway \
  --to-revisions PREVIOUS_REVISION=100

# AWS ECS
aws ecs update-service \
  --service perimeter-gateway \
  --task-definition PREVIOUS_TASK_DEF

# Kubernetes
kubectl rollout undo deployment/perimeter-gateway
```

### Manual Rollback Steps
1. Announce rollback started
2. Execute rollback command
3. Verify health checks pass
4. Monitor error rate (should decrease)
5. Monitor latency (should decrease)
6. Announce rollback complete
7. Investigate root cause
8. Plan fix deployment

---

# SIGN-OFF

## Deployment Approval

**Date:** ________________  
**Version:** v2.0.0  
**Environment:** □ Staging  □ Production

### Sign-Off Required From:

- [ ] **Engineering Lead:** _____________________  
      Verified: Tests pass, code quality good

- [ ] **Security Lead:** _____________________  
      Verified: Security review complete, no vulnerabilities

- [ ] **Operations Lead:** _____________________  
      Verified: Infrastructure ready, monitoring configured

- [ ] **Product Owner:** _____________________  
      Approved: Ready for customer use

### Deployment Executed By:

**Name:** _____________________  
**Date/Time:** _____________________  
**Result:** □ Success  □ Rolled Back  
**Notes:** _____________________________________________________

---

# APPENDIX: Quick Reference

## Useful Commands

### Check Service Status
```bash
# GCP
gcloud run services describe perimeter-gateway --region us-central1

# AWS
aws ecs describe-services --cluster perimeter --services perimeter-gateway

# Kubernetes
kubectl get deployment perimeter-gateway -o wide
```

### View Logs
```bash
# GCP
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# AWS
aws logs tail /aws/ecs/perimeter-gateway --follow

# Kubernetes
kubectl logs -f deployment/perimeter-gateway
```

### Check Metrics
```bash
# Prometheus
curl http://localhost:9090/metrics | grep perimeter_

# Dashboard
# GCP: Cloud Monitoring dashboard
# AWS: CloudWatch dashboard
```

### Emergency Contacts
- Engineering On-Call: [phone/slack]
- Security Team: [email/slack]
- DevOps Team: [phone/slack]

---

**Checklist Version:** 2.0  
**Last Updated:** October 23, 2026  
**Next Review:** November 23, 2026
