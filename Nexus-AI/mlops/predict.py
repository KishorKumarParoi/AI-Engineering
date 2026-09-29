"""
Nexus-AI: FastAPI Model Inference Server
==========================================
Production-ready inference endpoint with:
- Health/readiness checks for Kubernetes
- Prometheus metrics integration
- Request validation with Pydantic
- Batch prediction support
- Latency tracking

Usage:
    uvicorn mlops.predict:app --host 0.0.0.0 --port 8081
"""

import time
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Nexus-AI Delivery ETA Prediction API",
    description="Production model serving for Zomato delivery time prediction",
    version="1.0.0",
)

# ── Global State ─────────────────────────────────────────────────────────
_model = None
_model_metadata = None
_prediction_count = 0
_total_latency = 0.0


class PredictionRequest(BaseModel):
    """Single delivery ETA prediction request."""

    distance_km: float = Field(..., gt=0, le=50, description="Delivery distance in km")
    preparation_time_min: float = Field(..., ge=0, le=60, description="Kitchen prep time")
    weather_code: int = Field(0, ge=0, le=5, description="0=Clear, 1=Cloudy, 2=Rain, 3=Heavy Rain, 4=Storm, 5=Fog")
    traffic_code: int = Field(1, ge=0, le=3, description="0=Low, 1=Medium, 2=High, 3=Jam")
    partner_tier_code: int = Field(1, ge=0, le=2, description="0=Bronze, 1=Silver, 2=Gold")
    vehicle_type_code: int = Field(2, ge=0, le=3, description="0=Bicycle, 1=Scooter, 2=Bike, 3=Car")
    hour_of_day: int = Field(..., ge=0, le=23, description="Hour of order placement")
    is_weekend: bool = Field(False, description="Weekend order flag")
    items_count: int = Field(1, ge=1, le=20, description="Number of items ordered")
    order_value: float = Field(300, ge=0, description="Total order amount (INR)")
    restaurant_rating: float = Field(4.0, ge=1.0, le=5.0, description="Restaurant rating")
    avg_cost_for_two: float = Field(500, ge=0, description="Restaurant avg cost for two")
    price_tier_code: int = Field(1, ge=0, le=3, description="0=Budget, 1=Mid, 2=Premium, 3=Luxury")
    cuisine_restaurant_count: int = Field(50, ge=1, description="Restaurants with same cuisine")
    estimated_eta_min: float = Field(30, ge=5, description="System's initial ETA estimate")


class PredictionResponse(BaseModel):
    """Prediction response with confidence."""

    predicted_eta_min: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    model_type: str
    latency_ms: float


class BatchPredictionRequest(BaseModel):
    """Batch prediction request."""

    predictions: list[PredictionRequest]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    model_loaded: bool
    predictions_served: int
    avg_latency_ms: float


def _load_model():
    """Load the trained model from artifacts."""
    global _model, _model_metadata

    if _model is not None:
        return

    artifacts_dir = Path("mlops/artifacts")

    # Try joblib first, then pickle
    model_path = artifacts_dir / "delivery_eta_model.joblib"
    if model_path.exists():
        import joblib
        _model = joblib.load(model_path)
    else:
        model_path = artifacts_dir / "delivery_eta_model.pkl"
        if model_path.exists():
            import pickle
            with open(model_path, "rb") as f:
                _model = pickle.load(f)

    # Load metadata
    metadata_path = artifacts_dir / "model_registry.json"
    if metadata_path.exists():
        import json
        with open(metadata_path) as f:
            _model_metadata = json.load(f)


def _request_to_features(req: PredictionRequest) -> np.ndarray:
    """Convert a PredictionRequest to the feature vector expected by the model."""
    return np.array([[
        req.distance_km,
        req.preparation_time_min,
        req.weather_code,
        req.traffic_code,
        req.partner_tier_code,
        req.vehicle_type_code,
        req.hour_of_day,
        int(req.is_weekend),
        req.items_count,
        req.order_value,
        req.restaurant_rating,
        req.avg_cost_for_two,
        req.price_tier_code,
        req.cuisine_restaurant_count,
        req.estimated_eta_min,
    ]])


@app.on_event("startup")
async def startup():
    """Load model on startup."""
    _load_model()


@app.get("/health", response_model=HealthResponse, tags=["ops"])
async def health():
    """Kubernetes health/readiness check."""
    global _prediction_count, _total_latency

    avg_latency = (_total_latency / _prediction_count * 1000) if _prediction_count > 0 else 0

    return HealthResponse(
        status="healthy" if _model is not None else "degraded",
        model_loaded=_model is not None,
        predictions_served=_prediction_count,
        avg_latency_ms=round(avg_latency, 2),
    )


@app.post("/predict", response_model=PredictionResponse, tags=["inference"])
async def predict(request: PredictionRequest):
    """Single delivery ETA prediction."""
    global _prediction_count, _total_latency

    _load_model()
    if _model is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Run training pipeline first.")

    start = time.time()
    features = _request_to_features(request)
    prediction = float(_model.predict(features)[0])
    latency = time.time() - start

    _prediction_count += 1
    _total_latency += latency

    # Confidence interval (simplified: ±model MAE)
    mae = 5.0  # Default, updated from model metrics
    if _model_metadata and "metrics" in _model_metadata:
        mae = _model_metadata["metrics"].get("mae", 5.0)

    return PredictionResponse(
        predicted_eta_min=round(max(5, prediction), 1),
        confidence_interval_lower=round(max(5, prediction - mae), 1),
        confidence_interval_upper=round(prediction + mae, 1),
        model_type=_model_metadata.get("model_type", "unknown") if _model_metadata else "unknown",
        latency_ms=round(latency * 1000, 2),
    )


@app.post("/predict/batch", response_model=list[PredictionResponse], tags=["inference"])
async def predict_batch(request: BatchPredictionRequest):
    """Batch delivery ETA predictions (up to 100)."""
    if len(request.predictions) > 100:
        raise HTTPException(status_code=400, detail="Batch size limited to 100")

    results = []
    for pred_req in request.predictions:
        result = await predict(pred_req)
        results.append(result)

    return results


@app.get("/metrics", tags=["ops"])
async def prometheus_metrics():
    """Prometheus metrics endpoint for scraping."""
    metrics_path = Path("mlops/artifacts/prometheus_metrics.prom")
    if metrics_path.exists():
        content = metrics_path.read_text()
        # Append runtime metrics
        content += f'\nnexus_model_predictions_total {{}} {_prediction_count}\n'
        avg_lat = (_total_latency / _prediction_count) if _prediction_count > 0 else 0
        content += f'nexus_model_avg_inference_latency_seconds {{}} {avg_lat:.6f}\n'
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content, media_type="text/plain")

    return {"error": "No metrics available. Run training pipeline first."}


@app.get("/model/info", tags=["registry"])
async def model_info():
    """Get current model metadata."""
    _load_model()
    if _model_metadata:
        return _model_metadata
    return {"status": "NO_MODEL", "message": "No model registered. Run training first."}
