import json
import pytest
import pandas as pd
import numpy as np

from src.inference.inference import input_fn, predict_fn, output_fn, DEFAULT_FEATURES


def test_input_fn_json_dict_list(sample_row_dict):
    """Test input_fn with list of dictionaries."""
    payload = [sample_row_dict]
    df = input_fn(payload, "application/json")
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (1, 20)
    assert list(df.columns) == DEFAULT_FEATURES


def test_input_fn_json_instances_wrapper(sample_row_dict):
    """Test input_fn with {'instances': [...]} format."""
    payload = json.dumps({"instances": [sample_row_dict]})
    df = input_fn(payload, "application/json")
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (1, 20)


def test_input_fn_csv(sample_row_dict):
    """Test input_fn with text/csv content."""
    csv_row = ",".join(str(sample_row_dict[f]) for f in DEFAULT_FEATURES)
    df = input_fn(csv_row, "text/csv")
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (1, 20)


def test_input_fn_invalid_content_type():
    """Test input_fn raises error on invalid content-type."""
    with pytest.raises(ValueError, match="Unsupported content type"):
        input_fn("some body", "application/xml")


def test_predict_fn(model_bundle, sample_row_dict):
    """Test predict_fn with loaded model bundle."""
    df = pd.DataFrame([sample_row_dict])
    results = predict_fn(df, model_bundle)

    assert "predictions" in results
    assert "classes" in results
    assert len(results["predictions"]) == 1

    item = results["predictions"][0]
    assert "predicted_class" in item
    assert item["predicted_class"] in [0, 1, 2, 3]
    assert "predicted_label" in item
    assert "probabilities" in item
    assert len(item["probabilities"]) == 4

    prob_sum = sum(item["probabilities"].values())
    assert np.isclose(prob_sum, 1.0, atol=1e-3)


def test_output_fn(model_bundle, sample_row_dict):
    """Test output_fn serialization for JSON and CSV."""
    df = pd.DataFrame([sample_row_dict])
    preds = predict_fn(df, model_bundle)

    # JSON accept
    json_out = output_fn(preds, "application/json")
    parsed = json.loads(json_out)
    assert "predictions" in parsed

    # CSV accept
    csv_out = output_fn(preds, "text/csv")
    assert csv_out in ["0", "1", "2", "3"]
