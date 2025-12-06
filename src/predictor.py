# src/predictor.py — CLEAN VERSION for new ML pipeline

import os
import joblib
import pandas as pd

# -------------------------------------------------
# Paths
# -------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "models", "restaurant_grade_model.pkl")
DATA_PATH = os.path.join(BASE_DIR, "data", "df_merged_big.csv")

print("🔄 Loading model from:", MODEL_PATH)
model = joblib.load(MODEL_PATH)
print("✅ Model loaded successfully!")

print("🔄 Loading demo/population data from:", DATA_PATH)
try:
    df_demo = pd.read_csv(DATA_PATH)
    print("✅ Demo/population data loaded:", df_demo.shape)
except Exception as e:
    print("❌ ERROR loading df_merged_big.csv:", e)
    raise


# Ensure zipcode is string
if "zipcode" in df_demo.columns:
    df_demo["zipcode"] = df_demo["zipcode"].astype(str)
else:
    raise RuntimeError("df_merged_big.csv must contain a 'zipcode' column.")

# -------------------------------------------------
# Build ZIP and BORO lookup tables
# -------------------------------------------------

# Aggregate by ZIP (median is fine, data already recent)
zip_group = df_demo.groupby("zipcode").agg({
    "population": "median",
    "nyc_poverty_rate": "median",
    "median_income": "median",
    "perc_white": "median",
    "perc_black": "median",
    "perc_asian": "median",
    "perc_other": "median",
    "perc_hispanic": "median",
    "indexscore": "median",
    "boro": "first"
}).reset_index()

ZIP_LOOKUP = zip_group.set_index("zipcode")

# Fallback by BORO
boro_group = df_demo.groupby("boro").agg({
    "population": "median",
    "nyc_poverty_rate": "median",
    "median_income": "median",
    "perc_white": "median",
    "perc_black": "median",
    "perc_asian": "median",
    "perc_other": "median",
    "perc_hispanic": "median",
    "indexscore": "median",
}).reset_index()

BORO_LOOKUP = boro_group.set_index("boro")

# Global fallback (all NYC)
GLOBAL_FALLBACK = df_demo.agg({
    "population": "median",
    "nyc_poverty_rate": "median",
    "median_income": "median",
    "perc_white": "median",
    "perc_black": "median",
    "perc_asian": "median",
    "perc_other": "median",
    "perc_hispanic": "median",
    "indexscore": "median",
})


# -------------------------------------------------
# Feature columns (must match training)
# -------------------------------------------------

FEATURE_COLUMNS = [
    "score",
    "nyc_poverty_rate",
    "median_income",
    "perc_white",
    "perc_black",
    "perc_asian",
    "perc_other",
    "perc_hispanic",
    "indexscore",
    "population",
    "pop_missing",
    "demo_missing",
    "boro",
    "zipcode",
    "cuisine_description",
    "violation_code",
    "critical_flag",
]


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def _normalize_boro(boro: str | None) -> str:
    if not boro or pd.isna(boro):
        return "Unknown"
    b = str(boro).strip()
    # simple clean
    if b.lower() in ["bronx"]:
        return "Bronx"
    if b.lower() in ["brooklyn"]:
        return "Brooklyn"
    if b.lower() in ["manhattan"]:
        return "Manhattan"
    if b.lower() in ["queens"]:
        return "Queens"
    if b.lower() in ["staten island", "statenisland"]:
        return "Staten Island"
    return b


def _get_demo_for_location(zipcode: str | None, boro: str | None) -> dict:
    """
    Return demographics + population + flags for a given zipcode/boro.
    """
    demo = {}
    pop_missing = 0
    demo_missing = 0

    z = None
    if zipcode is not None:
        z = str(zipcode).strip()

    b_norm = _normalize_boro(boro)

    # 1) Try ZIP-level lookup
    if z and z in ZIP_LOOKUP.index:
        row = ZIP_LOOKUP.loc[z]
        demo["population"] = float(row["population"])
        demo["nyc_poverty_rate"] = float(row["nyc_poverty_rate"])
        demo["median_income"] = float(row["median_income"])
        demo["perc_white"] = float(row["perc_white"])
        demo["perc_black"] = float(row["perc_black"])
        demo["perc_asian"] = float(row["perc_asian"])
        demo["perc_other"] = float(row["perc_other"])
        demo["perc_hispanic"] = float(row["perc_hispanic"])
        demo["indexscore"] = float(row["indexscore"])
        pop_missing = 0
        demo_missing = 0
        return demo | {"pop_missing": pop_missing, "demo_missing": demo_missing}

    # 2) Fallback to BORO-level if ZIP not found
    if b_norm in BORO_LOOKUP.index:
        row = BORO_LOOKUP.loc[b_norm]
        demo["population"] = float(row["population"])
        demo["nyc_poverty_rate"] = float(row["nyc_poverty_rate"])
        demo["median_income"] = float(row["median_income"])
        demo["perc_white"] = float(row["perc_white"])
        demo["perc_black"] = float(row["perc_black"])
        demo["perc_asian"] = float(row["perc_asian"])
        demo["perc_other"] = float(row["perc_other"])
        demo["perc_hispanic"] = float(row["perc_hispanic"])
        demo["indexscore"] = float(row["indexscore"])
        pop_missing = 1   # no ZIP detail
        demo_missing = 1
        return demo | {"pop_missing": pop_missing, "demo_missing": demo_missing}

    # 3) Global fallback (very rare)
    demo["population"] = float(GLOBAL_FALLBACK["population"])
    demo["nyc_poverty_rate"] = float(GLOBAL_FALLBACK["nyc_poverty_rate"])
    demo["median_income"] = float(GLOBAL_FALLBACK["median_income"])
    demo["perc_white"] = float(GLOBAL_FALLBACK["perc_white"])
    demo["perc_black"] = float(GLOBAL_FALLBACK["perc_black"])
    demo["perc_asian"] = float(GLOBAL_FALLBACK["perc_asian"])
    demo["perc_other"] = float(GLOBAL_FALLBACK["perc_other"])
    demo["perc_hispanic"] = float(GLOBAL_FALLBACK["perc_hispanic"])
    demo["indexscore"] = float(GLOBAL_FALLBACK["indexscore"])
    pop_missing = 1
    demo_missing = 1
    return demo | {"pop_missing": pop_missing, "demo_missing": demo_missing}


def _extract_base_fields(raw: dict) -> dict:
    """
    Extract minimal known fields from any restaurant dict
    (dataset row or Google Places) and apply simple defaults.
    """
    # Score: dataset inspections have it; Google restaurants don't.
    score = raw.get("score", None)
    if score is None or pd.isna(score):
        score = 10.0  # neutral mid-range default
    else:
        score = float(score)

    # Boro / Borough
    boro = raw.get("boro") or raw.get("borough") or raw.get("Boro")

    # ZIP code: try different key names
    zipcode = (
        raw.get("zipcode")
        or raw.get("zip")
        or raw.get("postal_code")
        or raw.get("postalCode")
    )
    if zipcode is not None:
        zipcode = str(zipcode).strip()

    # Cuisine
    cuisine = (
        raw.get("cuisine_description")
        or raw.get("cuisine")
        or raw.get("type")
        or "Unknown"
    )

    # Violation code
    violation_code = raw.get("violation_code") or "NONE"

    # Critical flag: may be 0/1 or text
    critical_flag = raw.get("critical_flag", 0)
    if isinstance(critical_flag, str):
        critical_flag = 1 if critical_flag.strip().upper() == "CRITICAL" else 0
    try:
        critical_flag = int(critical_flag)
    except Exception:
        critical_flag = 0

    return {
        "score": score,
        "boro": boro,
        "zipcode": zipcode,
        "cuisine_description": cuisine,
        "violation_code": violation_code,
        "critical_flag": critical_flag,
    }


def _build_feature_df(raw: dict) -> tuple[pd.DataFrame, dict]:
    """
    Take any raw restaurant dict and return:
      - 1-row DataFrame with all model features
      - the dict of features used (for debugging/inspection)
    """
    base = _extract_base_fields(raw)

    # Get demo + population from zipcode/boro
    demo = _get_demo_for_location(base["zipcode"], base["boro"])
    boro_norm = _normalize_boro(base["boro"])

    full_features = {
        "score": base["score"],
        "nyc_poverty_rate": demo["nyc_poverty_rate"],
        "median_income": demo["median_income"],
        "perc_white": demo["perc_white"],
        "perc_black": demo["perc_black"],
        "perc_asian": demo["perc_asian"],
        "perc_other": demo["perc_other"],
        "perc_hispanic": demo["perc_hispanic"],
        "indexscore": demo["indexscore"],
        "population": demo["population"],
        "pop_missing": demo["pop_missing"],
        "demo_missing": demo["demo_missing"],
        "boro": boro_norm,
        "zipcode": base["zipcode"] if base["zipcode"] is not None else "",
        "cuisine_description": base["cuisine_description"],
        "violation_code": base["violation_code"],
        "critical_flag": base["critical_flag"],
    }

    # Build DF with correct column order
    row_ordered = {col: full_features[col] for col in FEATURE_COLUMNS}
    df = pd.DataFrame([row_ordered])

    # Fix dtypes
    df["zipcode"] = df["zipcode"].astype(str)
    df["boro"] = df["boro"].astype(str)
    df["cuisine_description"] = df["cuisine_description"].astype(str)
    df["violation_code"] = df["violation_code"].astype(str)
    df["critical_flag"] = df["critical_flag"].astype(int)

    return df, full_features


# -------------------------------------------------
# Public prediction functions
# -------------------------------------------------

def predict_restaurant_grade(restaurant_data: dict) -> dict:
    """
    Old-style API: takes a dict with basic restaurant info
    and returns grade + probabilities.
    """
    X, features_used = _build_feature_df(restaurant_data)

    pred = model.predict(X)[0]

    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)[0]
        prob_dict = {label: float(p) for label, p in zip(model.classes_, probs)}
    else:
        prob_dict = {}

    return {
        "grade": pred,
        "probabilities": prob_dict,
        "features_used": features_used,
    }


def predict_from_raw_restaurant(raw_restaurant: dict) -> dict:
    """
    Universal API: takes a raw restaurant dict (dataset or Google Places)
    and returns:
      - predicted grade
      - probabilities
      - the final feature dict used
    """
    X, features_used = _build_feature_df(raw_restaurant)

    pred = model.predict(X)[0]

    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)[0]
        prob_dict = {label: float(p) for label, p in zip(model.classes_, probs)}
    else:
        prob_dict = {}

    return {
        "grade": pred,
        "probabilities": prob_dict,
        "features_used": features_used,
    }


# Optional convenience wrapper
def predict_grade(input_data: dict) -> dict:
    """
    Simple wrapper used by other modules if needed.
    """
    return predict_restaurant_grade(input_data)

