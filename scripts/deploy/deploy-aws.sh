#!/bin/bash
set -e

# Perimeter AWS Deployment Script
# Deploys the complete infrastructure and application to AWS

echo "🚀 Perimeter AWS Deployment"
echo "=============================="
echo ""

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-production}"
ECR_REPO_NAME="perimeter-gateway"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Please install it first."
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install it first."
        exit 1
    fi
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        log_error "Terraform not found. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    
    log_info "✅ All prerequisites met"
}

create_terraform_backend() {
    log_info "Setting up Terraform backend..."
    
    # Create S3 bucket for Terraform state
    aws s3 mb s3://perimeter-terraform-state --region $AWS_REGION 2>/dev/null || log_warn "Bucket already exists"
    
    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket perimeter-terraform-state \
        --versioning-configuration Status=Enabled \
        --region $AWS_REGION
    
    # Enable encryption
    aws s3api put-bucket-encryption \
        --bucket perimeter-terraform-state \
        --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' \
        --region $AWS_REGION
    
    log_info "✅ Terraform backend ready"
}

build_and_push_image() {
    log_info "Building and pushing Docker image..."
    
    # Get AWS account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ECR_URL="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    
    # Create ECR repository if it doesn't exist
    aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $AWS_REGION 2>/dev/null || \
        aws ecr create-repository --repository-name $ECR_REPO_NAME --region $AWS_REGION
    
    # Login to ECR
    log_info "Logging in to ECR..."
    aws ecr get-login-password --region $AWS_REGION | \
        docker login --username AWS --password-stdin $ECR_URL
    
    # Build image
    log_info "Building Docker image..."
    docker build -t $ECR_REPO_NAME:latest -f Dockerfile .
    
    # Tag image
    docker tag $ECR_REPO_NAME:latest $ECR_URL/$ECR_REPO_NAME:latest
    docker tag $ECR_REPO_NAME:latest $ECR_URL/$ECR_REPO_NAME:$(git rev-parse --short HEAD)
    
    # Push image
    log_info "Pushing image to ECR..."
    docker push $ECR_URL/$ECR_REPO_NAME:latest
    docker push $ECR_URL/$ECR_REPO_NAME:$(git rev-parse --short HEAD)
    
    log_info "✅ Image pushed: $ECR_URL/$ECR_REPO_NAME:latest"
}

deploy_infrastructure() {
    log_info "Deploying infrastructure with Terraform..."
    
    cd infra/terraform/aws
    
    # Initialize Terraform
    terraform init
    
    # Plan
    log_info "Running Terraform plan..."
    terraform plan -out=tfplan
    
    # Apply
    log_info "Applying Terraform changes..."
    terraform apply tfplan
    
    # Save outputs
    terraform output -json > ../../../aws-outputs.json
    
    cd ../../..
    
    log_info "✅ Infrastructure deployed"
}

update_ecs_service() {
    log_info "Updating ECS service..."
    
    # Get cluster and service names from Terraform outputs
    CLUSTER_NAME=$(jq -r '.ecs_cluster_name.value' aws-outputs.json)
    SERVICE_NAME=$(jq -r '.ecs_service_name.value' aws-outputs.json)
    
    # Force new deployment
    aws ecs update-service \
        --cluster $CLUSTER_NAME \
        --service $SERVICE_NAME \
        --force-new-deployment \
        --region $AWS_REGION
    
    log_info "✅ ECS service updated"
}

wait_for_deployment() {
    log_info "Waiting for deployment to complete..."
    
    CLUSTER_NAME=$(jq -r '.ecs_cluster_name.value' aws-outputs.json)
    SERVICE_NAME=$(jq -r '.ecs_service_name.value' aws-outputs.json)
    
    aws ecs wait services-stable \
        --cluster $CLUSTER_NAME \
        --services $SERVICE_NAME \
        --region $AWS_REGION
    
    log_info "✅ Deployment complete"
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    ALB_DNS=$(jq -r '.alb_dns_name.value' aws-outputs.json)
    
    # Wait a bit for ALB to be ready
    sleep 10
    
    # Test health endpoint
    if curl -f "http://${ALB_DNS}/health" &> /dev/null; then
        log_info "✅ Health check passed"
    else
        log_warn "⚠️  Health check failed. Service may still be starting up."
    fi
}

print_summary() {
    echo ""
    echo "=============================="
    echo "🎉 Deployment Complete!"
    echo "=============================="
    echo ""
    
    ALB_DNS=$(jq -r '.alb_dns_name.value' aws-outputs.json)
    ECR_URL=$(jq -r '.ecr_repository_url.value' aws-outputs.json)
    REDIS_ENDPOINT=$(jq -r '.redis_endpoint.value' aws-outputs.json)
    RDS_ENDPOINT=$(jq -r '.rds_endpoint.value' aws-outputs.json)
    
    echo "📍 Endpoints:"
    echo "   Load Balancer: http://${ALB_DNS}"
    echo "   Health Check:  http://${ALB_DNS}/health"
    echo "   API Docs:      http://${ALB_DNS}/docs"
    echo ""
    echo "🐳 Resources:"
    echo "   ECR Repository: $ECR_URL"
    echo "   Redis Endpoint: $REDIS_ENDPOINT"
    echo "   RDS Endpoint:   $RDS_ENDPOINT"
    echo ""
    echo "📊 Monitoring:"
    echo "   ECS Console:    https://console.aws.amazon.com/ecs"
    echo "   CloudWatch:     https://console.aws.amazon.com/cloudwatch"
    echo ""
    echo "🔧 Next Steps:"
    echo "   1. Configure DNS (CNAME to $ALB_DNS)"
    echo "   2. Update SSL certificate"
    echo "   3. Configure environment secrets"
    echo "   4. Run integration tests"
    echo ""
}

# Main execution
main() {
    log_info "Starting AWS deployment..."
    
    check_prerequisites
    create_terraform_backend
    build_and_push_image
    deploy_infrastructure
    update_ecs_service
    wait_for_deployment
    verify_deployment
    print_summary
}

# Run main function
main
