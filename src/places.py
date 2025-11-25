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
# 2. Google Place Details (full data from place_id)
# -------------------------------------------------
def google_place_details(place_id):
    if not API_KEY:
        return {}

    url = (
        "https://maps.googleapis.com/maps/api/place/details/json"
        f"?place_id={place_id}&key={API_KEY}"
    )

    data = requests.get(url).json()
    return data.get("result", {})


# -------------------------------------------------
# 3. Reverse geocode → get zipcode + borough
# -------------------------------------------------
def reverse_geocode(lat, lng):
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
# 4. Guess cuisine from Google “types”
# -------------------------------------------------
def guess_cuisine_from_place(place_obj):
    types = place_obj.get("types", [])
    cuisine_tags = [t for t in types if "_restaurant" in t]

    if len(cuisine_tags) == 0:
        return None

    raw = cuisine_tags[0].replace("_restaurant", "")
    return raw.replace("_", " ").title()


# -------------------------------------------------
# 5. Normalize Google API result → standard restaurant dict
# -------------------------------------------------
def normalize_place_to_restaurant(details):
    """
    Takes Google Place Details result and produces a clean, standardized dict
    that the predictor can use.
    """

    # required fields
    name = details.get("name", "")
    address = details.get("formatted_address", "")

    lat = details["geometry"]["location"]["lat"]
    lng = details["geometry"]["location"]["lng"]

    # zipcode + borough
    zipcode, borough = reverse_geocode(lat, lng)

    # cuisine guess
    cuisine = guess_cuisine_from_place(details) or "Other"

    return {
        "name": name,
        "address": address,
        "latitude": lat,
        "longitude": lng,

        # model-required fields
        "zipcode": zipcode,
        "borough": borough,
        "cuisine_description": cuisine,

        # these will be None → model handles them properly
        "score": None,
        "critical_flag_bin": None,
    }


def google_nearby_restaurants(lat, lng, radius=800):
    """
    Return nearby restaurants using Google Places Nearby Search.
    """
    if not API_KEY:
        return []

    url = (
        "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        f"?location={lat},{lng}&radius={radius}&type=restaurant&key={API_KEY}"
    )

    resp = requests.get(url).json()
    return resp.get("results", [])

