import pytest


def test_api_health_endpoint(test_client):
    """Test GET /health returns 200 OK and valid health metadata."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert data["feature_count"] == 20
    assert "target_classes" in data


def test_api_predict_single_instance(test_client, sample_row_dict):
    """Test POST /predict with a valid mobile payload."""
    payload = {"instances": [sample_row_dict]}
    response = test_client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert len(data["predictions"]) == 1
    assert data["predictions"][0]["predicted_class"] in [0, 1, 2, 3]
    assert "probabilities" in data["predictions"][0]


def test_api_predict_batch_instances(test_client, sample_row_dict):
    """Test POST /predict with multiple instances in a batch."""
    second_row = dict(sample_row_dict)
    second_row["ram"] = 3900
    second_row["battery_power"] = 1950

    payload = {"instances": [sample_row_dict, second_row]}
    response = test_client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["predictions"]) == 2


def test_api_predict_invalid_schema(test_client, sample_row_dict):
    """Test POST /predict returns 422 on invalid feature values."""
    invalid_row = dict(sample_row_dict)
    invalid_row["battery_power"] = 99999  # Exceeds max 2000

    payload = {"instances": [invalid_row]}
    response = test_client.post("/predict", json=payload)
    assert response.status_code == 422
