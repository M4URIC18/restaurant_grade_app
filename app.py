import streamlit as st
import pandas as pd
import folium
import os
import requests


from streamlit_folium import st_folium

from src.data_loader import get_data
from src.predictor import predict_restaurant_grade
from src.utils import (
    get_grade_color,
    format_probabilities,
    row_to_model_input,
    restaurant_popup_html,
    normalize_text,
)
# Google Places module (step 12)
from src.places import (
    google_text_search,
    google_place_details,
    reverse_geocode,
    guess_cuisine_from_place,
    normalize_place_to_restaurant,
    google_nearby_restaurants
)


# -------------------------------------------------
# Helper: clear everything
# -------------------------------------------------
def clear_all_selections():
    st.session_state["google_restaurant"] = None
    st.session_state["google_restaurant_nearby"] = None
    st.session_state["map_click"] = None
    st.session_state["google_nearby"] = []
    st.rerun()


# -------------------------------------------------
# Google API key (from Streamlit secrets)
# -------------------------------------------------
GOOGLE_API_KEY = st.secrets.get("GOOGLE_MAPS_API_KEY")

if not GOOGLE_API_KEY:
    st.warning(
        "⚠️ Google Maps API key not found. "
        "Add GOOGLE_MAPS_API_KEY to your .streamlit/secrets.toml and Streamlit Cloud secrets."
    )
else:
    # Make it available to other modules via environment variable
    os.environ["GOOGLE_MAPS_API_KEY"] = GOOGLE_API_KEY


# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="CleanKitchen NYC",
    page_icon="🍽️",
    layout="wide"
)

st.title("CleanKitchen NYC")

st.write("🔑 Secret key exists:", bool(st.secrets.get("GOOGLE_MAPS_API_KEY")))
st.write("🔑 OS env key exists:", bool(os.environ.get("GOOGLE_MAPS_API_KEY")))


st.markdown(
    "Explore NYC restaurant inspections, neighborhood demographics, "
    "and **AI-powered grade predictions** based on real inspection data."
)


# -------------------------------------------------
# Load data
# -------------------------------------------------
@st.cache_data
def load_app_data():
    df = get_data()

    # Basic assumptions about columns
    # Adjust if your col names differ
    if "latitude" in df.columns and "longitude" in df.columns:
        df = df.dropna(subset=["latitude", "longitude"])

    # Normalize some text fields for filters
    df["borough"] = df["borough"].astype(str).str.strip().str.title()
    df["cuisine_description"] = df["cuisine_description"].astype(str).str.strip().str.title()

    return df


df = load_app_data()

if df.empty:
    st.error("No data loaded. Please check your CSV files in the data/ folder.")
    st.stop()


# -------------------------------------------------
# SIDEBAR FILTERS
# -------------------------------------------------
st.sidebar.header("🔎 Filter Restaurants")

# Borough filter
boroughs = ["All"] + sorted(df["borough"].dropna().unique().tolist())
borough_choice = st.sidebar.selectbox("Borough", boroughs, index=0)

# ZIP filter (depends on borough choice)
if borough_choice != "All":
    zip_candidates = df.loc[df["borough"] == borough_choice, "zipcode"].unique()
else:
    zip_candidates = df["zipcode"].unique()

zips = ["All"] + sorted([int(z) for z in zip_candidates if pd.notna(z)])
zip_choice = st.sidebar.selectbox("ZIP code", zips, index=0)

# Cuisine filter
cuisine_list = sorted(df["cuisine_description"].dropna().unique().tolist())
cuisine_choice = st.sidebar.multiselect(
    "Cuisine type",
    options=cuisine_list,
    default=[]
)

# Apply filters
df_filtered = df.copy()

if borough_choice != "All":
    df_filtered = df_filtered[df_filtered["borough"] == borough_choice]

if zip_choice != "All":
    df_filtered = df_filtered[df_filtered["zipcode"] == zip_choice]

if cuisine_choice:
    df_filtered = df_filtered[df_filtered["cuisine_description"].isin(cuisine_choice)]

st.sidebar.markdown(f"**Results: {len(df_filtered)} restaurants**")







# -------------------------------------------------
# MAIN LAYOUT: Map (left) + Details/Prediction (right)
# -------------------------------------------------
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader(" Map of Restaurants")

    if len(df_filtered) == 0:
        st.info("No restaurants match your filters. Try changing the filters.")
    else:
        # -------------------------------------------------
        # 1. Create map centered on filtered dataset
        # -------------------------------------------------
        center_lat = df_filtered["latitude"].mean()
        center_lon = df_filtered["longitude"].mean()

        m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

        # -------------------------------------------------
        # 2. Add dataset restaurants to the map
        # -------------------------------------------------
        for _, row in df_filtered.iterrows():
            lat = row["latitude"]
            lon = row["longitude"]
            grade = row.get("grade", "N/A")
            color = get_grade_color(grade)

            popup_html = restaurant_popup_html(row)

            marker = folium.CircleMarker(
                location=[lat, lon],
                radius=4,
                popup=folium.Popup(popup_html, max_width=250),
                color=color,
                fill=True,
                fill_opacity=0.8
            )

            marker.add_to(m)


        # -------------------------------------------------
        # Google Nearby Restaurants (Step 13)  ✅ FIXED
        # -------------------------------------------------
        nearby = []
        if (
            "map_click" in st.session_state and
            st.session_state["map_click"] is not None
        ):
            clat, clon = st.session_state["map_click"]


            from src.places import google_nearby_restaurants

            # Use the dedicated Nearby Search endpoint  ✅
            
            # 1. RUN Google nearby search (inside a spinner)
            with st.spinner("🔍 Loading nearby restaurants…"):
                nearby = google_nearby_restaurants(clat, clon)


            # Save results for right column prediction logic
            st.session_state["google_nearby"] = nearby

            for place in nearby:
                plat = place["geometry"]["location"]["lat"]
                plon = place["geometry"]["location"]["lng"]
                name = place.get("name", "Unknown")

                popup_html = f"""
                <div style='font-size:14px;'>
                    <b>{name}</b><br>
                    <i>(Google Nearby Restaurant)</i>
                </div>
                """

                marker = folium.CircleMarker(
                    location=[plat, plon],
                    radius=5,
                    popup=folium.Popup(popup_html, max_width=250),
                    color="#1e90ff",
                    fill=True,
                    fill_opacity=0.9
                )

                # NEW → Show name when hovering  
                folium.Tooltip(name).add_to(marker)

                marker.add_to(m)
                marker.place_id = place.get("place_id")





        # -------------------------------------------------
        # 4. Render Folium map
        # -------------------------------------------------
        map_data = st_folium(
            m,
            width="100%",
            height=500,
            key="main_map",
            returned_objects=["last_clicked"]
        )

        # -------------------------------------------------
        # 5. Detect map click
        # -------------------------------------------------
        if map_data and map_data.get("last_clicked"):
            click_lat = map_data["last_clicked"]["lat"]
            click_lon = map_data["last_clicked"]["lng"]

            st.session_state["map_click"] = (click_lat, click_lon)
            # Clear Google Search result when user interacts with map
            st.session_state["google_restaurant"] = None

            st.success(f"📍 You clicked at: {click_lat:.6f}, {click_lon:.6f}")

    # -------------------------------------------------
    # 6. Restaurant table
    # -------------------------------------------------
    st.subheader("Restaurant List")
    st.caption("Filtered view based on your selections in the sidebar.")

    cols_to_show = [
        c for c in ["DBA", "dba", "borough", "zipcode",
                    "cuisine_description", "score", "grade", "inspection_date"]
        if c in df_filtered.columns
    ]

    st.dataframe(df_filtered[cols_to_show].head(300), width="stretch")



with right_col:
    st.subheader(" Inspect & Predict")

    from src.predictor import predict_from_raw_restaurant
    import requests

    # Safety: make sure these exist in session
    if "google_nearby" not in st.session_state:
        st.session_state["google_nearby"] = []
    if "map_click" not in st.session_state:
        st.session_state["map_click"] = None

    has_click = (
        "map_click" in st.session_state and
        st.session_state["map_click"] is not None
    )

    # Small helper to compute squared distance
    def _dist2(lat1, lon1, lat2, lon2):
        return (lat1 - lat2)**2 + (lon1 - lon2)**2

    # =================================================
    # PRIORITY 1 — Dataset restaurant (CSV) click
    # =================================================
    if has_click and (len(df_filtered) > 0):
        clat, clon = st.session_state["map_click"]

        closest_row = None
        min_ds_dist = float("inf")

        for _, row in df_filtered.iterrows():
            if pd.isna(row["latitude"]) or pd.isna(row["longitude"]):
                continue
            d2 = _dist2(clat, clon, row["latitude"], row["longitude"])
            if d2 < min_ds_dist:
                min_ds_dist = d2
                closest_row = row

        # Threshold: very close to a dataset dot
        if closest_row is not None and min_ds_dist < 0.00002:
            st.markdown("## 🍽️ Dataset Restaurant Selected")

            name = closest_row.get("DBA") or closest_row.get("dba", "Unknown")
            borough = closest_row.get("borough") or closest_row.get("boro")
            zipcode = closest_row.get("zipcode")
            cuisine = closest_row.get("cuisine_description", "Unknown")
            score = closest_row.get("score", None)
            crit = closest_row.get("critical_flag_bin", None)

            st.write(f"**Name:** {name}")
            st.write(f"**Borough:** {borough}")
            st.write(f"**ZIP:** {zipcode}")
            st.write(f"**Cuisine:** {cuisine}")
            if score is not None:
                st.write(f"**Score:** {score}")

            raw_restaurant = {
                "borough": borough,
                "zipcode": zipcode,
                "cuisine_description": cuisine,
                "score": score,
                "critical_flag_bin": crit,
            }

            pred = predict_from_raw_restaurant(raw_restaurant)
            grade = pred["grade"]
            probs = pred["probabilities"]
            color = get_grade_color(grade)

            st.markdown(
                f"### ⭐ Predicted Grade: "
                f"<span style='color:{color}; font-size:24px; font-weight:bold'>{grade}</span>",
                unsafe_allow_html=True
            )

            st.markdown("#### Confidence")
            for g_label, p in probs.items():
                st.write(f"{g_label}: {p*100:.1f}%")

            st.markdown("---")
            st.stop()

    # =================================================
    # PRIORITY 2 — Google Nearby restaurant click (blue dot)
    # =================================================
    if has_click and st.session_state.get("google_nearby"):
        clat, clon = st.session_state["map_click"]

        closest_place = None
        min_nb_dist = float("inf")

        for place in st.session_state["google_nearby"]:
            plat = place["geometry"]["location"]["lat"]
            plon = place["geometry"]["location"]["lng"]
            d2 = _dist2(clat, clon, plat, plon)
            if d2 < min_nb_dist:
                min_nb_dist = d2
                closest_place = place

        # If click is close to a blue marker
        if closest_place is not None and min_nb_dist < 0.00002:
            st.markdown("## 🍽️ Google Nearby Restaurant Selected")

            # Get full details from Google
            details = google_place_details(closest_place["place_id"])
            norm = normalize_place_to_restaurant(details)

            st.write(f"**Name:** {norm['name']}")
            st.write(f"**Address:** {norm['address']}")
            st.write(f"**ZIP:** {norm['zipcode']}")
            st.write(f"**Borough:** {norm['borough']}")
            st.write(f"**Cuisine Guess:** {norm['cuisine_description']}")

            pred = predict_from_raw_restaurant(norm)
            grade = pred["grade"]
            probs = pred["probabilities"]
            color = get_grade_color(grade)

            st.markdown(
                f"### ⭐ Predicted Grade: "
                f"<span style='color:{color}; font-size:24px; font-weight:bold'>{grade}</span>",
                unsafe_allow_html=True
            )

            st.markdown("#### Confidence")
            for g_label, p in probs.items():
                st.write(f"{g_label}: {p*100:.1f}%")

            st.markdown("---")
            st.stop()

    # =================================================
    # PRIORITY 3 — Plain map click (NO prediction)
    # =================================================
    if (
        "map_click" in st.session_state and
        st.session_state["map_click"] is not None
    ):
        clat, clon = st.session_state["map_click"]

        st.markdown("## 📍 Map Click Detected")

        API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
        geo_url = (
            f"https://maps.googleapis.com/maps/api/geocode/json"
            f"?latlng={clat},{clon}&key={API_KEY}"
        )
        geo_data = requests.get(geo_url).json()

        zipcode = None
        borough = None
        address = None

        if geo_data.get("results"):
            res = geo_data["results"][0]
            address = res.get("formatted_address", "")
            for comp in res["address_components"]:
                if "postal_code" in comp["types"]:
                    zipcode = comp["long_name"]
                if comp["long_name"].lower() in [
                    "manhattan", "bronx", "brooklyn", "queens", "staten island"
                ]:
                    borough = comp["long_name"].title()

        st.write(f"**Address:** {address}")
        st.write(f"**ZIP:** {zipcode}")
        st.write(f"**Borough:** {borough}")

        st.info("Click a restaurant to see the predicted grade.")

        st.markdown("---")
        st.stop()


    # =================================================
    # PRIORITY 4 — Default
    # =================================================
    st.info("Select a restaurant (red/green/yellow) or click the map to begin.")
