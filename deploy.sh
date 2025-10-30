#!/bin/bash
# Konyali Optik Sayim Sistemi - Google Cloud Run Deploy Script

set -e

echo "========================================="
echo "Konyali Optik Sayim Sistemi - Deploy"
echo "========================================="
echo ""

# Configuration
PROJECT_ID=${GCLOUD_PROJECT_ID:-"your-project-id"}
SERVICE_NAME=${SERVICE_NAME:-"konyali-optik-sayim"}
REGION=${REGION:-"europe-west1"}
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "Project ID: $PROJECT_ID"
echo "Service Name: $SERVICE_NAME"
echo "Region: $REGION"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "ERROR: gcloud CLI not found. Please install it first."
    echo "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not found. Please install it first."
    exit 1
fi

echo "Step 1: Building Docker image..."
docker build -t ${IMAGE_NAME} .

echo ""
echo "Step 2: Pushing to Google Container Registry..."
docker push ${IMAGE_NAME}

echo ""
echo "Step 3: Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --port 5000 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars "FLASK_DEBUG=False" \
  --set-env-vars "ALLOWED_ORIGINS=*"

echo ""
echo "========================================="
echo "Deploy COMPLETED!"
echo "========================================="
echo ""
echo "IMPORTANT: Set environment variables in Cloud Run Console:"
echo "  - AIRTABLE_TOKEN"
echo "  - AIRTABLE_BASE_OPTIK"
echo "  - AIRTABLE_BASE_GUNES"
echo "  - AIRTABLE_BASE_LENS"
echo ""
echo "Cloud Run Console:"
echo "https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}/metrics"
echo ""
