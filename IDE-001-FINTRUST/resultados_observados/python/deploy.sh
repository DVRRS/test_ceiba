#!/bin/bash
set -e

# ========================================
# CONFIGURACIÓN - EDITAR ESTAS VARIABLES
# ========================================
PROJECT_ID="${PROJECT_ID:-tu-project-id}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-tu-servicio}"
IMAGE_NAME="${IMAGE_NAME:-$SERVICE_NAME}"
BQ_DATASET_RAW="${BQ_DATASET_RAW:-tu_dataset_raw}"
BQ_DATASET_CLEAN="${BQ_DATASET_CLEAN:-tu_dataset_clean}"
BQ_DATASET_REJECTS="${BQ_DATASET_REJECTS:-tu_dataset_rejects}"
BQ_DATASET_DATAMART="${BQ_DATASET_DATAMART:-tu_dataset_datamart}"
DEBUG="${DEBUG:-false}"

# Validar que las variables fueron configuradas
if [[ "$PROJECT_ID" == "tu-project-id" ]]; then
  echo "❌ Error: Debes configurar PROJECT_ID"
  echo "   Edita este script o exporta: export PROJECT_ID='tu-project-id'"
  exit 1
fi

if [[ "$SERVICE_NAME" == "tu-servicio" ]]; then
  echo "❌ Error: Debes configurar SERVICE_NAME"
  echo "   Edita este script o exporta: export SERVICE_NAME='tu-servicio'"
  exit 1
fi

echo "🚀 Desplegando a Cloud Run..."
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Service: $SERVICE_NAME"
echo ""

# 1. Build de imagen usando Cloud Build
echo "📦 Building imagen en Cloud Build..."
gcloud builds submit \
  --project=$PROJECT_ID \
  --tag gcr.io/$PROJECT_ID/$IMAGE_NAME \
  --timeout=10m

# 2. Deploy a Cloud Run
echo ""
echo "☁️  Deploying a Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --project=$PROJECT_ID \
  --image gcr.io/$PROJECT_ID/$IMAGE_NAME \
  --region=$REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID" \
  --set-env-vars "BQ_LOCATION=$REGION" \
  --set-env-vars "BQ_DATASET_RAW=$BQ_DATASET_RAW" \
  --set-env-vars "BQ_DATASET_CLEAN=$BQ_DATASET_CLEAN" \
  --set-env-vars "BQ_DATASET_REJECTS=$BQ_DATASET_REJECTS" \
  --set-env-vars "BQ_DATASET_DATAMART=$BQ_DATASET_DATAMART" \
  --set-env-vars "DEBUG=$DEBUG"

echo ""
echo "✅ Deploy completado!"
echo ""
echo "URL del servicio:"
gcloud run services describe $SERVICE_NAME \
  --project=$PROJECT_ID \
  --region=$REGION \
  --format='value(status.url)'
