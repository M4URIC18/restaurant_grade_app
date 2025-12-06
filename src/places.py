import requests
import os
import urllib.parse

# Dynamically load the API key each time
def get_api_key():
    return os.environ.get("GOOGLE_MAPS_API_KEY")




# -------------------------------------------------
# 2. Google Place Details
# -------------------------------------------------
def google_place_details(place_id):
    API_KEY = get_api_key()
    if not API_KEY:
        return {}

    url = (
        "https://maps.googleapis.com/maps/api/place/details/json"
        f"?place_id={place_id}&key={API_KEY}"
    )

    resp = requests.get(url).json()

    if resp.get("status") != "OK":
        return {}

    return resp.get("result", {})


# -------------------------------------------------
# 3. Reverse Geocoding
# -------------------------------------------------
def reverse_geocode(lat, lng):
    API_KEY = get_api_key()
    if not API_KEY:
        return None, None, None

    url = (
        "https://maps.googleapis.com/maps/api/geocode/json"
        f"?latlng={lat},{lng}&key={API_KEY}"
    )

    resp = requests.get(url).json()

    zipcode = None
    borough = None
    address = None

    if resp.get("results"):
        result = resp["results"][0]
        address = result.get("formatted_address", "")

        for comp in result.get("address_components", []):
            long_name = comp["long_name"]
            low = long_name.lower()

            # ZIP code
            if "postal_code" in comp.get("types", []):
                zipcode = long_name

            # -------------------------------
            # Correct Borough Detection
            # -------------------------------
            if "manhattan" in low or "new york county" in low:
                borough = "Manhattan"
            elif "bronx" in low or "bronx county" in low:
                borough = "Bronx"
            elif "brooklyn" in low or "kings county" in low:
                borough = "Brooklyn"
            elif "queens" in low or "queens county" in low:
                borough = "Queens"
            elif "staten island" in low or "richmond county" in low:
                borough = "Staten Island"

    return zipcode, borough, address



# -------------------------------------------------
# 5. Normalize Place Details → Model Input
# -------------------------------------------------
# -------------------------------------------------
# 5. Normalize Place Details → Model Input
# -------------------------------------------------
def normalize_place_to_restaurant(details):
    """
    Convert Google Place Details into the raw restaurant dictionary.
    This will be later enriched with demographics via ZIP lookup.
    """

    # 1. Extract base info
    name = details.get("name", "") or "Unknown"
    address = details.get("formatted_address", "") or "Unknown"

    lat = details["geometry"]["location"]["lat"]
    lng = details["geometry"]["location"]["lng"]

    # 2. Reverse geocode → ZIP + borough
    zipcode, borough, _addr = reverse_geocode(lat, lng)

    zipcode = str(zipcode) if zipcode else "00000"
    if not borough:
        borough = "Unknown"

    # 3. Cuisine detection
    types_list = details.get("types", [])
    cuisine = map_google_types_to_cuisine(types_list)
    if not cuisine or cuisine.strip() == "":
        cuisine = "Other"

    # 4. Build the *raw* Google restaurant dict
    #    (demographics will be added later)
    return {
        "name": name,
        "address": address,
        "latitude": lat,
        "longitude": lng,

        "zipcode": zipcode,
        "boro": borough,
        "borough": borough,     # ← REQUIRED FIX

        "cuisine_description": cuisine,

        # Google restaurants do not have inspection data:
        "score": 10,
        "critical_flag": 0,
        "violation_code": "00X",
    }





def map_google_types_to_cuisine(types_list):
    """
    Converts Google Place 'types' into a cuisine string for the ML model.
    """
    if not types_list:
        return "Unknown"

    # Priority 1: Look for tags like 'mexican_restaurant', 'chinese_restaurant'
    for t in types_list:
        if t.endswith("_restaurant"):
            return t.replace("_restaurant", "").replace("_", " ").title()

    # Priority 2: Common food categories
    keyword_map = {
        "fast_food": "Fast Food",
        "pizza": "Pizza",
        "cafe": "Cafe",
        "bar": "Bar",
        "bakery": "Bakery",
        "seafood": "Seafood",
        "steakhouse": "Steakhouse",
        "sandwich": "Sandwiches",
        "deli": "Deli",
    }
    for t in types_list:
        for key, val in keyword_map.items():
            if key in t:
                return val

    # Default fallback
    return "Other"



# -------------------------------------------------
# 6. Nearby Search
# -------------------------------------------------
def google_nearby_restaurants(lat, lng, radius=800):
    API_KEY = get_api_key()
    if not API_KEY:
        return []

    url = (
        "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        f"?location={lat},{lng}&radius={radius}&type=restaurant&key={API_KEY}"
    )

    resp = requests.get(url).json()

    if resp.get("status") not in ["OK", "ZERO_RESULTS"]:
        return []

    return resp.get("results", [])



# -------------------------------------------------
# 7. Convert Google place → ML feature dict
# -------------------------------------------------
def google_place_to_ml_features(details, demographics_lookup=None, population_lookup=None):
    """
    Convert Google Place Details into the full ML feature set
    required by predictor.py.
    """

    base = normalize_place_to_restaurant(details)

    # ---- 1. Extract known fields ----
    zipcode = base.get("zipcode")
    borough = base.get("borough")
    cuisine = base.get("cuisine_description", "Other")

    # ---- 2. Look up demographics if ZIP is present ----
    if zipcode and demographics_lookup is not None and zipcode in demographics_lookup:
        demo = demographics_lookup[zipcode]
        nyc_poverty_rate = demo["nyc_poverty_rate"]
        median_income = demo["median_income"]
        perc_white = demo["perc_white"]
        perc_black = demo["perc_black"]
        perc_asian = demo["perc_asian"]
        perc_other = demo["perc_other"]
        perc_hispanic = demo["perc_hispanic"]
        indexscore = demo["indexscore"]
        demo_missing = 0
    else:
        # fallback defaults
        nyc_poverty_rate = 0.20
        median_income = 30000
        perc_white = 0.30
        perc_black = 0.30
        perc_asian = 0.15
        perc_other = 0.05
        perc_hispanic = 0.20
        indexscore = 4.0
        demo_missing = 1

    # ---- 3. Population lookup ----
    if zipcode and population_lookup is not None and zipcode in population_lookup:
        population = population_lookup[zipcode]
        pop_missing = 0
    else:
        population = 50000
        pop_missing = 1

    # ---- 4. Build the final ML dictionary ----
    return {
        "score": 12,  # fallback average if Google restaurant has no score
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
        "critical_flag": 0,  # Google doesn't provide violation data
        "boro": borough if borough else "Unknown",
        "zipcode": zipcode if zipcode else "00000",
        "cuisine_description": cuisine,
        "violation_code": "00X"  # default code when unknown
    }

