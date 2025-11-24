import requests
import os

API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")


# -------------------------------------------------
# 1. Google Places Text Search
# -------------------------------------------------
def google_text_search(query):
    if not API_KEY:
        return []

    url = (
        "https://maps.googleapis.com/maps/api/place/textsearch/json"
        f"?query={query}&key={API_KEY}"
    )

    resp = requests.get(url).json()
    return resp.get("results", [])


# -------------------------------------------------
# 2. Resolve Borough + ZIP from coordinates
# -------------------------------------------------
def reverse_geocode(lat, lng):
    """
    Return zipcode + borough using Google Geocoding API
    """
    if not API_KEY:
        return None, None

    url = (
        "https://maps.googleapis.com/maps/api/geocode/json"
        f"?latlng={lat},{lng}&key={API_KEY}"
    )

    data = requests.get(url).json()

    zipcode = None
    borough = None

    if "results" in data and len(data["results"]) > 0:
        for c in data["results"][0]["address_components"]:
            if "postal_code" in c["types"]:
                zipcode = c["long_name"]

            if "sublocality" in c["types"] or "political" in c["types"]:
                maybe = c["long_name"].lower()
                borough_map = {
                    "manhattan": "Manhattan",
                    "bronx": "Bronx",
                    "brooklyn": "Brooklyn",
                    "queens": "Queens",
                    "staten island": "Staten Island"
                }
                if maybe in borough_map:
                    borough = borough_map[maybe]

    return zipcode, borough


# -------------------------------------------------
# 3. Guess cuisine from Google Tags
# -------------------------------------------------
def guess_cuisine_from_place(place_obj):
    """
    Google Places sometimes returns:
    place["types"] = ["restaurant", "thai_restaurant", "food", ...]

    This function converts "thai_restaurant" → "Thai"
    """
    types = place_obj.get("types", [])
    cuisine_tags = [t for t in types if "_restaurant" in t]

    if len(cuisine_tags) == 0:
        return None

    raw = cuisine_tags[0].replace("_restaurant", "")
    return raw.replace("_", " ").title()
