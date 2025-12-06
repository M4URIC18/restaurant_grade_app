import pandas as pd

# -------------------------------------------------
# 1. Grade → Color mapping (UI styling)
# -------------------------------------------------

GRADE_COLORS = {
    "A": "#2ECC71",   # green
    "B": "#F1C40F",   # yellow
    "C": "#E67E22",   # orange
    "P": "#3498DB",   # blue (Pending)
    "Z": "#95A5A6"    # gray (Grade Pending / Not Yet Graded)
}

def get_grade_color(grade: str):
    """Return the hex color associated with a grade letter."""
    return GRADE_COLORS.get(grade, "#95A5A6")


# -------------------------------------------------
# 2. Format model prediction probabilities
# -------------------------------------------------

def format_probabilities(prob_dict: dict):
    """
    Convert the { 'A': 0.87, 'B': 0.09, ... } dictionary
    into a sorted, clean list for UI display.
    """
    formatted = []
    for grade, prob in prob_dict.items():
        formatted.append((grade, round(prob * 100, 2)))  # convert to %
    return sorted(formatted, key=lambda x: x[1], reverse=True)


# -------------------------------------------------
# 3. Convert a restaurant row into model input dictionary
# -------------------------------------------------

def row_to_model_input(row: pd.Series):
    """
    Take a row from the merged restaurant dataset and extract
    EXACTLY the 12 features expected by the model.

    This ensures predictor.py ALWAYS receives correct values.
    """

    required_fields = [
        "borough",
        "zipcode",
        "cuisine_description",
        "critical_flag_bin",
        "score",
        "nyc_poverty_rate",
        "median_income",
        "perc_white",
        "perc_black",
        "perc_asian",
        "perc_hispanic",
        "indexscore"
    ]

    data = {}

    for field in required_fields:
        if field not in row:
            raise KeyError(f"Missing required field: {field}")
        data[field] = row[field]

    return data


# -------------------------------------------------
# 4. Quick helper: clean filter inputs (ZIP, Cuisine, etc.)
# -------------------------------------------------

def clean_zip(zip_value):
    """Ensure ZIP codes become integers or None."""
    try:
        return int(zip_value)
    except:
        return None


def normalize_text(text):
    """Simple helper for cleaning cuisine/borough search inputs."""
    if pd.isna(text):
        return ""
    return str(text).strip().title()


# -------------------------------------------------
# 5. Map marker helper functions (for Streamlit-Folium or PyDeck)
# -------------------------------------------------

def restaurant_popup_html(row):
    """
    Builds the HTML used in popups on the map
    for folium / leaflet display.
    """
    name = row.get("dba") or row.get("DBA") or "Unknown Restaurant"
    cuisine = row.get("cuisine_description", "Unknown")
    borough = row.get("borough", "Unknown")
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
from .data_loader import load_demo_data

# Load demographic lookup table once
_df_demo = load_demo_data()

DEMO_COLS = [
    "nyc_poverty_rate",
    "median_income",
    "perc_white",
    "perc_black",
    "perc_asian",
    "perc_hispanic",
    "indexscore",
]


def _demo_lookup(zipcode, borough):
    """
    Safely look up demographic info by zipcode.
    If zipcode is missing or doesn't exist in the demographics table,
    return global averages.
    """

    global _df_demo, DEMO_COLS

    df = _df_demo  # the actual demographics dataframe

    # If demographics table is not loaded → return zeros
    if df is None or df.empty:
        return {col: 0 for col in DEMO_COLS}

    # Try to convert zipcode to int
    try:
        zipcode = int(zipcode)
    except:
        zipcode = None

    # If zipcode missing OR column missing → fallback
    if (
        zipcode is None
        or "zipcode" not in df.columns
    ):
        return df[DEMO_COLS].mean().to_dict()

    # Filter rows with matching zipcode
    df_zip = df[df["zipcode"] == zipcode]

    if not df_zip.empty:
        return df_zip[DEMO_COLS].iloc[0].to_dict()

    # Final fallback → global averages
    return df[DEMO_COLS].mean().to_dict()



def build_feature_vector_from_raw(raw):
    """
    Convert ANY restaurant (Google or dataset) into strict model-ready features.
    Ensures:
    - zipcode: str
    - boro: str
    - cuisine_description: str
    - violation_code: str
    - critical_flag: int
    - score: float
    """

    # 1. Borough
    borough = raw.get("boro") or raw.get("borough") or "Unknown"
    borough = normalize_borough(borough)

    # 2. ZIP code → ALWAYS STRING
    zipcode = raw.get("zipcode") or "00000"
    zipcode = str(zipcode).strip()

    # 3. Cuisine description → ALWAYS STRING
    cuisine = raw.get("cuisine_description") or "Other"
    cuisine = str(cuisine).strip().lower()

    # 4. Score → float
    score = raw.get("score")
    try:
        score = float(score)
    except:
        score = 12.0

    # 5. Critical flag → int
    crit = raw.get("critical_flag") or raw.get("critical_flag_bin") or 0
    try:
        crit = int(crit)
    except:
        crit = 0

    # 6. Violation code → ALWAYS STRING
    vio = raw.get("violation_code") or "00X"
    vio = str(vio)

    # 7. Demographics
    demo = _demo_lookup(zipcode, borough)

    # 8. Build final dictionary in correct shapes
    features = {
        "score": score,
        "nyc_poverty_rate": demo.get("nyc_poverty_rate", 0),
        "median_income": demo.get("median_income", 0),
        "perc_white": demo.get("perc_white", 0),
        "perc_black": demo.get("perc_black", 0),
        "perc_asian": demo.get("perc_asian", 0),
        "perc_other": demo.get("perc_other", 0),
        "perc_hispanic": demo.get("perc_hispanic", 0),
        "indexscore": demo.get("indexscore", 0),
        "population": demo.get("population", 0),
        "pop_missing": demo.get("pop_missing", 1),
        "demo_missing": demo.get("demo_missing", 1),
        "critical_flag": crit,
        "boro": borough,
        "zipcode": zipcode,
        "cuisine_description": cuisine,
        "violation_code": vio
    }

    return features


if __name__ == "__main__":
    raw_test = {
        "borough": "Brooklyn",
        "zipcode": 11234,
        "cuisine_description": "caribbean",
        "score": None,
        "critical_flag_bin": None,
    }

    print(build_feature_vector_from_raw(raw_test))



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

        "queens": "Queens",

        "staten island": "Staten Island",
        "statenisl": "Staten Island",
        "staten": "Staten Island",
    }

    return mapping.get(boro, boro.title())



