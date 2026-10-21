#!/usr/bin/env python3
"""
FastAPI Microservice for Local Model Serving.

Exposes REST endpoints for local testing, integration tests, and Swagger documentation:
- GET  /health: Health check, model status, and metadata.
- POST /predict: Inference endpoint with Pydantic request validation.
- GET  /docs: Interactive OpenAPI Swagger documentation.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from src.api.schemas import HealthResponse, PredictionRequest, PredictionResponse
from src.inference.inference import model_fn, predict_fn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("api")

# Global state for loaded model bundle
model_state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: load model on startup."""
    model_dir = os.environ.get("MODEL_DIR", str(PROJECT_ROOT / "artifacts" / "model"))
    logger.info("Initializing API: Loading model from %s", model_dir)
    try:
        bundle = model_fn(model_dir)
        model_state["bundle"] = bundle
        logger.info("Model loaded successfully into FastAPI application memory.")
    except Exception as e:
        logger.error("Failed to load model on startup: %s", e)
        model_state["bundle"] = None
    yield
    # Cleanup on shutdown
    model_state.clear()


app = FastAPI(
    title="Mobile Price Classification MLOps API",
    description="Production REST API serving the Random Forest Mobile Price Tier Classifier.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """Health check endpoint verifying model readiness."""
    bundle = model_state.get("bundle")
    if not bundle:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded or unavailable.",
        )

    return HealthResponse(
        status="healthy",
        model_loaded=True,
        model_type=type(bundle["model"]).__name__,
        feature_count=len(bundle["features"]),
        features=bundle["features"],
        target_classes={str(k): v for k, v in bundle["target_classes"].items()},
    )


@app.post("/predict", response_model=PredictionResponse, tags=["Inference"])
async def predict_price_range(request: PredictionRequest):
    """
    Predict mobile price range category for one or more specification records.

    Price Classes:
    - 0: Low Cost
    - 1: Medium Cost
    - 2: High Cost
    - 3: Very High Cost
    """
    bundle = model_state.get("bundle")
    if not bundle:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not initialized.",
        )

    try:
        # Convert Pydantic records to DataFrame
        instances = [item.model_dump() for item in request.instances]
        df = pd.DataFrame(instances)

        # Run inference using standard SageMaker predict_fn
        results = predict_fn(input_data=df, model_bundle=bundle)
        return results

    except Exception as e:
        logger.error("Inference exception: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Inference error: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("API_PORT", 8000))
    host = os.environ.get("API_HOST", "0.0.0.0")
    uvicorn.run("src.api.main:app", host=host, port=port, reload=False)
