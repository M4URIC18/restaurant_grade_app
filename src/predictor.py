import json
import joblib
import numpy as np
import pandas as pd
import os

# -------------------------------------------------
# Load model + metadata once
# -------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "models", "restaurant_grade_model.pkl")
META_PATH = os.path.join(BASE_DIR, "models", "model_metadata.json")

print("Loading model from:", MODEL_PATH)
model = joblib.load(MODEL_PATH)
print("Model loaded successfully!")

# Load metadata
with open(META_PATH, "r") as f:
    metadata = json.load(f)

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

def build_features_from_google(place: dict):
    """
    Google Places restaurant → ML model feature dict
    """

    zipcode = place.get("zipcode")
    if zipcode:
        zipcode = str(zipcode).strip()

    features = {
        "score": place.get("score", 10),  # default inspection score
    
        "nyc_poverty_rate": place.get("nyc_poverty_rate", 0),
        "median_income": place.get("median_income", 0),
        "perc_white": place.get("perc_white", 0),
        "perc_black": place.get("perc_black", 0),
        "perc_asian": place.get("perc_asian", 0),
        "perc_other": place.get("perc_other", 0),
        "perc_hispanic": place.get("perc_hispanic", 0),
        "indexscore": place.get("indexscore", 0),

        "population": place.get("population", 0),
        "pop_missing": place.get("pop_missing", 1),
        "demo_missing": place.get("demo_missing", 1),

        "critical_flag": place.get("critical_flag", 0),

        "boro": normalize_borough(place.get("borough", "Unknown")),
        "zipcode": zipcode if zipcode else "00000",
        "cuisine_description": place.get("cuisine_description", "Unknown"),
        "violation_code": place.get("violation_code", "NONE"),
    }

    return features


# -------------------------------------------------
# Dataset restaurant → model feature conversion
# -------------------------------------------------

def build_features_from_dataset(row: dict):
    """
    Raw row from df_merged_big.csv → ML model feature dict
    """

    zipcode = row.get("zipcode")
    if zipcode:
        zipcode = str(zipcode).strip()

    features = {
        "score": row.get("score", 10),
        "nyc_poverty_rate": row.get("nyc_poverty_rate", 0),
        "median_income": row.get("median_income", 0),
        "perc_white": row.get("perc_white", 0),
        "perc_black": row.get("perc_black", 0),
        "perc_asian": row.get("perc_asian", 0),
        "perc_other": row.get("perc_other", 0),
        "perc_hispanic": row.get("perc_hispanic", 0),
        "indexscore": row.get("indexscore", 0),

        "population": row.get("population", 0),
        "pop_missing": row.get("pop_missing", 0),
        "demo_missing": row.get("demo_missing", 0),

        "critical_flag": row.get("critical_flag", 0),

        "boro": normalize_borough(row.get("boro", "Unknown")),
        "zipcode": zipcode if zipcode else "00000",
        "cuisine_description": row.get("cuisine_description", "Unknown"),
        "violation_code": row.get("violation_code", "NONE"),
    }

    return features


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


def predict_from_google(place: dict):
    """
    For Google API restaurant markers.
    """
    features = build_features_from_google(place)
    return predict_from_features(features)


def predict_from_dataset_row(row: dict):
    """
    For df_merged_big.csv rows.
    """
    features = build_features_from_dataset(row)
    return predict_from_features(features)



