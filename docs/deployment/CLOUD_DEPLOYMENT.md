# Perimeter Deployment Guide

Complete deployment instructions for AWS and GCP.

## Prerequisites

### General
- Docker installed and running
- Git installed
- Terraform >= 1.5
- curl and jq

### AWS Deployment
- AWS CLI installed and configured
- AWS account with appropriate permissions
- SSL certificate in ACM (for HTTPS)

### GCP Deployment
- Google Cloud SDK installed and configured
- GCP project created
- Billing enabled on project

## Quick Deployment

### AWS Deployment

```bash
# Set environment variables
export AWS_REGION=us-east-1
export ENVIRONMENT=production
export TF_VAR_db_password="your-secure-password"
export TF_VAR_certificate_arn="arn:aws:acm:..."
export TF_VAR_openai_api_key="sk-..."
export TF_VAR_anthropic_api_key="sk-ant-..."

# Run deployment script
./scripts/deploy/deploy-aws.sh
```

### GCP Deployment

```bash
# Set environment variables
export GCP_PROJECT=your-project-id
export GCP_REGION=us-central1
export ENVIRONMENT=production

# Run deployment script
./scripts/deploy/deploy-gcp.sh
```

## Manual Deployment Steps

### AWS Manual Deployment

#### 1. Prepare Infrastructure

```bash
cd infra/terraform/aws

# Initialize Terraform
terraform init

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
region = "us-east-1"
environment = "production"
db_password = "your-secure-password"
certificate_arn = "arn:aws:acm:us-east-1:..."
openai_api_key = "sk-..."
anthropic_api_key = "sk-ant-..."
EOF

# Plan and apply
terraform plan
terraform apply
```

#### 2. Build and Push Docker Image

```bash
# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=us-east-1

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Build and push
docker build -t perimeter-gateway:latest .
docker tag perimeter-gateway:latest \
    ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/perimeter-gateway:latest
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/perimeter-gateway:latest
```

#### 3. Deploy ECS Service

```bash
# Force new deployment
aws ecs update-service \
    --cluster perimeter-cluster \
    --service perimeter-gateway \
    --force-new-deployment \
    --region $AWS_REGION
```

#### 4. Verify Deployment

```bash
# Get ALB DNS name
ALB_DNS=$(terraform output -raw alb_dns_name)

# Test health endpoint
curl http://${ALB_DNS}/health
```

### GCP Manual Deployment

#### 1. Enable APIs

```bash
gcloud services enable \
    run.googleapis.com \
    redis.googleapis.com \
    sql.googleapis.com \
    vpcaccess.googleapis.com \
    --project=YOUR_PROJECT_ID
```

#### 2. Prepare Infrastructure

```bash
cd infra/terraform

# Initialize Terraform
terraform init

# Plan and apply
terraform plan -var="project_id=YOUR_PROJECT_ID"
terraform apply -var="project_id=YOUR_PROJECT_ID"
```

#### 3. Build and Push Docker Image

```bash
export GCP_PROJECT=your-project-id

# Configure Docker
gcloud auth configure-docker gcr.io

# Build and push
docker build -t gcr.io/$GCP_PROJECT/perimeter-gateway:latest .
docker push gcr.io/$GCP_PROJECT/perimeter-gateway:latest
```

#### 4. Verify Deployment

```bash
# Get Cloud Run URL
GATEWAY_URL=$(terraform output -raw gateway_url)

# Test health endpoint
curl ${GATEWAY_URL}/health
```

## Post-Deployment Configuration

### AWS

#### Configure DNS
```bash
# Create Route 53 record pointing to ALB
aws route53 change-resource-record-sets \
    --hosted-zone-id YOUR_ZONE_ID \
    --change-batch '{
        "Changes": [{
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "api.perimeter.ai",
                "Type": "A",
                "AliasTarget": {
                    "HostedZoneId": "YOUR_ALB_ZONE_ID",
                    "DNSName": "YOUR_ALB_DNS",
                    "EvaluateTargetHealth": true
                }
            }
        }]
    }'
```

#### Configure Secrets
```bash
# Create secrets in Secrets Manager
aws secretsmanager create-secret \
    --name perimeter/openai-key \
    --secret-string "sk-..." \
    --region $AWS_REGION

aws secretsmanager create-secret \
    --name perimeter/anthropic-key \
    --secret-string "sk-ant-..." \
    --region $AWS_REGION
```

### GCP

#### Configure Custom Domain
```bash
# Map custom domain to Cloud Run
gcloud run services update perimeter-gateway \
    --platform managed \
    --region $GCP_REGION \
    --add-custom-domain api.perimeter.ai
```

#### Configure Secrets
```bash
# Create secrets in Secret Manager
echo -n "sk-..." | gcloud secrets create openai-key \
    --data-file=- \
    --replication-policy=automatic

echo -n "sk-ant-..." | gcloud secrets create anthropic-key \
    --data-file=- \
    --replication-policy=automatic
```

## Monitoring & Logging

### AWS CloudWatch

```bash
# View ECS logs
aws logs tail /ecs/perimeter-gateway --follow

# View metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/ECS \
    --metric-name CPUUtilization \
    --dimensions Name=ServiceName,Value=perimeter-gateway \
    --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average
```

### GCP Cloud Logging

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision" \
    --project=$GCP_PROJECT \
    --limit=50 \
    --format=json

# Stream logs
gcloud alpha run services logs tail perimeter-gateway \
    --region=$GCP_REGION
```

## Scaling Configuration

### AWS Auto Scaling

Edit `infra/terraform/aws/main.tf`:

```hcl
resource "aws_appautoscaling_target" "ecs" {
  min_capacity = 3    # Minimum tasks
  max_capacity = 20   # Maximum tasks
}
```

### GCP Cloud Run Scaling

```bash
# Update min/max instances
gcloud run services update perimeter-gateway \
    --platform managed \
    --region $GCP_REGION \
    --min-instances 3 \
    --max-instances 100
```

## Cost Optimization

### AWS

- Use Spot Instances for non-critical workloads
- Enable S3 Intelligent-Tiering for logs
- Use Reserved Instances for RDS
- Enable CloudWatch Logs retention policies

### GCP

- Use committed use discounts
- Enable Cloud CDN for static content
- Use regional persistent disk
- Set appropriate Cloud Run timeout values

## Troubleshooting

### AWS

```bash
# Check ECS task status
aws ecs describe-tasks \
    --cluster perimeter-cluster \
    --tasks $(aws ecs list-tasks --cluster perimeter-cluster --query 'taskArns[0]' --output text)

# Check ALB health
aws elbv2 describe-target-health \
    --target-group-arn $(terraform output -raw target_group_arn)
```

### GCP

```bash
# Check Cloud Run service status
gcloud run services describe perimeter-gateway \
    --region=$GCP_REGION \
    --format=yaml

# Check recent errors
gcloud logging read "severity>=ERROR" \
    --limit=10 \
    --format=json
```

## Rollback Procedures

### AWS

```bash
# Rollback to previous task definition
aws ecs update-service \
    --cluster perimeter-cluster \
    --service perimeter-gateway \
    --task-definition perimeter-gateway:PREVIOUS_REVISION
```

### GCP

```bash
# Rollback to previous revision
gcloud run services update-traffic perimeter-gateway \
    --to-revisions=PREVIOUS_REVISION=100 \
    --region=$GCP_REGION
```

## Security Hardening

### AWS

- Enable GuardDuty
- Configure AWS WAF rules
- Enable VPC Flow Logs
- Use Systems Manager Parameter Store for secrets
- Enable RDS encryption at rest

### GCP

- Enable Cloud Armor
- Configure Identity-Aware Proxy
- Enable VPC Flow Logs
- Use Secret Manager for secrets
- Enable Cloud SQL encryption

## Disaster Recovery

### AWS

```bash
# Enable automated backups
aws rds modify-db-instance \
    --db-instance-identifier perimeter-db \
    --backup-retention-period 7 \
    --preferred-backup-window "03:00-04:00"

# Create snapshot
aws rds create-db-snapshot \
    --db-instance-identifier perimeter-db \
    --db-snapshot-identifier perimeter-snapshot-$(date +%Y%m%d)
```

### GCP

```bash
# Configure backup
gcloud sql instances patch perimeter-db \
    --backup-start-time=03:00 \
    --enable-bin-log

# Create on-demand backup
gcloud sql backups create \
    --instance=perimeter-db
```

## Support

For deployment issues:
- AWS: Check CloudWatch Logs
- GCP: Check Cloud Logging
- Review Terraform state: `terraform show`
- Check service health: `curl https://your-domain/health`

---

**Last Updated:** July 4, 2026  
**Version:** 1.0.0
