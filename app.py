import os
import requests

import pandas as pd
import streamlit as st
import folium
import altair as alt
from streamlit_folium import st_folium

from src.data_loader import get_data
from src.predictor import predict_from_raw_restaurant
from src.utils import (
    get_grade_color,
    restaurant_popup_html,
    VIOLATION_SHORT,
    UNKNOWN_VIOLATION_LABEL,
)
from src.places import (
    google_place_details,
    reverse_geocode,
    normalize_place_to_restaurant,
    google_nearby_restaurants,
)

# -------------------------------------------------
# 🔧 Session State Initialization
# -------------------------------------------------
if "map_center" not in st.session_state:
    # Default to NYC
    st.session_state["map_center"] = [40.7128, -74.0060]

if "map_zoom" not in st.session_state:
    st.session_state["map_zoom"] = 12

if "just_selected_restaurant" not in st.session_state:
    st.session_state["just_selected_restaurant"] = False

if "map_click" not in st.session_state:
    st.session_state["map_click"] = None

if "last_processed_click" not in st.session_state:
    st.session_state["last_processed_click"] = None

if "google_nearby" not in st.session_state:
    st.session_state["google_nearby"] = []

if "google_restaurant_nearby" not in st.session_state:
    st.session_state["google_restaurant_nearby"] = None

if "google_mode" not in st.session_state:
    st.session_state["google_mode"] = False

if "prev_google_mode" not in st.session_state:
    st.session_state["prev_google_mode"] = st.session_state["google_mode"]


# -------------------------------------------------
# 🔑 Google API key (from Streamlit secrets)
# -------------------------------------------------
GOOGLE_API_KEY = st.secrets.get("GOOGLE_MAPS_API_KEY")
if not GOOGLE_API_KEY:
    st.warning(
        "⚠️ Google Maps API key not found. "
        "Add GOOGLE_MAPS_API_KEY to your .streamlit/secrets.toml and Streamlit Cloud secrets."
    )
else:
    os.environ["GOOGLE_MAPS_API_KEY"] = GOOGLE_API_KEY

# -------------------------------------------------
# 🧱 Page config
# -------------------------------------------------
st.set_page_config(
    page_title="CleanKitchen NYC",
    page_icon="🍽️",
    layout="wide",
)

st.title("CleanKitchen NYC")

st.markdown(
    "Explore NYC restaurant inspections, neighborhood demographics, "
    "and **AI-powered grade predictions** based on real inspection data."
)

# -------------------------------------------------
# 📥 Load & prepare data
# -------------------------------------------------
def load_app_data():
    df = get_data()

    # Drop rows without coordinates (for the map)
    if "latitude" in df.columns and "longitude" in df.columns:
        df = df.dropna(subset=["latitude", "longitude"])

    # Normalize text fields
    df["borough"] = df["borough"].astype(str).str.strip().str.title()
    df["cuisine_description"] = (
        df["cuisine_description"].astype(str).str.strip().str.title()
    )

    return df


df = load_app_data()

if df.empty:
    st.error("No data loaded. Please check your CSV files in the data/ folder.")
    st.stop()

# -------------------------------------------------
# 🎚️ Sidebar Filters
# -------------------------------------------------
st.sidebar.header("🔎 Filter Restaurants")

# Borough filter
boroughs = ["All"] + sorted(df["borough"].dropna().unique().tolist())
borough_choice = st.sidebar.selectbox("Borough", boroughs, index=0)

# ZIP filter (depends on borough)
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
    default=[],
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
# 🗺️ Map Builder
# -------------------------------------------------
def build_map(center, zoom, df_for_map, google_nearby_data, google_mode: bool):
    """
    Build a fresh Folium map for each rerun.

    - If google_mode == False → show dataset restaurants only.
    - If google_mode == True  → show Google nearby restaurants only.
    """
    m = folium.Map(location=center, zoom_start=zoom, control_scale=True)

    dataset_fg = folium.FeatureGroup(name="Dataset Restaurants")
    google_fg = folium.FeatureGroup(name="Google Restaurants")

    # Dataset markers (only if NOT in google mode)
    if not google_mode:
        for _, row in df_for_map.iterrows():
            lat = row["latitude"]
            lon = row["longitude"]
            grade = row.get("grade", "N/A")
            color = get_grade_color(grade)
            popup_html = restaurant_popup_html(row)

            folium.CircleMarker(
                location=[lat, lon],
                radius=4,
                popup=folium.Popup(popup_html, max_width=250),
                color=color,
                fill=True,
                fill_opacity=0.8,
            ).add_to(dataset_fg)

        dataset_fg.add_to(m)

    # Google markers (only if in google mode)
    if google_mode and google_nearby_data:
        for place in google_nearby_data:
            plat = place["geometry"]["location"]["lat"]
            plon = place["geometry"]["location"]["lng"]
            name = place.get("name", "Unknown")

            folium.CircleMarker(
                location=[plat, plon],
                radius=6,
                popup=name,
                color="#1e90ff",
                fill=True,
                fill_opacity=0.9,
            ).add_to(google_fg)

        google_fg.add_to(m)

    return m


# -------------------------------------------------
# 📐 Distance helper
# -------------------------------------------------
def _dist2(lat1, lon1, lat2, lon2):
    return (lat1 - lat2) ** 2 + (lon1 - lon2) ** 2


# -------------------------------------------------
# MAIN LAYOUT: Map (left) + Inspect/Prediction (right)
# -------------------------------------------------
left_col, right_col = st.columns([2, 1])

# ===========================
# LEFT: Map & Table
# ===========================
with left_col:
    st.subheader(" Map of Restaurants")

    # Toggle Google mode
    google_mode = st.toggle("Enable Google Nearby Search", key="google_mode")
    prev_mode = st.session_state.get("prev_google_mode", google_mode)
    if prev_mode != google_mode:
        # Mode changed → reset click + nearby data
        st.session_state["prev_google_mode"] = google_mode
        st.session_state["map_click"] = None
        st.session_state["last_processed_click"] = None
        st.session_state["google_nearby"] = []
        st.session_state["google_restaurant_nearby"] = None

    if len(df_filtered) == 0:
        st.info("No restaurants match your filters.")
    else:
        # 1. Default center based on filtered data
        default_center = [
            df_filtered["latitude"].mean(),
            df_filtered["longitude"].mean(),
        ]

        # 2. Decide center & zoom
        if st.session_state.get("just_selected_restaurant"):
            center = st.session_state["map_center"]
            zoom = st.session_state["map_zoom"]
            st.session_state["just_selected_restaurant"] = False
        else:
            center = st.session_state.get("map_center", default_center)
            zoom = st.session_state.get("map_zoom", 12)

        # 3. Prepare data for map
        df_for_map = df_filtered.head(2000)
        google_data = st.session_state.get("google_nearby", [])

        # 4. Build map
        @st.cache_data(show_spinner=False)
        def cached_build_map(center, zoom, df_for_map, google_data, google_mode):
            return build_map(center, zoom, df_for_map, google_data, google_mode)

        m = cached_build_map(center, zoom, df_for_map, google_data, google_mode)


        # 5. Render map
        map_data = st_folium(
            m,
            width="100%",
            height=500,
            key="main_map",
            returned_objects=["last_clicked", "center", "zoom"],
        )

        # 6. Update center/zoom based on user interactions
        if map_data:
            new_center = map_data.get("center")
            new_zoom = map_data.get("zoom")

            if new_center and tuple(new_center.values()) != tuple(center):
                st.session_state["map_center"] = [new_center["lat"], new_center["lng"]]

            if new_zoom:
                st.session_state["map_zoom"] = new_zoom

        # 7. Handle map clicks (stable version — NO st.stop, NO refresh loop)
        if map_data and map_data.get("last_clicked"):
            click = (
                map_data["last_clicked"]["lat"],
                map_data["last_clicked"]["lng"],
            )

            # Process only new clicks
            if st.session_state.get("last_processed_click") != click:
                st.session_state["last_processed_click"] = click
                st.session_state["map_click"] = click

                if google_mode:
                    # Google mode → fetch nearby places
                    with st.spinner("🔍 Searching nearby restaurants..."):
                        places = google_nearby_restaurants(click[0], click[1])
                    st.session_state["google_nearby"] = places
                else:
                    # dataset mode → clear previous google results
                    st.session_state["google_nearby"] = []

                # IMPORTANT: no st.stop(), no rerun loop


        # 8. Table of filtered restaurants
        st.markdown("### Restaurants in this area")

        cols = ["dba", "boro", "borough", "zipcode", "cuisine_description", "grade", "score"]
        cols = [c for c in cols if c in df_filtered.columns]

        st.dataframe(
            df_filtered[cols].reset_index(drop=True),
            use_container_width=True,
            height=300,
        )

# ===========================
# RIGHT: Inspect & Predict
# ===========================

with right_col:
    st.subheader(" Inspect & Predict")

    google_mode = st.session_state.get("google_mode", False)
    click = st.session_state.get("map_click")

    # ----------------------------------------------
    # CASE 1 — No click at all
    # ----------------------------------------------
    if click is None:
        st.info("Select a restaurant or click the map to begin.")
        st.session_state["just_selected_restaurant"] = False
        st.session_state["last_processed_click"] = None
        # Do NOT rerun
        # Do NOT return
        pass

    else:
        clat, clon = click

        # ----------------------------------------------
        # PRIORITY 1 — Dataset mode selection
        # ----------------------------------------------
        if not google_mode and len(df_filtered) > 0:

            closest_row = None
            min_ds_dist = float("inf")

            for _, row in df_filtered.iterrows():
                lat = row.get("latitude")
                lon = row.get("longitude")
                if pd.isna(lat) or pd.isna(lon):
                    continue

                d2 = _dist2(clat, clon, lat, lon)
                if d2 < min_ds_dist:
                    min_ds_dist = d2
                    closest_row = row

            if closest_row is not None and min_ds_dist < 0.00002:

                st.session_state["just_selected_restaurant"] = True

                st.markdown("## 🍽️ Dataset Restaurant Selected")

                name = closest_row.get("DBA") or closest_row.get("dba", "Unknown")
                borough = closest_row.get("boro") or closest_row.get("borough")
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
                    unsafe_allow_html=True,
                )

                st.markdown("#### Confidence")
                for g_label, p in probs.items():
                    st.write(f"{g_label}: {p * 100:.1f}%")

                st.session_state["map_click"] = None

                # NO RETURN, NO RERUN
                # let the script finish normally

        # ----------------------------------------------
        # PRIORITY 2 — Google nearby selection
        # ----------------------------------------------
        elif google_mode and st.session_state.get("google_nearby"):

            closest_place = None
            min_nb_dist = float("inf")

            for place in st.session_state["google_nearby"]:
                plat = place["geometry"]["location"]["lat"]
                plon = place["geometry"]["location"]["lng"]
                d2 = _dist2(clat, clon, plat, plon)
                if d2 < min_nb_dist:
                    min_nb_dist = d2
                    closest_place = place

            if closest_place is not None and min_nb_dist < 0.00002:

                st.session_state["just_selected_restaurant"] = True

                st.markdown("## 🍽️ Google Nearby Restaurant Selected")

                details = google_place_details(closest_place["place_id"])
                norm = normalize_place_to_restaurant(details)

                st.session_state["google_restaurant_nearby"] = norm

                cuisine = norm.get("cuisine_description", "Other")

                st.write(f"**Name:** {norm['name']}")
                st.write(f"**Address:** {norm['address']}")
                st.write(f"**ZIP:** {norm['zipcode']}")
                st.write(f"**Borough:** {norm.get('boro', 'Unknown')}")
                st.write(f"**Cuisine:** {cuisine}")

                pred = predict_from_raw_restaurant(norm)
                grade = pred["grade"]
                probs = pred["probabilities"]
                color = get_grade_color(grade)

                st.markdown(
                    f"### ⭐ Predicted Grade: "
                    f"<span style='color:{color}; font-size:24px; font-weight:bold'>{grade}</span>",
                    unsafe_allow_html=True,
                )

                st.markdown("#### Confidence")
                for g_label, p in probs.items():
                    st.write(f"{g_label}: {p * 100:.1f}%")

                st.session_state["map_click"] = None

        # ----------------------------------------------
        # PRIORITY 3 — Plain map click
        # ----------------------------------------------
        else:
            zipcode, borough, address = reverse_geocode(clat, clon)

            st.markdown("## 📍 Map Click Detected")
            st.write(f"**Address:** {address or 'Unknown'}")
            st.write(f"**ZIP:** {zipcode or 'Unknown'}")
            st.write(f"**Borough:** {borough or 'Unknown'}")
            st.info("Click a restaurant marker to see the predicted grade.")

            st.session_state["map_click"] = None





# -------------------------------------------------
# 📊 Insights Section
# -------------------------------------------------
st.markdown("---")
st.header("📊 Insights")

col1, col2 = st.columns(2)

# ---- Grade Distribution (Pie Chart) ----
with col1:
    if "grade" in df_filtered.columns and len(df_filtered) > 0:
        grade_counts = (
            df_filtered["grade"]
            .value_counts()
            .reset_index()
        )
        grade_counts.columns = ["grade", "count"]

        pie = (
            alt.Chart(grade_counts)
            .mark_arc()
            .encode(
                theta=alt.Theta("count:Q"),
                color=alt.Color("grade:N"),
                tooltip=["grade:N", "count:Q"],
            )
        )

        st.altair_chart(pie, width="content")
    else:
        st.info("No grade data available for the current filter.")

# ---- Most Common Violations (Bar Chart) ----
with col2:
    if "violation_code" in df_filtered.columns and len(df_filtered) > 0:
        violation_counts = (
            df_filtered["violation_code"]
            .value_counts()
            .reset_index()
        )
        violation_counts.columns = ["violation_code", "count"]

        violation_counts["description"] = violation_counts["violation_code"].apply(
            lambda code: VIOLATION_SHORT.get(code, UNKNOWN_VIOLATION_LABEL)
        )

        violation_counts = violation_counts.head(10)

        if len(violation_counts) == 0:
            st.info("No violation data available for this filter.")
        else:
            chart_violations = (
                alt.Chart(violation_counts)
                .mark_bar()
                .encode(
                    x=alt.X("violation_code:N", sort="-y", title="Violation Code"),
                    y=alt.Y("count:Q", title="Count"),
                    color=alt.Color("violation_code:N", legend=None),
                    tooltip=[
                        "violation_code:N",
                        "description:N",
                        "count:Q",
                    ],
                )
                .properties(height=350)
            )

            st.altair_chart(chart_violations, width="content")
    else:
        st.info("No violation data available for this filter.")

# ---- Best & Worst Cuisines (Side-by-side Bar Charts) ----
st.subheader("Best & Worst Cuisine Types")

cuisine_scores = None
best_cuisines = None
worst_cuisines = None

if "cuisine_description" in df_filtered.columns and len(df_filtered) > 0:
    cuisine_scores = (
        df_filtered.groupby("cuisine_description")["score"]
        .mean()
        .sort_values()
    )

    if len(cuisine_scores) == 0:
        st.info("No cuisine data available for this filter.")
        cuisine_scores = None
    else:
        best_cuisines = cuisine_scores.head(10)
        worst_cuisines = cuisine_scores.tail(10).sort_values(ascending=False)
else:
    st.info("No cuisine data available for this filter.")
    cuisine_scores = None

if cuisine_scores is not None:
    c1, c2 = st.columns(2)

    # Best cuisines
    with c1:
        st.markdown("#### 🥇 Top 10 Best Cuisines")

        best_df = best_cuisines.reset_index()
        best_df.columns = ["cuisine_description", "score"]

        chart_best = (
            alt.Chart(best_df)
            .mark_bar()
            .encode(
                x=alt.X("cuisine_description:N", sort="-y", title="Cuisine"),
                y=alt.Y("score:Q", title="Average Score"),
                color=alt.Color("cuisine_description:N", legend=None),
                tooltip=["cuisine_description:N", "score:Q"],
            )
            .properties(height=300)
        )

        st.altair_chart(chart_best, width="content")

    # Worst cuisines
    with c2:
        st.markdown("#### 🚨 Top 10 Worst Cuisines")

        worst_df = worst_cuisines.reset_index()
        worst_df.columns = ["cuisine_description", "score"]

        chart_worst = (
            alt.Chart(worst_df)
            .mark_bar()
            .encode(
                x=alt.X("cuisine_description:N", sort="-y", title="Cuisine"),
                y=alt.Y("score:Q", title="Average Score"),
                color=alt.Color("cuisine_description:N", legend=None),
                tooltip=["cuisine_description:N", "score:Q"],
            )
            .properties(height=300)
        )

        st.altair_chart(chart_worst, width="content")
else:
    st.info("No cuisine ranking to display.")
