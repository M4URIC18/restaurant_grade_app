import json
import os

import joblib
import pandas as pd
import streamlit as st

from src.utils import build_feature_vector_from_raw

# -------------------------------------------------
# PATHS
# -------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "restaurant_grade_model.pkl")
META_PATH = os.path.join(BASE_DIR, "models", "model_metadata.json")


# -------------------------------------------------
# LOAD MODEL + METADATA (cached)
# -------------------------------------------------

@st.cache_resource
def load_model():
    print("Loading model from:", MODEL_PATH)
    model = joblib.load(MODEL_PATH)
    print("Model loaded OK!")
    return model


model = load_model()

try:
    with open(META_PATH, "r") as f:
        metadata = json.load(f)
except Exception as e:
    raise RuntimeError(f"❌ Could not load metadata JSON at {META_PATH}: {e}")

FEATURE_COLUMNS = metadata["feature_columns"]
ENCODERS = metadata.get("encoders", {})
SCALER_NEEDED = metadata.get("scaler_needed", False)


# -------------------------------------------------
# Helper: dict → DataFrame with correct column order
# -------------------------------------------------

def to_dataframe(feature_dict: dict) -> pd.DataFrame:
    """
    Convert feature dict → DataFrame with columns in FEATURE_COLUMNS order.
    Missing expected features are filled with 0.
    """
    row = [feature_dict.get(col, 0) for col in FEATURE_COLUMNS]

    # Debug (you can comment these out later)
    print("DEBUG FEATURE TYPES:")
    for k, v in feature_dict.items():
        print(k, type(v), v)

    X = pd.DataFrame([row], columns=FEATURE_COLUMNS)
    return X


# -------------------------------------------------
# Core prediction helpers
# -------------------------------------------------

def predict_from_features(feature_dict: dict) -> dict:
    """
    Predict using a prepared feature dictionary.
    """
    X = to_dataframe(feature_dict)

    pred = model.predict(X)[0]

    if hasattr(model, "predict_proba"):
        probs_raw = model.predict_proba(X)[0]
        prob_dict = {
            label: float(p)
            for label, p in zip(model.classes_, probs_raw)
        }
    else:
        prob_dict = {}

    print("DEBUG row to model:", X.dtypes)
    print(X)

    return {
        "grade": pred,
        "probabilities": prob_dict,
        "features_used": feature_dict,
    }


def predict_from_raw_restaurant(raw_dict: dict) -> dict:
    """
    Universal prediction function.

    Accepts ANY restaurant dictionary:
      - Dataset restaurant row (df_merged_big)
      - Google normalized restaurant (from places.normalize_place_to_restaurant)
      - Any raw dict built in app.py

    Steps:
      1. build_feature_vector_from_raw(raw_dict)  → strict feature dict
      2. to_dataframe(feature_dict)              → DataFrame with correct columns
      3. model.predict / predict_proba
    """
    features = build_feature_vector_from_raw(raw_dict)
    return predict_from_features(features)
