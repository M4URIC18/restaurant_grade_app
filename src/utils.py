import pandas as pd

# -------------------------------------------------
# 1. Grade → Color mapping (UI styling)
# -------------------------------------------------

GRADE_COLORS = {
    "A": "#2ECC71",   # green
    "B": "#F1C40F",   # yellow
    "C": "#E67E22",   # orange
    "P": "#3498DB",   # blue (Pending)
    "Z": "#95A5A6",   # gray (Not Yet Graded / Pending)
}


def get_grade_color(grade: str) -> str:
    """Return the hex color associated with a grade letter."""
    return GRADE_COLORS.get(str(grade).upper(), "#95A5A6")


# -------------------------------------------------
# 2. Format model prediction probabilities
# -------------------------------------------------

def format_probabilities(prob_dict: dict):
    """
    Convert { 'A': 0.87, 'B': 0.09, ... } into
    a sorted list of (grade, percent) pairs for UI.
    """
    formatted = [
        (grade, round(float(prob) * 100.0, 2))
        for grade, prob in prob_dict.items()
    ]
    return sorted(formatted, key=lambda x: x[1], reverse=True)


# -------------------------------------------------
# 3. Simple text / ZIP helpers
# -------------------------------------------------

def clean_zip(zip_value):
    """Ensure ZIP codes become integers or None."""
    try:
        return int(zip_value)
    except Exception:
        return None


def normalize_text(text):
    """Simple helper for cleaning cuisine/borough search inputs."""
    if pd.isna(text):
        return ""
    return str(text).strip().title()


# -------------------------------------------------
# 4. Borough normalization (single source of truth)
# -------------------------------------------------

def normalize_borough(boro):
    """
    Clean borough names so everything is consistent for the ML model.
    """
    if not boro:
        return "Unknown"

    boro = str(boro).strip().lower()

    mapping = {
        "manhattan": "Manhattan",
        "new york": "Manhattan",
        "ny": "Manhattan",

        "bronx": "Bronx",

        "brooklyn": "Brooklyn",
        "kings": "Brooklyn",
        "kings county": "Brooklyn",

        "queens": "Queens",
        "queens county": "Queens",

        "staten island": "Staten Island",
        "statenisl": "Staten Island",
        "staten": "Staten Island",
        "richmond": "Staten Island",
        "richmond county": "Staten Island",
    }

    return mapping.get(boro, boro.title())


# -------------------------------------------------
# 5. Map popup HTML helper
# -------------------------------------------------

def restaurant_popup_html(row):
    """
    Builds the HTML used in popups on the map for folium.
    Works for both dataset rows and normalized Google places
    as long as they have these fields where possible.
    """
    name = row.get("dba") or row.get("DBA") or row.get("name") or "Unknown Restaurant"
    cuisine = row.get("cuisine_description", "Unknown")
    borough = row.get("borough") or row.get("boro", "Unknown")
    zipcode = row.get("zipcode", "")
    score = row.get("score", "")
    grade = row.get("grade", "N/A")

    color = get_grade_color(grade)

    html = f"""
    <div style="font-size:14px;">
        <b>{name}</b><br>
        <span>Cuisine: {cuisine}</span><br>
        <span>Borough: {borough}</span><br>
        <span>ZIP: {zipcode}</span><br>
        <span>Score: {score}</span><br>
        <span>Grade: <b style='color:{color};'>{grade}</b></span>
    </div>
    """
    return html


# -------------------------------------------------
# 6. Build full feature vector for ANY restaurant
# -------------------------------------------------
# This is the main “engine” used by predictor.py.

from src.data_loader import lookup_zip_demo  # noqa: E402


def build_feature_vector_from_raw(raw: dict) -> dict:
    """
    Convert ANY restaurant (Google or dataset) into a strict
    model-ready feature dict matching feature_columns in
    model_metadata.json.

    Expected final keys (order handled in predictor.to_dataframe):

        score,
        nyc_poverty_rate,
        median_income,
        perc_white,
        perc_black,
        perc_asian,
        perc_other,
        perc_hispanic,
        indexscore,
        population,
        pop_missing,
        demo_missing,
        critical_flag,
        boro,
        zipcode,
        cuisine_description,
        violation_code
    """

    # 1. Borough (normalized)
    borough = raw.get("boro") or raw.get("borough") or "Unknown"
    borough = normalize_borough(borough)

    # 2. ZIP → always string
    zipcode = raw.get("zipcode") or "00000"
    zipcode = str(zipcode).strip() if zipcode is not None else "00000"
    if zipcode == "":
        zipcode = "00000"

    # 3. Cuisine → always string (lower or title won’t matter to model after encoding)
    cuisine = raw.get("cuisine_description") or raw.get("cuisine") or "Other"
    cuisine = str(cuisine).strip().lower() or "other"

    # 4. Score → float
    score = raw.get("score")
    try:
        score = float(score)
    except Exception:
        # Safe fallback (mid-range score)
        score = 12.0

    # 5. Critical flag → int
    crit = (
        raw.get("critical_flag")
        or raw.get("critical_flag_bin")
        or raw.get("critical_flag_int")
        or 0
    )
    try:
        crit = int(crit)
    except Exception:
        crit = 0

    # 6. Violation code → string
    vio = raw.get("violation_code") or "00X"
    vio = str(vio).strip() or "00X"

    # 7. Demographics via ZIP lookup (df_merged_big → ZIP table)
    demo = lookup_zip_demo(zipcode)
    if demo is not None:
        nyc_poverty_rate = demo.get("nyc_poverty_rate", 0.20)
        median_income = demo.get("median_income", 30000)
        perc_white = demo.get("perc_white", 0.30)
        perc_black = demo.get("perc_black", 0.30)
        perc_asian = demo.get("perc_asian", 0.15)
        perc_other = demo.get("perc_other", 0.05)
        perc_hispanic = demo.get("perc_hispanic", 0.20)
        indexscore = demo.get("indexscore", 4.0)
        population = demo.get("population", 50000)

        pop_missing = 0
        demo_missing = 0
    else:
        # Fallback defaults if ZIP not found at all
        nyc_poverty_rate = 0.20
        median_income = 30000
        perc_white = 0.30
        perc_black = 0.30
        perc_asian = 0.15
        perc_other = 0.05
        perc_hispanic = 0.20
        indexscore = 4.0
        population = 50000

        pop_missing = 1
        demo_missing = 1

    features = {
        "score": score,
        "nyc_poverty_rate": nyc_poverty_rate,
        "median_income": median_income,
        "perc_white": perc_white,
        "perc_black": perc_black,
        "perc_asian": perc_asian,
        "perc_other": perc_other,
        "perc_hispanic": perc_hispanic,
        "indexscore": indexscore,
        "population": population,
        "pop_missing": pop_missing,
        "demo_missing": demo_missing,
        "critical_flag": crit,
        "boro": borough,
        "zipcode": zipcode,
        "cuisine_description": cuisine,
        "violation_code": vio,
    }

    return features


# -------------------------------------------------
# 7. Violation-code short labels (for charts / UI)
# -------------------------------------------------

VIOLATION_SHORT = {
    "02G": "Cold Hold",
    "02B": "Hot Hold",
    "04A": "Pests",
    "04L": "Flies",
    "04M": "Roaches",
    "04N": "Rats",
    "06C": "Food Temp",
    "06D": "Food Contact",
    "06E": "Sanitation",
    "08A": "Handwash",
    "09C": "Waste",
    "10F": "Plumbing",
    "10G": "Water",
    "15D": "Lighting",
    "10B": "Ventilation",
    "16A": "Food Allergy",
    "22A": "Facility",
}

UNKNOWN_VIOLATION_LABEL = "Other"


if __name__ == "__main__":
    # Quick sanity check
    raw_test = {
        "borough": "Brooklyn",
        "zipcode": 11234,
        "cuisine_description": "Caribbean",
        "score": None,
        "critical_flag_bin": None,
    }
    print(build_feature_vector_from_raw(raw_test))
