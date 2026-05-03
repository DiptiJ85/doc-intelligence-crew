#!/bin/bash

set -e

PROJECT_ID="document-intelligence-crew"
REGION="us-east1"
REGISTRY="us-east1-docker.pkg.dev/$PROJECT_ID/doc-intelligence"
PROJECT_NUMBER="391346508447"
SERVICE_ACCOUNT="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

echo "🚀 Starting deployment..."
echo "Project: $PROJECT_ID"
echo "Region:  $REGION"
echo ""

# ── Step 1: Grant permissions ─────────────────────────
echo "🔐 Granting IAM permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/storage.objectAdmin"

echo "✅ Permissions granted"

# ── Step 2: Build images ──────────────────────────────
echo ""
echo "📦 Building Docker images..."
docker build -f Dockerfile.api -t doc-intelligence-api .
docker build -f Dockerfile.streamlit -t doc-intelligence-streamlit .
echo "✅ Images built"

# ── Step 3: Tag images ────────────────────────────────
echo ""
echo "🏷️  Tagging images..."
docker tag doc-intelligence-api $REGISTRY/api:latest
docker tag doc-intelligence-streamlit $REGISTRY/streamlit:latest
echo "✅ Images tagged"

# ── Step 4: Push images ───────────────────────────────
echo ""
echo "⬆️  Pushing images to Artifact Registry..."
docker push $REGISTRY/api:latest
docker push $REGISTRY/streamlit:latest
echo "✅ Images pushed"

# ── Step 5: Deploy FastAPI ────────────────────────────
echo ""
echo "🌐 Deploying FastAPI to Cloud Run..."
gcloud run deploy doc-intelligence-api \
    --image=$REGISTRY/api:latest \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --port=8000 \
    --memory=2Gi \
    --cpu=2 \
    --min-instances=1 \
    --set-secrets=GEMINI_API_KEY=GEMINI_API_KEY:latest,GOOGLE_API_KEY=GOOGLE_API_KEY:latest,PINECONE_API_KEY=PINECONE_API_KEY:latest,CHROMA_GOOGLE_GENAI_API_KEY=CHROMA_GOOGLE_GENAI_API_KEY:latest \
    --set-env-vars=PINECONE_INDEX=doc-intelligence \
    --project=$PROJECT_ID

API_URL=$(gcloud run services describe doc-intelligence-api \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(status.url)")
echo "✅ FastAPI deployed: $API_URL"

# ── Step 6: Deploy Streamlit ──────────────────────────
echo ""
echo "🎨 Deploying Streamlit to Cloud Run..."
gcloud run deploy doc-intelligence-streamlit \
    --image=$REGISTRY/streamlit:latest \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --port=8501 \
    --memory=1Gi \
    --cpu=1 \
    --set-env-vars=API_BASE=$API_URL \
    --project=$PROJECT_ID

STREAMLIT_URL=$(gcloud run services describe doc-intelligence-streamlit \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(status.url)")

# ── Done ──────────────────────────────────────────────
echo ""
echo "🎉 Deployment complete!"
echo "================================"
echo "FastAPI URL:   $API_URL"
echo "Streamlit URL: $STREAMLIT_URL"
echo "================================"