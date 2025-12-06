import json
import joblib
import numpy as np
import pandas as pd
import os
import streamlit as st

from src.utils import build_feature_vector_from_raw




# -------------------------------------------------
# PATHS
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "restaurant_grade_model.pkl")
META_PATH = os.path.join(BASE_DIR, "models", "model_metadata.json")



# -------------------------------------------------
# LOAD MODEL WITH CACHE (Fix #1)
# -------------------------------------------------
@st.cache_resource
def load_model():
    print("Loading model from:", MODEL_PATH)
    model = joblib.load(MODEL_PATH)
    print("Model loaded OK!")
    return model

model = load_model()   # <-- cached

# Load metadata
try:
    with open(META_PATH, "r") as f:
        metadata = json.load(f)
except Exception as e:
    raise RuntimeError(f"❌ Could not load metadata JSON at {META_PATH}: {e}")

FEATURE_COLUMNS = metadata["feature_columns"]
ENCODERS = metadata.get("encoders", {})
SCALER_NEEDED = metadata.get("scaler_needed", False)


# -------------------------------------------------
# Helper: normalize borough names
# -------------------------------------------------
BORO_FIX = {
    "New York": "Manhattan",
    "NY": "Manhattan",
    "Manhattan": "Manhattan",
    "Brooklyn": "Brooklyn",
    "Kings": "Brooklyn",
    "Kings County": "Brooklyn",
    "Bronx": "Bronx",
    "The Bronx": "Bronx",
    "Queens": "Queens",
    "Queens County": "Queens",
    "Staten Island": "Staten Island",
    "Richmond": "Staten Island",
    "Richmond County": "Staten Island",
}


def normalize_borough(boro):
    if not isinstance(boro, str):
        return "Unknown"
    b = boro.strip().title()
    return BORO_FIX.get(b, b)


# -------------------------------------------------
# Google API → model feature conversion
# -------------------------------------------------
from src.data_loader import lookup_zip_demo
from src.utils import normalize_borough


# def build_features_from_google(place: dict):
#     """
#     Google Places → ML model feature dict (with ZIP demographic enrichment)
#     """

#     zipcode = str(place.get("zipcode") or "").strip()

#     # -----------------------------
#     #  DEMOGRAPHIC LOOKUP BY ZIP
#     # -----------------------------
#     demo = lookup_zip_demo(zipcode)

#     if demo:
#         # ZIP exists in our dataset
#         population       = demo.get("population", 0)
#         nyc_poverty_rate = demo.get("nyc_poverty_rate", 0)
#         median_income    = demo.get("median_income", 0)
#         perc_white       = demo.get("perc_white", 0)
#         perc_black       = demo.get("perc_black", 0)
#         perc_asian       = demo.get("perc_asian", 0)
#         perc_other       = demo.get("perc_other", 0)
#         perc_hispanic    = demo.get("perc_hispanic", 0)
#         indexscore       = demo.get("indexscore", 0)

#         pop_missing  = 0
#         demo_missing = 0
#     else:
#         # ZIP not found in dataset
#         population       = 0
#         nyc_poverty_rate = 0
#         median_income    = 0
#         perc_white       = 0
#         perc_black       = 0
#         perc_asian       = 0
#         perc_other       = 0
#         perc_hispanic    = 0
#         indexscore       = 0

#         pop_missing  = 1
#         demo_missing = 1

#     # -----------------------------
#     #  BUILD FEATURE DICTIONARY
#     # -----------------------------
#     return {
#         "score": place.get("score", 10),

#         "nyc_poverty_rate": nyc_poverty_rate,
#         "median_income": median_income,
#         "perc_white": perc_white,
#         "perc_black": perc_black,
#         "perc_asian": perc_asian,
#         "perc_other": perc_other,
#         "perc_hispanic": perc_hispanic,
#         "indexscore": indexscore,

#         "population": population,
#         "pop_missing": pop_missing,
#         "demo_missing": demo_missing,

#         "critical_flag": place.get("critical_flag", 0),

#         "boro": normalize_borough(place.get("boro", "Unknown")),
#         "zipcode": zipcode if zipcode else "00000",
#         "cuisine_description": place.get("cuisine_description", "Unknown"),
#         "violation_code": place.get("violation_code", "00X"),
#     }



# -------------------------------------------------
# Dataset restaurant → model feature conversion
# -------------------------------------------------

# def build_features_from_dataset(row: dict):
#     """
#     Raw row from df_merged_big.csv → ML model feature dict
#     """

#     zipcode = row.get("zipcode")
#     if zipcode:
#         zipcode = str(zipcode).strip()

#     features = {
#         "score": row.get("score", 12),
#         "nyc_poverty_rate": row.get("nyc_poverty_rate", 0.20),
#         "median_income": row.get("median_income", 30000),
#         "perc_white": row.get("perc_white", 0.30),
#         "perc_black": row.get("perc_black", 0.30),
#         "perc_asian": row.get("perc_asian", 0.15),
#         "perc_other": row.get("perc_other", 0.05),
#         "perc_hispanic": row.get("perc_hispanic", 0.20),
#         "indexscore": row.get("indexscore", 4.0),

#         "population": row.get("population", 50000),
#         "pop_missing": row.get("pop_missing", 0),
#         "demo_missing": row.get("demo_missing", 0),

#         "critical_flag": row.get("critical_flag", 0),

#         "boro": normalize_borough(row.get("boro", "Unknown")),
#         "zipcode": zipcode if zipcode else "00000",
#         "cuisine_description": row.get("cuisine_description", "Other"),
#         "violation_code": row.get("violation_code", "00X"),
#     }

#     return features


# -------------------------------------------------
# Build final DataFrame in correct column order
# -------------------------------------------------

def to_dataframe(feature_dict: dict):
    """
    Convert feature dict → DataFrame with correct feature order.
    Missing expected features are filled with 0.
    """
    row = []
    for col in FEATURE_COLUMNS:
        row.append(feature_dict.get(col, 0))

    return pd.DataFrame([row], columns=FEATURE_COLUMNS)


# -------------------------------------------------
# Main prediction functions
# -------------------------------------------------

def predict_from_features(feature_dict: dict):
    """
    Predict using a prepared feature dictionary.
    """
    X = to_dataframe(feature_dict)

    pred = model.predict(X)[0]

    if hasattr(model, "predict_proba"):
        probs_raw = model.predict_proba(X)[0]
        prob_dict = {label: float(p) for label, p in zip(model.classes_, probs_raw)}
    else:
        prob_dict = {}

    return {
        "grade": pred,
        "probabilities": prob_dict,
        "features_used": feature_dict
    }


# def predict_from_google(place: dict):
#     """
#     For Google API restaurant markers.
#     """
#     features = build_features_from_google(place)
#     return predict_from_features(features)


# def predict_from_dataset_row(row: dict):
#     """
#     For df_merged_big.csv rows.
#     """
#     features = build_features_from_dataset(row)
#     return predict_from_features(features)


def predict_from_raw_restaurant(raw_restaurant: dict):
    """
    Universal prediction entry point.
    Works for:
      - Dataset rows
      - Google Places normalized restaurants
      - Any raw dict coming from app.py
    """

    # 1. Build full enriched feature vector
    features = build_feature_vector_from_raw(raw_restaurant)

    # 2. Convert to DataFrame (same shape as model)
    X = pd.DataFrame([features], columns=FEATURE_COLUMNS)

    # 3. Predict
    pred = model.predict(X)[0]
    probs = model.predict_proba(X)[0]

    # 4. Format probabilities
    prob_dict = {
        label: float(p)
        for label, p in zip(model.classes_, probs)
    }

    return {
        "grade": pred,
        "probabilities": prob_dict,
        "features_used": features
    }



# -------------------------------------------------------
# Build ML feature vector from Google restaurant features
# -------------------------------------------------------
def build_feature_vector_from_google(google_features: dict):
    """
    google_features is built in places.py via google_place_to_ml_features()

    This function:
    - aligns keys with the model's FEATURE_COLUMNS
    - fills missing values with safe defaults
    """

    row = {}

    for col in FEATURE_COLUMNS:
        if col in google_features:
            row[col] = google_features[col]
        else:
            # universal fallback for unexpected missing fields
            row[col] = 0

    return pd.DataFrame([row])




def predict_from_raw_restaurant(raw_dict: dict):
    """
    Universal prediction function.

    Accepts ANY restaurant dictionary:
    - Google API normalized restaurant (from places.py)
    - Dataset restaurant row
    - Sidebar input restaurant (future feature)

    Converts it → model features using ONE universal builder.
    """

    # Step 1 — Build standard feature dict (boro, zipcode, cuisine, score, etc.)
    features = build_feature_vector_from_raw(raw_dict)

    # Step 2 — Convert dict → DataFrame matching model columns
    X = to_dataframe(features)

    # Step 3 — Predict
    pred = model.predict(X)[0]

    # Step 4 — Probabilities
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)[0]
        prob_dict = {label: float(p) for label, p in zip(model.classes_, probs)}
    else:
        prob_dict = {}

    return {
        "grade": pred,
        "probabilities": prob_dict,
        "features_used": features
    }