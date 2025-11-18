import json
import joblib
import numpy as np
import pandas as pd
import os

# -------------------------------------------------
# Load model + metadata once (cached)
# -------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# ✔️ Updated the filename here
MODEL_PATH = os.path.join(BASE_DIR, "models", "restaurant_grade_model.pkl")

META_PATH = os.path.join(BASE_DIR, "models", "model_metadata.json")


print("Loading model from:", MODEL_PATH)
try:
    model = joblib.load(MODEL_PATH)
    print("Model loaded successfully!")
except Exception as e:
    print("MODEL LOAD ERROR:", e)
    raise RuntimeError(f"❌ Could not load model: {e}")

# try:
#     model = joblib.load(MODEL_PATH)
# except Exception as e:
#     raise RuntimeError(f"❌ Could not load model: {e}")

try:
    with open(META_PATH, "r") as f:
        metadata = json.load(f)
except Exception as e:
    raise RuntimeError(f"❌ Could not load metadata JSON: {e}")

FEATURE_COLUMNS = metadata["feature_columns"]   # exact order used in training
ENCODERS = metadata.get("encoders", {})
SCALER_NEEDED = metadata.get("scaler_needed", False)


# -------------------------------------------------
# Convert restaurant info into model-ready features
# -------------------------------------------------

def build_feature_vector(restaurant_data: dict):
    """
    restaurant_data is a dict containing the fields your app sends, e.g.:

    {
        "zipcode": 11372,
        "borough": "Queens",
        "cuisine_description": "Latin American",
        "critical_flag_bin": 0,
        "score": 12
    }

    This function transforms it into a DataFrame with the SAME columns
    and order that the model was trained on.
    """
    df_input = pd.DataFrame([restaurant_data])

    if ENCODERS:
        for col, mapping in ENCODERS.items():
            if col in df_input:
                val = df_input[col].iloc[0]
                df_input[col] = mapping.get(val, mapping.get("__OTHER__", 0))

    # Rebuild DataFrame with correct column order
    df_final = pd.DataFrame(columns=FEATURE_COLUMNS)
    for col in FEATURE_COLUMNS:
        df_final[col] = df_input[col] if col in df_input else 0

    return df_final


# -------------------------------------------------
# Prediction function
# -------------------------------------------------

def predict_restaurant_grade(restaurant_data: dict):
    """
    Input: dict with restaurant info
    Output: dict with prediction + probabilities
    """
    X = build_feature_vector(restaurant_data)

    pred = model.predict(X)[0]
    probs = model.predict_proba(X)[0]

    prob_dict = {label: float(p) for label, p in zip(model.classes_, probs)}

    return {
        "grade": pred,
        "probabilities": prob_dict,
        "raw_output": probs.tolist()
    }
