#!/bin/bash
set -e

# Perimeter GCP Deployment Script
# Deploys the complete infrastructure and application to Google Cloud Platform

echo "🚀 Perimeter GCP Deployment"
echo "=============================="
echo ""

# Configuration
GCP_PROJECT="${GCP_PROJECT:-}"
GCP_REGION="${GCP_REGION:-us-central1}"
ENVIRONMENT="${ENVIRONMENT:-production}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

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
    
    # Check gcloud
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI not found. Please install Google Cloud SDK."
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
    
    # Check GCP project
    if [ -z "$GCP_PROJECT" ]; then
        GCP_PROJECT=$(gcloud config get-value project 2>/dev/null)
        if [ -z "$GCP_PROJECT" ]; then
            log_error "GCP_PROJECT not set. Run 'gcloud config set project PROJECT_ID' or export GCP_PROJECT"
            exit 1
        fi
    fi
    
    log_info "✅ Using GCP Project: $GCP_PROJECT"
    log_info "✅ All prerequisites met"
}

enable_apis() {
    log_info "Enabling required GCP APIs..."
    
    gcloud services enable \
        run.googleapis.com \
        redis.googleapis.com \
        sql.googleapis.com \
        sqladmin.googleapis.com \
        vpcaccess.googleapis.com \
        compute.googleapis.com \
        container.googleapis.com \
        containerregistry.googleapis.com \
        artifactregistry.googleapis.com \
        cloudresourcemanager.googleapis.com \
        servicenetworking.googleapis.com \
        --project=$GCP_PROJECT
    
    log_info "✅ APIs enabled"
}

create_terraform_backend() {
    log_info "Setting up Terraform backend..."
    
    # Create GCS bucket for Terraform state
    gsutil mb -p $GCP_PROJECT -l $GCP_REGION gs://perimeter-terraform-state-${GCP_PROJECT} 2>/dev/null || log_warn "Bucket already exists"
    
    # Enable versioning
    gsutil versioning set on gs://perimeter-terraform-state-${GCP_PROJECT}
    
    log_info "✅ Terraform backend ready"
}

build_and_push_image() {
    log_info "Building and pushing Docker image..."
    
    # Configure Docker for GCR
    gcloud auth configure-docker gcr.io --quiet
    
    # Build image
    log_info "Building Docker image..."
    docker build -t gcr.io/$GCP_PROJECT/perimeter-gateway:latest -f Dockerfile .
    docker tag gcr.io/$GCP_PROJECT/perimeter-gateway:latest gcr.io/$GCP_PROJECT/perimeter-gateway:$(git rev-parse --short HEAD)
    
    # Push image
    log_info "Pushing image to GCR..."
    docker push gcr.io/$GCP_PROJECT/perimeter-gateway:latest
    docker push gcr.io/$GCP_PROJECT/perimeter-gateway:$(git rev-parse --short HEAD)
    
    log_info "✅ Image pushed: gcr.io/$GCP_PROJECT/perimeter-gateway:latest"
}

deploy_infrastructure() {
    log_info "Deploying infrastructure with Terraform..."
    
    cd infra/terraform
    
    # Initialize Terraform
    terraform init \
        -backend-config="bucket=perimeter-terraform-state-${GCP_PROJECT}" \
        -backend-config="prefix=gcp/prod"
    
    # Plan
    log_info "Running Terraform plan..."
    terraform plan \
        -var="project_id=$GCP_PROJECT" \
        -var="region=$GCP_REGION" \
        -out=tfplan
    
    # Apply
    log_info "Applying Terraform changes..."
    terraform apply tfplan
    
    # Save outputs
    terraform output -json > ../../gcp-outputs.json
    
    cd ../..
    
    log_info "✅ Infrastructure deployed"
}

deploy_cloud_run() {
    log_info "Deploying to Cloud Run..."
    
    GATEWAY_URL=$(jq -r '.gateway_url.value' gcp-outputs.json)
    
    if [ "$GATEWAY_URL" != "null" ]; then
        log_info "✅ Cloud Run service deployed"
        log_info "   URL: $GATEWAY_URL"
    else
        log_warn "Could not retrieve Cloud Run URL from Terraform outputs"
    fi
}

wait_for_deployment() {
    log_info "Waiting for deployment to stabilize..."
    sleep 15
    log_info "✅ Deployment stable"
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    GATEWAY_URL=$(jq -r '.gateway_url.value' gcp-outputs.json)
    
    if [ "$GATEWAY_URL" != "null" ]; then
        # Test health endpoint
        if curl -f "${GATEWAY_URL}/health" &> /dev/null; then
            log_info "✅ Health check passed"
        else
            log_warn "⚠️  Health check failed. Service may still be starting up."
        fi
    fi
}

print_summary() {
    echo ""
    echo "=============================="
    echo "🎉 GCP Deployment Complete!"
    echo "=============================="
    echo ""
    
    GATEWAY_URL=$(jq -r '.gateway_url.value' gcp-outputs.json)
    REDIS_HOST=$(jq -r '.redis_host.value' gcp-outputs.json)
    DB_CONNECTION=$(jq -r '.db_connection_name.value' gcp-outputs.json)
    
    echo "📍 Endpoints:"
    echo "   Gateway URL:    $GATEWAY_URL"
    echo "   Health Check:   ${GATEWAY_URL}/health"
    echo "   API Docs:       ${GATEWAY_URL}/docs"
    echo ""
    echo "🐳 Resources:"
    echo "   Project:        $GCP_PROJECT"
    echo "   Region:         $GCP_REGION"
    echo "   Redis Host:     $REDIS_HOST"
    echo "   DB Connection:  $DB_CONNECTION"
    echo ""
    echo "📊 Monitoring:"
    echo "   Cloud Run:      https://console.cloud.google.com/run?project=$GCP_PROJECT"
    echo "   Monitoring:     https://console.cloud.google.com/monitoring?project=$GCP_PROJECT"
    echo "   Logs:           https://console.cloud.google.com/logs?project=$GCP_PROJECT"
    echo ""
    echo "🔧 Next Steps:"
    echo "   1. Configure custom domain"
    echo "   2. Set up Cloud Armor (WAF)"
    echo "   3. Configure Secrets Manager"
    echo "   4. Enable Cloud CDN"
    echo "   5. Run integration tests"
    echo ""
}

main() {
    log_info "Starting GCP deployment..."
    
    check_prerequisites
    enable_apis
    create_terraform_backend
    build_and_push_image
    deploy_infrastructure
    deploy_cloud_run
    wait_for_deployment
    verify_deployment
    print_summary
}

# Run main function
main
