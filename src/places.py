import requests
import os
import urllib.parse

# Dynamically load the API key each time
def get_api_key():
    return os.environ.get("GOOGLE_MAPS_API_KEY")


# -------------------------------------------------
# 1. Google Places Text Search
# -------------------------------------------------
def google_text_search(query):
    API_KEY = get_api_key()
    if not API_KEY:
        return []

    encoded_query = urllib.parse.quote(query)

    url = (
        "https://maps.googleapis.com/maps/api/place/textsearch/json"
        f"?query={encoded_query}&key={API_KEY}"
    )

    print("DEBUG GOOGLE URL:", url)

    resp = requests.get(url).json()

    # Catch API errors clearly
    if resp.get("status") not in ["OK", "ZERO_RESULTS"]:
        return []

    return resp.get("results", [])


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
            if "postal_code" in comp["types"]:
                zipcode = comp["long_name"]

            low = comp["long_name"].lower()
            borough_map = {
                "manhattan": "Manhattan",
                "bronx": "Bronx",
                "brooklyn": "Brooklyn",
                "queens": "Queens",
                "staten island": "Staten Island",
            }
            if low in borough_map:
                borough = borough_map[low]

    return zipcode, borough, address


# -------------------------------------------------
# 4. Guess cuisine
# -------------------------------------------------
def guess_cuisine_from_place(place_obj):
    types = place_obj.get("types", [])
    cuisine_tags = [t for t in types if "_restaurant" in t]

    if not cuisine_tags:
        return None

    raw = cuisine_tags[0].replace("_restaurant", "")
    return raw.replace("_", " ").title()


# -------------------------------------------------
# 5. Normalize Place Details → Model Input
# -------------------------------------------------
def normalize_place_to_restaurant(details):
    name = details.get("name", "")
    address = details.get("formatted_address", "")

    lat = details["geometry"]["location"]["lat"]
    lng = details["geometry"]["location"]["lng"]

    zipcode, borough, _addr = reverse_geocode(lat, lng)

    cuisine = guess_cuisine_from_place(details) or "Other"

    return {
        "name": name,
        "address": address,
        "latitude": lat,
        "longitude": lng,
        "zipcode": zipcode,
        "borough": borough,
        "cuisine_description": cuisine,
        "score": None,
        "critical_flag_bin": None,
    }


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
