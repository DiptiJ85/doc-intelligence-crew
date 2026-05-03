#!/bin/bash

set -e  # stop on any error

PROJECT_ID="document-intelligence-crew"
REGION="us-east1"
REGISTRY="us-east1-docker.pkg.dev/$PROJECT_ID/doc-intelligence"

echo "🚀 Starting deployment..."
echo "Project: $PROJECT_ID"
echo "Region:  $REGION"
echo ""

# ── Step 1: Build images ──────────────────────────────
echo "📦 Building Docker images..."
docker build -f Dockerfile.api -t doc-intelligence-api .
docker build -f Dockerfile.streamlit -t doc-intelligence-streamlit .
echo "✅ Images built"

# ── Step 2: Tag images ────────────────────────────────
echo ""
echo "🏷️  Tagging images..."
docker tag doc-intelligence-api $REGISTRY/api:latest
docker tag doc-intelligence-streamlit $REGISTRY/streamlit:latest
echo "✅ Images tagged"

# ── Step 3: Push images ───────────────────────────────
echo ""
echo "⬆️  Pushing images to Artifact Registry..."
docker push $REGISTRY/api:latest
docker push $REGISTRY/streamlit:latest
echo "✅ Images pushed"

# ── Step 4: Deploy FastAPI ────────────────────────────
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

# get FastAPI URL
API_URL=$(gcloud run services describe doc-intelligence-api \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(status.url)")
echo "✅ FastAPI deployed: $API_URL"

# ── Step 5: Deploy Streamlit ──────────────────────────
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

# get Streamlit URL
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