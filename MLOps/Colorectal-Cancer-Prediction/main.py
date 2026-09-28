import os
import logging
from flask import Flask, render_template, request, jsonify
import joblib
import numpy as np
import pandas as pd

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Base directory for relative artifact paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "artifacts", "models", "model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "artifacts", "processed", "scaler.pkl")

# Categorical mappings matching LabelEncoder training
TREATMENT_MAPPING = {
    "chemotherapy": 0, "0": 0, 0: 0,
    "combination": 1, "1": 1, 1: 1,
    "radiotherapy": 2, "2": 2, 2: 2,
    "surgery": 3, "3": 3, 3: 3,
}

DIABETES_MAPPING = {
    "no": 0, "0": 0, 0: 0,
    "yes": 1, "1": 1, 1: 1,
}

FEATURE_COLUMNS = [
    "Healthcare_Costs",
    "Tumor_Size_mm",
    "Treatment_Type",
    "Diabetes",
    "Mortality_Rate_per_100K",
]

# Load artifacts safely
model = None
scaler = None

try:
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        logger.info("Model and Scaler loaded successfully.")
    else:
        logger.warning(
            f"Artifacts missing: model_exists={os.path.exists(MODEL_PATH)}, scaler_exists={os.path.exists(SCALER_PATH)}"
        )
except Exception as e:
    logger.error(f"Error loading model/scaler: {e}")


def parse_and_validate_inputs(data):
    """Parses, validates, and encodes form/JSON inputs."""
    # Healthcare costs
    raw_cost = data.get("healthcare_costs")
    if raw_cost is None or str(raw_cost).strip() == "":
        raise ValueError("Healthcare Costs is required.")
    cost = float(raw_cost)
    if cost <= 0:
        raise ValueError("Healthcare Costs must be a positive number.")

    # Tumor size
    raw_tumor = data.get("tumor_size")
    if raw_tumor is None or str(raw_tumor).strip() == "":
        raise ValueError("Tumor Size is required.")
    tumor = float(raw_tumor)
    if tumor <= 0:
        raise ValueError("Tumor Size must be greater than 0 mm.")

    # Mortality rate
    raw_mortality = data.get("mortality_rate")
    if raw_mortality is None or str(raw_mortality).strip() == "":
        raise ValueError("Mortality Rate is required.")
    mortality = float(raw_mortality)
    if mortality < 0:
        raise ValueError("Mortality Rate cannot be negative.")

    # Treatment type
    raw_treatment = str(data.get("treatment_type", "")).strip().lower()
    if raw_treatment not in TREATMENT_MAPPING:
        raise ValueError(
            "Invalid Treatment Type. Choose from: Chemotherapy, Combination, Radiotherapy, or Surgery."
        )
    treatment_val = TREATMENT_MAPPING[raw_treatment]

    # Diabetes
    raw_diabetes = str(data.get("diabetes", "")).strip().lower()
    if raw_diabetes not in DIABETES_MAPPING:
        raise ValueError("Invalid Diabetes status. Choose 'No' or 'Yes'.")
    diabetes_val = DIABETES_MAPPING[raw_diabetes]

    return {
        "Healthcare_Costs": cost,
        "Tumor_Size_mm": tumor,
        "Treatment_Type": treatment_val,
        "Diabetes": diabetes_val,
        "Mortality_Rate_per_100K": mortality,
    }


@app.route("/")
def home():
    return render_template(
        "index.html",
        prediction=None,
        form_data={},
        error=None,
    )


@app.route("/health")
def health():
    return jsonify(
        {
            "status": "healthy",
            "model_loaded": model is not None,
            "scaler_loaded": scaler is not None,
        }
    )


@app.route("/predict", methods=["POST"])
def predict():
    if model is None or scaler is None:
        err_msg = "Model or Scaler not loaded. Please ensure training pipeline has run."
        if request.is_json:
            return jsonify({"status": "error", "message": err_msg}), 503
        return render_template("index.html", error=err_msg, prediction=None, form_data={}), 503

    is_api = request.is_json or request.headers.get("Accept") == "application/json"
    raw_data = request.get_json(silent=True) if request.is_json else request.form.to_dict()

    try:
        validated = parse_and_validate_inputs(raw_data)

        # Build DataFrame with explicit feature names to eliminate sklearn warnings
        input_df = pd.DataFrame([validated], columns=FEATURE_COLUMNS)

        # Scale features and run inference
        scaled_input = scaler.transform(input_df)
        pred_label = model.predict(scaled_input)[0]

        # Calculate prediction probabilities if supported
        probabilities = {}
        confidence = 0.0
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(scaled_input)[0]
            classes = list(model.classes_)
            no_idx = classes.index("No") if "No" in classes else 0
            yes_idx = classes.index("Yes") if "Yes" in classes else 1

            p_no = float(probs[no_idx])
            p_yes = float(probs[yes_idx])
            probabilities = {
                "p_no": round(p_no * 100, 1),
                "p_yes": round(p_yes * 100, 1),
            }
            confidence = round(max(p_no, p_yes) * 100, 1)

        result_payload = {
            "prediction": pred_label,
            "survival_likely": pred_label == "Yes",
            "confidence": confidence,
            "probabilities": probabilities,
            "inputs": {
                "healthcare_costs": validated["Healthcare_Costs"],
                "tumor_size": validated["Tumor_Size_mm"],
                "treatment_type": raw_data.get("treatment_type"),
                "diabetes": raw_data.get("diabetes"),
                "mortality_rate": validated["Mortality_Rate_per_100K"],
            },
        }

        if is_api:
            return jsonify({"status": "success", **result_payload})

        return render_template(
            "index.html",
            prediction=result_payload,
            form_data=raw_data,
            error=None,
        )

    except ValueError as ve:
        logger.warning(f"Validation error: {ve}")
        if is_api:
            return jsonify({"status": "error", "message": str(ve)}), 400
        return render_template(
            "index.html",
            error=str(ve),
            prediction=None,
            form_data=raw_data,
        ), 400
    except Exception as e:
        logger.error(f"Unexpected prediction error: {e}", exc_info=True)
        if is_api:
            return jsonify({"status": "error", "message": f"Server error: {e}"}), 500
        return render_template(
            "index.html",
            error=f"An unexpected error occurred during prediction: {e}",
            prediction=None,
            form_data=raw_data,
        ), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, host="0.0.0.0", port=port)