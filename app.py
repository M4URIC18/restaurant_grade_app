import streamlit as st
import pandas as pd
import folium
import os

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
# Google Search (Step 12 – unified)
# -------------------------------------------------
st.subheader(" Search Any Restaurant (Google Places)")

google_query = st.text_input(
    "Search restaurant by name:",
    placeholder="e.g. Shake Shack, Katz Deli, Chipotle…"
)

# Session slot
if "google_restaurant" not in st.session_state:
    st.session_state["google_restaurant"] = None

if google_query:

    # 1. Text search
    places = google_text_search(google_query)

    if not places:
        st.warning("No matching restaurants found.")
    else:
        # Let user choose the correct result
        names = [p["name"] for p in places]
        choice = st.selectbox("Select restaurant:", names)

        selected = next(p for p in places if p["name"] == choice)

        # 2. Get full details
        details = google_place_details(selected["place_id"])

        # 3. Normalize → (name, address, lat, lon, borough, zipcode, cuisine,...)
        norm = normalize_place_to_restaurant(details)

        # Store normalized record
        st.session_state["google_restaurant"] = norm

        # 4. Predict grade
        from src.predictor import predict_from_raw_restaurant
        pred = predict_from_raw_restaurant(norm)

        grade = pred["grade"]
        probs = pred["probabilities"]
        color = get_grade_color(grade)

        # 5. Display basic info
        st.markdown("### ⭐ Google Search Prediction")
        st.write(f"**Name:** {norm['name']}")
        st.write(f"**Address:** {norm['address']}")
        st.write(f"**ZIP:** {norm['zipcode']}")
        st.write(f"**Borough:** {norm['borough']}")
        st.write(f"**Cuisine Guess:** {norm['cuisine_description']}")

        st.markdown(
            f"**Predicted Grade:** "
            f"<span style='color:{color}; font-size:26px; font-weight:bold'>{grade}</span>",
            unsafe_allow_html=True
        )

        st.markdown("#### Confidence")
        for g, p in probs.items():
            st.write(f"{g}: {p*100:.1f}%")

        st.markdown("---")











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
        # Google Nearby Restaurants (Step 13)
        # -------------------------------------------------
        nearby = []
        if "map_click" in st.session_state:
            clat, clon = st.session_state["map_click"]

            from src.places import google_text_search

            # Search for "restaurants near lat,lon"
            nearby_query = f"restaurants near {clat},{clon}"
            nearby = google_text_search(nearby_query)

            # SAVE into session
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

                marker.add_to(m)

                # Attach place_id to marker object for detection later
                marker.place_id = place.get("place_id")




        # -------------------------------------------------
        # Google restaurant marker (Step 12)
        # -------------------------------------------------
        if st.session_state.get("google_restaurant"):
            g = st.session_state["google_restaurant"]

            popup_html = f"""
            <div style="font-size:14px;">
                <b>{g['name']}</b><br>
                {g['address']}<br>
                <span style='color:blue;'>Google Search Result</span>
            </div>
            """

            folium.Marker(
                location=[g["latitude"], g["longitude"]],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)

            # recenter map
            m.location = [g["latitude"], g["longitude"]]
            m.zoom_start = 15


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

    # -------------------------------------------------
    # NEW: Detect nearest Google Nearby Restaurant clicked
    # -------------------------------------------------

    # Ensure session lists exist
    if "google_nearby" not in st.session_state:
        st.session_state["google_nearby"] = []

    # ❗ Do NOT run detection unless BOTH exist:
    # - user clicked map (map_click exists)
    # - google_nearby has results
    if (
        "map_click" in st.session_state
        and "google_nearby" in st.session_state
        and len(st.session_state["google_nearby"]) > 0
    ):


        clat, clon = st.session_state["map_click"]

        clicked_lat = clat
        clicked_lon = clon

        closest = None
        min_dist = float("inf")

        # Loop over saved nearby results
        for place in st.session_state["google_nearby"]:
            plat = place["geometry"]["location"]["lat"]
            plon = place["geometry"]["location"]["lng"]

            dist = (plat - clicked_lat)**2 + (plon - clicked_lon)**2

            if dist < min_dist:
                min_dist = dist
                closest = place

        # If the closest marker is extremely close → treat it as clicked
        if closest and min_dist < 0.00005:

            st.markdown("## 🍽️ Google Nearby Restaurant Selected")

            # Fetch Google full details
            details = google_place_details(closest["place_id"])

            # Normalize → convert Google data to model input format
            norm = normalize_place_to_restaurant(details)

            # Save it
            st.session_state["google_restaurant_nearby"] = norm

            # Display basic info
            st.write(f"**Name:** {norm['name']}")
            st.write(f"**Address:** {norm['address']}")
            st.write(f"**ZIP:** {norm['zipcode']}")
            st.write(f"**Borough:** {norm['borough']}")
            st.write(f"**Cuisine Guess:** {norm['cuisine_description']}")

            # Predict grade
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
            for g, p in probs.items():
                st.write(f"{g}: {p*100:.1f}%")

            st.markdown("---")

            # Stop UI here so nothing else renders
            st.stop()




    # -------------------------------------------------
    # If user clicked the map, reverse geocode + predict
    # -------------------------------------------------
    if "map_click" in st.session_state:
        clat, clon = st.session_state["map_click"]

        st.markdown("## 📍 Map Click Detected")

        # Reverse geocode ZIP + borough
        import requests
        API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
        geo_url = (
            "https://maps.googleapis.com/maps/api/geocode/json"
            f"?latlng={clat},{clon}&key={API_KEY}"
        )
        geo_data = requests.get(geo_url).json()

        zipcode = None
        borough = None
        address = None

        if "results" in geo_data and geo_data["results"]:
            address = geo_data["results"][0].get("formatted_address", "")
            for comp in geo_data["results"][0]["address_components"]:
                if "postal_code" in comp["types"]:
                    zipcode = comp["long_name"]
                if comp["long_name"].lower() in ["manhattan", "bronx", "brooklyn", "queens", "staten island"]:
                    borough = comp["long_name"].title()

        st.write(f"**Address:** {address}")
        st.write(f"**ZIP:** {zipcode}")
        st.write(f"**Borough:** {borough}")



        # Predict assuming unknown cuisine
        from src.predictor import predict_from_raw_restaurant

        raw_restaurant = {
            "borough": borough,
            "zipcode": zipcode,
            "cuisine_description": "Unknown",
            "score": None,
            "critical_flag_bin": None,
        }

        pred = predict_from_raw_restaurant(raw_restaurant)

        grade = pred["grade"]
        probs = pred["probabilities"]
        color = get_grade_color(grade)

        st.markdown(
            f"### 🍽️ Prediction for Clicked Location: "
            f"<span style='color:{color}; font-size:24px; font-weight:bold'>{grade}</span>",
            unsafe_allow_html=True
        )

        st.markdown("#### Confidence")
        for g, p in probs.items():
            st.write(f"{g}: {p*100:.1f}%")

        st.markdown("---")


    # -------------------------------------------------
    # 👉 INSERT GOOGLE PANEL HERE (Step 7 block)
    # -------------------------------------------------
    # -------------------------------------------------
    # Right column – Google restaurant details (Step 12)
    # -------------------------------------------------
    if st.session_state.get("google_restaurant"):
        g = st.session_state["google_restaurant"]

        st.markdown("## 🔍 Google Restaurant Selected")
        st.write(f"**Name:** {g['name']}")
        st.write(f"**Address:** {g['address']}")
        st.write(f"**ZIP:** {g['zipcode']}")
        st.write(f"**Borough:** {g['borough']}")
        st.write(f"**Cuisine Guess:** {g['cuisine_description']}")

        cuisine_input = st.text_input(
            "Refine Cuisine (optional):",
            value=g["cuisine_description"]
        )

        # Predict with refined cuisine
        if st.button("Predict Grade (Google Restaurant)"):
            refined = g.copy()
            refined["cuisine_description"] = cuisine_input

            from src.predictor import predict_from_raw_restaurant
            pred = predict_from_raw_restaurant(refined)

            grade = pred["grade"]
            probs = pred["probabilities"]
            color = get_grade_color(grade)

            st.markdown("### ⭐ Prediction Result")
            st.markdown(
                f"<span style='color:{color}; font-size:24px; font-weight:bold;'>{grade}</span>",
                unsafe_allow_html=True
            )

            st.markdown("#### Confidence")
            for h, p in probs.items():
                st.write(f"{h}: {p*100:.1f}%")

        st.markdown("---")
        # stop remaining UI
        st.stop()


    # -------------------------------------------------
    # END OF GOOGLE PANEL
    # -------------------------------------------------



    if len(df_filtered) == 0:
        st.info("Use the filters to select at least one restaurant.")
    else:
        # Let user pick a restaurant from a dropdown
        # Use name + zip as label
        if "dba" in df_filtered.columns:
            name_col = "dba"
        elif "DBA" in df_filtered.columns:
            name_col = "DBA"
        else:
            name_col = df_filtered.columns[0]  # fallback

        df_filtered = df_filtered.reset_index(drop=True)
        options = df_filtered.index.tolist()
        labels = [
            f"{df_filtered.loc[i, name_col]} ({df_filtered.loc[i, 'borough']}, {df_filtered.loc[i, 'zipcode']})"
            for i in options
        ]

        selected_idx = st.selectbox(
            "Choose a restaurant to analyze:",
            options=options,
            format_func=lambda i: labels[i]
        )

        selected_row = df_filtered.loc[selected_idx]

        st.markdown("###  Selected Restaurant")
        st.markdown(f"**Name:** {selected_row.get(name_col, 'N/A')}")
        st.markdown(f"**Borough:** {selected_row.get('borough', 'N/A')}")
        st.markdown(f"**ZIP:** {selected_row.get('zipcode', 'N/A')}")
        st.markdown(f"**Cuisine:** {selected_row.get('cuisine_description', 'N/A')}")

        # Show existing inspection info (if present)
        st.markdown("###  Latest Inspection Info")
        st.markdown(f"- **Score:** {selected_row.get('score', 'N/A')}")
        st.markdown(f"- **Official Grade:** {selected_row.get('grade', 'N/A')}")
        if "inspection_date" in selected_row:
            st.markdown(f"- **Inspection Date:** {selected_row.get('inspection_date')}")

        st.markdown("---")
        st.markdown("###  Model Prediction")

        if st.button("Predict Inspection Grade"):
            try:
                # Build model input
                model_input = row_to_model_input(selected_row)
                result = predict_restaurant_grade(model_input)

                predicted_grade = result["grade"]
                probabilities = result["probabilities"]
                formatted_probs = format_probabilities(probabilities)

                color = get_grade_color(predicted_grade)

                st.markdown(
                    f"**Predicted Grade:** "
                    f"<span style='color:{color}; font-size: 24px; font-weight: bold;'>{predicted_grade}</span>",
                    unsafe_allow_html=True
                )

                st.markdown("#### Confidence by Grade")
                for g, p in formatted_probs:
                    bar = "█" * int(p // 4)  # simple text bar
                    st.write(f"{g}: {p:.1f}% {bar}")

            except Exception as e:
                st.error(f"Error making prediction: {e}")

        st.markdown("---")
        st.markdown("###  Neighborhood Snapshot (from NFH data)")
        nf_cols = [
            "nyc_poverty_rate",
            "median_income",
            "perc_white",
            "perc_black",
            "perc_asian",
            "perc_hispanic",
            "indexscore"
        ]
        for col in nf_cols:
            if col in selected_row:
                st.write(f"**{col}:** {selected_row[col]}")
