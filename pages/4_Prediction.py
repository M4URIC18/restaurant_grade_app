import streamlit as st
from streamlit_folium import st_folium
import folium
import pandas as pd

# ==== IMPORT YOUR INTERNAL FUNCTIONS/MODELS ====
from src.predictor import predict_from_raw_restaurant
from src.utils import get_grade_color, _dist2
from src.data_loader import load_model_data
from src.google import google_place_details, normalize_place_to_restaurant, reverse_geocode

# Load your main dataset
df_all = load_model_data()

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="Restaurant Prediction",
    layout="wide",
)

st.title("🍽️ NYC Restaurant Grade Predictor")

# ================================
# SIDEBAR — FILTERS
# ================================
st.sidebar.header("🔎 Filters")

borough_choice = st.sidebar.multiselect(
    "Borough",
    options=sorted(df_all["borough"].dropna().unique()),
)

cuisine_choice = st.sidebar.multiselect(
    "Cuisine",
    options=sorted(df_all["cuisine_description"].dropna().unique()),
)

zip_choice = st.sidebar.multiselect(
    "Zip Code",
    options=sorted(df_all["zipcode"].dropna().unique()),
)

google_mode = st.sidebar.checkbox(
    "Use Google Nearby Results (instead of dataset markers)",
    value=False
)

if st.sidebar.button("Reset Filters"):
    st.session_state["filters_reset"] = True
    st.rerun()

# Filter dataset
df_filtered = df_all.copy()

if borough_choice:
    df_filtered = df_filtered[df_filtered["borough"].isin(borough_choice)]

if cuisine_choice:
    df_filtered = df_filtered[df_filtered["cuisine_description"].isin(cuisine_choice)]

if zip_choice:
    df_filtered = df_filtered[df_filtered["zipcode"].isin(zip_choice)]

# ================================
# MAP + PREDICTION LAYOUT
# ================================
left_col, right_col = st.columns([1.8, 1])

# -------------------------
# LEFT COLUMN — MAP
# -------------------------
with left_col:
    st.subheader("🗺️ Map")

    # Map center defaults
    default_lat, default_lon = 40.7128, -74.0060

    m = folium.Map(
        location=[default_lat, default_lon],
        zoom_start=12,
        control_scale=True,
    )

    # Add dataset markers (optional depending on Google mode)
    if not google_mode:
        for _, row in df_filtered.iterrows():
            if pd.isna(row["latitude"]) or pd.isna(row["longitude"]):
                continue

            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=3,
                color="blue",
                fill=True,
                fill_opacity=0.6,
                popup=row.get("DBA", "Restaurant"),
            ).add_to(m)

    # Show map & capture click
    map_output = st_folium(m, height=550, width="100%", returned_objects=["last_clicked"])

    click = None
    if map_output and map_output.get("last_clicked"):
        click = (
            map_output["last_clicked"]["lat"],
            map_output["last_clicked"]["lng"]
        )
        st.session_state["map_click"] = click

# -------------------------
# RIGHT COLUMN — Prediction Panel
# Dynamic → appears ONLY when user selects
# -------------------------
with right_col:
    click = st.session_state.get("map_click")

    if click is None:
        st.info("Select a restaurant on the map to see prediction.")
        st.stop()

    clat, clon = click

    # =================================
    # PRIORITY 1 — Dataset Restaurant
    # =================================
    if not google_mode:
        closest_row = None
        min_dist = float("inf")

        for _, row in df_filtered.iterrows():
            if pd.isna(row["latitude"]) or pd.isna(row["longitude"]):
                continue

            d2 = _dist2(clat, clon, row["latitude"], row["longitude"])
            if d2 < min_dist:
                min_dist = d2
                closest_row = row

        if closest_row is not None and min_dist < 0.00002:
            st.markdown("## 🍽️ Dataset Restaurant Selected")

            name = closest_row.get("DBA") or closest_row.get("dba")
            borough = closest_row.get("borough")
            zipcode = closest_row.get("zipcode")
            cuisine = closest_row.get("cuisine_description")
            score = closest_row.get("score")
            crit = closest_row.get("critical_flag_bin")

            st.write(f"**Name:** {name}")
            st.write(f"**Borough:** {borough}")
            st.write(f"**ZIP:** {zipcode}")
            st.write(f"**Cuisine:** {cuisine}")
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
                f"<span style='color:{color}; font-size:26px; font-weight:bold'>{grade}</span>",
                unsafe_allow_html=True,
            )

            st.markdown("#### Confidence")
            for g, p in probs.items():
                st.write(f"{g}: {p*100:.1f}%")

            st.stop()

    # =================================
    # PRIORITY 2 — Google Nearby
    # =================================
    if google_mode:
        st.warning("Google Mode UI Here (same logic as before).")
        st.stop()

    # =================================
    # PRIORITY 3 — Blank click
    # =================================
    zipcode, borough, address = reverse_geocode(clat, clon)

    st.markdown("## 📍 Location Clicked")
    st.write(f"**Address:** {address or 'Unknown'}")
    st.write(f"**ZIP:** {zipcode or 'Unknown'}")
    st.write(f"**Borough:** {borough or 'Unknown'}")
    st.info("Click a restaurant marker to see predicted grade.")
