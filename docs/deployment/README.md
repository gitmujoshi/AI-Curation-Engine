# Deployment Guide

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- GCP SDK (for cloud deployment)
- Terraform 1.5+

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/perimeter.git
cd perimeter
```

### 2. Create Environment File

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start Services with Docker Compose

```bash
docker-compose up -d
```

This starts:
- Gateway (port 8000)
- Redis (port 6379)
- PostgreSQL (port 5432)
- Prometheus (port 9090)

### 4. Verify Installation

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development"
}
```

### 5. Test API

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Perimeter-API-Key: pmtr_live_test_key_12345" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

## GCP Cloud Run Deployment

### 1. Setup GCP Project

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  redis.googleapis.com \
  sql.googleapis.com \
  vpcaccess.googleapis.com
```

### 2. Build and Push Docker Image

```bash
# Build image
docker build -t gcr.io/YOUR_PROJECT_ID/perimeter-gateway:latest .

# Push to GCR
docker push gcr.io/YOUR_PROJECT_ID/perimeter-gateway:latest
```

### 3. Deploy with Terraform

```bash
cd infra/terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan \
  -var="project_id=YOUR_PROJECT_ID" \
  -var="region=us-central1"

# Apply changes
terraform apply \
  -var="project_id=YOUR_PROJECT_ID" \
  -var="region=us-central1"
```

### 4. Configure Secrets

```bash
# Create secrets in Secret Manager
gcloud secrets create perimeter-openai-key \
  --data-file=- <<< "YOUR_OPENAI_API_KEY"

gcloud secrets create perimeter-anthropic-key \
  --data-file=- <<< "YOUR_ANTHROPIC_API_KEY"

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding perimeter-openai-key \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"
```

### 5. Verify Deployment

```bash
# Get Cloud Run URL
GATEWAY_URL=$(terraform output -raw gateway_url)

# Test endpoint
curl $GATEWAY_URL/health
```

## GKE Deployment

### 1. Create GKE Cluster

```bash
gcloud container clusters create perimeter-cluster \
  --region us-central1 \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --enable-autoscaling \
  --min-nodes 3 \
  --max-nodes 20
```

### 2. Configure kubectl

```bash
gcloud container clusters get-credentials perimeter-cluster \
  --region us-central1
```

### 3. Create Namespace

```bash
kubectl create namespace perimeter
```

### 4. Create Secrets

```bash
kubectl create secret generic perimeter-secrets \
  --namespace=perimeter \
  --from-literal=redis-url="redis://REDIS_HOST:6379/0" \
  --from-literal=database-url="postgresql+asyncpg://USER:PASS@HOST:5432/perimeter" \
  --from-literal=secret-key="YOUR_SECRET_KEY" \
  --from-literal=openai-api-key="YOUR_OPENAI_KEY" \
  --from-literal=anthropic-api-key="YOUR_ANTHROPIC_KEY"
```

### 5. Deploy Application

```bash
kubectl apply -f infra/kubernetes/deployment.yaml
```

### 6. Check Status

```bash
kubectl get pods -n perimeter
kubectl get svc -n perimeter
kubectl logs -f deployment/perimeter-gateway -n perimeter
```

### 7. Get External IP

```bash
kubectl get svc perimeter-gateway -n perimeter
```

## GCP Marketplace Deployment (Enterprise)

### For End Users

1. Visit [GCP Marketplace - Perimeter Gateway]
2. Click "Get Started"
3. Select your GCP project
4. Configure:
   - Region
   - Instance size
   - VPC network
5. Click "Deploy"
6. Access gateway at provided endpoint

### For Publishers (Perimeter Team)

1. Package application as container image
2. Create deployer image with Terraform config
3. Submit to GCP Marketplace Partner Portal
4. Configure pricing (usage-based)
5. Submit for review

## Environment Variables

See `.env.example` for complete list. Key variables:

### Required
- `REDIS_URL` - Redis connection string
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Application secret key
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key

### Optional
- `ENVIRONMENT` - dev/staging/prod
- `LOG_LEVEL` - DEBUG/INFO/WARNING/ERROR
- `COMPRESSION_ENABLED` - Enable Headroom compression
- `PII_DETECTION_ENABLED` - Enable PII detection

## Monitoring Setup

### Prometheus

```bash
# Access Prometheus UI
kubectl port-forward -n perimeter svc/prometheus 9090:9090

# Open http://localhost:9090
```

### Grafana

```bash
# Install Grafana
helm repo add grafana https://grafana.github.io/helm-charts
helm install grafana grafana/grafana -n perimeter

# Get admin password
kubectl get secret --namespace perimeter grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode

# Port forward
kubectl port-forward -n perimeter svc/grafana 3000:80
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs gateway

# Or in Kubernetes
kubectl logs -f deployment/perimeter-gateway -n perimeter
```

### Redis Connection Fails

```bash
# Test Redis connection
redis-cli -h REDIS_HOST ping

# Check network connectivity
kubectl exec -it POD_NAME -n perimeter -- ping REDIS_HOST
```

### Database Migration Issues

```bash
# Run migrations manually
docker-compose exec gateway python -m alembic upgrade head
```

### Performance Issues

- Check Prometheus metrics at `/metrics`
- Review Cloud Run/GKE resource limits
- Scale up replicas if needed:
  ```bash
  kubectl scale deployment perimeter-gateway -n perimeter --replicas=10
  ```

## Security Best Practices

1. **Use Secret Manager**: Never commit secrets to git
2. **Enable VPC**: Deploy in private network
3. **Restrict IAM**: Principle of least privilege
4. **Enable Audit Logs**: Track all admin actions
5. **Use TLS**: Enable HTTPS for all endpoints
6. **Rate Limiting**: Configure appropriate limits
7. **Regular Updates**: Keep dependencies patched

## Backup & Disaster Recovery

### PostgreSQL Backups

```bash
# Automated daily backups enabled in Terraform
# Manual backup:
gcloud sql backups create \
  --instance=perimeter-db \
  --description="Manual backup"
```

### Redis Backups

```bash
# Redis persistence configured with AOF
# Manual snapshot:
redis-cli -h REDIS_HOST BGSAVE
```

### Restore Procedure

1. Provision new infrastructure
2. Restore database from backup
3. Update DNS to new endpoint
4. Verify functionality
5. Monitor metrics
