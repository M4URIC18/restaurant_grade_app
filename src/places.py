import os
import requests


# -------------------------------------------------------
# Read Google API key (we set it in app.py via secrets)
# -------------------------------------------------------
GOOGLE_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError(
        "❌ GOOGLE_MAPS_API_KEY not found in environment. "
        "Make sure you added it to .streamlit/secrets.toml and app.py loads it."
    )


# -------------------------------------------------------
# Text Search → find restaurants by name / keyword
# -------------------------------------------------------
def google_places_text_search(query: str):
    """
    Returns a list of places matching a search query.
    Example: 'Starbucks Upper East Side'
    """
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "key": GOOGLE_API_KEY,
    }
    r = requests.get(url, params=params)
    data = r.json()

    if "results" not in data:
        return []

    return data["results"]


# -------------------------------------------------------
# Place Details → get full info from place_id
# -------------------------------------------------------
def google_place_details(place_id: str):
    """
    Returns full details for a specific Google place_id
    including address, lat/lon, formatted_phone_number, types, etc.
    """
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,geometry,types,formatted_phone_number",
        "key": GOOGLE_API_KEY,
    }
    r = requests.get(url, params=params)
    data = r.json()

    if "result" not in data:
        return {}

    return data["result"]


# -------------------------------------------------------
# Reverse Geocode → lat/lon → ZIP & Borough
# -------------------------------------------------------
def reverse_geocode_zip(lat: float, lng: float):
    """
    Reverse geocode to get ZIP code + borough from coordinates.
    """
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "latlng": f"{lat},{lng}",
        "key": GOOGLE_API_KEY,
    }

    r = requests.get(url, params=params)
    data = r.json()

    zipcode = None
    borough = None

    if "results" not in data:
        return zipcode, borough

    for result in data["results"]:
        for comp in result["address_components"]:
            if "postal_code" in comp["types"]:
                zipcode = comp["long_name"]
            if "sublocality_level_1" in comp["types"]:
                borough = comp["long_name"]

    # Normalize borough (Google sometimes returns weird names)
    if borough:
        borough = borough.title()

    return zipcode, borough


# -------------------------------------------------------
# Clean Google result → minimal restaurant dict
# -------------------------------------------------------
def normalize_place_to_restaurant(place_details: dict):
    """
    Takes a Google Places Details result and returns a clean dict
    with fields your model pipeline can later use.
    """

    lat = place_details["geometry"]["location"]["lat"]
    lng = place_details["geometry"]["location"]["lng"]

    zipcode, borough = reverse_geocode_zip(lat, lng)

    # Guess a cuisine from Google "types" list
    types = place_details.get("types", [])
    cuisine = None

    for t in types:
        if "restaurant" in t:
            continue
        if "food" in t:
            continue
        if t not in ["point_of_interest", "establishment"]:
            cuisine = t.replace("_", " ")
            break

    # Fallback cuisine
    if cuisine is None:
        cuisine = "other"

    # Build raw restaurant dict
    return {
        "name": place_details.get("name"),
        "address": place_details.get("formatted_address"),
        "latitude": lat,
        "longitude": lng,

        # Core model input fields
        "borough": borough,
        "zipcode": zipcode,
        "cuisine_description": cuisine,

        # Score and critical flag we will fill later
        "score": None,
        "critical_flag_bin": None,
    }
