import os
import sys
from pathlib import Path
import pytest
import pandas as pd
from fastapi.testclient import TestClient

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.api.main import app, model_state
from src.inference.inference import model_fn

FEATURES = [
    "battery_power", "blue", "clock_speed", "dual_sim", "fc", "four_g",
    "int_memory", "m_dep", "mobile_wt", "n_cores", "pc", "px_height",
    "px_width", "ram", "sc_h", "sc_w", "talk_time", "three_g",
    "touch_screen", "wifi"
]


@pytest.fixture(scope="session")
def sample_row_dict():
    """Return a single valid mobile specification dictionary."""
    return {
        "battery_power": 842,
        "blue": 0,
        "clock_speed": 2.2,
        "dual_sim": 0,
        "fc": 1,
        "four_g": 0,
        "int_memory": 7,
        "m_dep": 0.6,
        "mobile_wt": 188,
        "n_cores": 2,
        "pc": 2,
        "px_height": 20,
        "px_width": 756,
        "ram": 2549,
        "sc_h": 9,
        "sc_w": 7,
        "talk_time": 19,
        "three_g": 0,
        "touch_screen": 0,
        "wifi": 1,
    }


@pytest.fixture(scope="session")
def sample_raw_dataframe():
    """Return a small dummy dataframe matching mobile price dataset."""
    rows = []
    for i in range(100):
        rows.append({
            "battery_power": 800 + i * 10,
            "blue": i % 2,
            "clock_speed": 1.0 + (i % 20) * 0.1,
            "dual_sim": (i + 1) % 2,
            "fc": i % 10,
            "four_g": i % 2,
            "int_memory": 16 + (i % 32),
            "m_dep": 0.5,
            "mobile_wt": 100 + i,
            "n_cores": 1 + (i % 8),
            "pc": i % 15,
            "px_height": 100 + i * 5,
            "px_width": 500 + i * 5,
            "ram": 500 + i * 30,
            "sc_h": 10,
            "sc_w": 5,
            "talk_time": 10,
            "three_g": 1,
            "touch_screen": 1,
            "wifi": 1,
            "price_range": i % 4,
        })
    return pd.DataFrame(rows)


@pytest.fixture(scope="session")
def model_bundle():
    """Load model bundle from artifacts/model or raise if missing."""
    model_dir = PROJECT_ROOT / "artifacts" / "model"
    if not (model_dir / "model.joblib").exists():
        pytest.skip("Model artifact not found. Run training first.")
    return model_fn(str(model_dir))


@pytest.fixture(scope="session")
def test_client(model_bundle):
    """Return FastAPI TestClient with pre-loaded model state."""
    model_state["bundle"] = model_bundle
    with TestClient(app) as client:
        yield client
