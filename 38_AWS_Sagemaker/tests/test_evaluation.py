import json
import os
import pytest
from pathlib import Path

from src.evaluation.evaluate import run_evaluation


def test_run_evaluation_output_schema(tmp_path, sample_raw_dataframe):
    """Test that run_evaluation generates valid evaluation.json report."""
    from src.training.train import train_model, TARGET_COLUMN
    import joblib

    features = [c for c in sample_raw_dataframe.columns if c != TARGET_COLUMN]
    X = sample_raw_dataframe[features]
    y = sample_raw_dataframe[TARGET_COLUMN]

    model = train_model(X, y, n_estimators=10, max_depth=5, random_state=42)

    model_dir = tmp_path / "model"
    model_dir.mkdir()
    model_file = model_dir / "model.joblib"
    joblib.dump(model, str(model_file))

    test_file = tmp_path / "test.csv"
    sample_raw_dataframe.to_csv(str(test_file), index=False)

    eval_dir = tmp_path / "evaluation"

    report = run_evaluation(
        model_path=str(model_dir),
        test_data_path=str(test_file),
        output_eval_dir=str(eval_dir),
    )

    assert "multiclass_classification_metrics" in report
    assert "accuracy" in report["multiclass_classification_metrics"]
    assert "value" in report["multiclass_classification_metrics"]["accuracy"]
    acc_val = report["multiclass_classification_metrics"]["accuracy"]["value"]
    assert 0.0 <= acc_val <= 1.0

    # Verify JSON file was written
    saved_json_path = eval_dir / "evaluation.json"
    assert saved_json_path.exists()
