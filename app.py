import streamlit as st
import pandas as pd
import folium
import os
import requests
import altair as alt


from streamlit_folium import st_folium

from src.data_loader import get_data
from src.predictor import predict_from_raw_restaurant
from src.utils import (
    get_grade_color,
    format_probabilities,
    row_to_model_input,
    restaurant_popup_html,
    normalize_text,
)
from src.places import (
    google_place_details,
    reverse_geocode,
    normalize_place_to_restaurant,
    google_nearby_restaurants,
)

# -------------------------------------------------
# 🔧 CLEAR SELECTIONS HELPER
# -------------------------------------------------
def clear_all_selections():
    st.session_state["google_restaurant"] = None
    st.session_state["google_restaurant_nearby"] = None
    st.session_state["map_click"] = None
    st.session_state["google_nearby"] = []

# -----------------------------
# Session State Initialization
# -----------------------------
if "map_center" not in st.session_state:
    st.session_state["map_center"] = (40.7128, -74.0060)  # NYC default

if "map_zoom" not in st.session_state:
    st.session_state["map_zoom"] = 12  # default zoom

if "just_selected_restaurant" not in st.session_state:
    st.session_state["just_selected_restaurant"] = False


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
    layout="wide",
)

st.title("CleanKitchen NYC")

# You can keep these or comment them out if noisy
st.write("🔑 Secret key exists:", bool(st.secrets.get("GOOGLE_MAPS_API_KEY")))
st.write("🔑 OS env key exists:", bool(os.environ.get("GOOGLE_MAPS_API_KEY")))

st.markdown(
    "Explore NYC restaurant inspections, neighborhood demographics, "
    "and **AI-powered grade predictions** based on real inspection data."
)

# -------------------------------------------------
# Load data (cached)
# -------------------------------------------------

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







def build_map(center, zoom, df_for_map, google_nearby_data):
    import folium

    # --- Always build a fresh map ---
    m = folium.Map(location=center, zoom_start=zoom, control_scale=True)

    # ==========================================================
    # FIX #1 — Create FeatureGroups to prevent mutation errors
    # ==========================================================
    dataset_fg = folium.FeatureGroup(name="Dataset Restaurants")
    google_fg = folium.FeatureGroup(name="Google Restaurants")

    # ---------------------------
    # Dataset markers
    # ---------------------------
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

    # ---------------------------
    # Google Places markers
    # ---------------------------
    for place in google_nearby_data:
        plat = place["geometry"]["location"]["lat"]
        plon = place["geometry"]["location"]["lng"]
        name = place.get("name", "Unknown")
        pid = place.get("place_id")

        selected = (
            st.session_state.get("google_restaurant_nearby")
            and st.session_state["google_restaurant_nearby"].get("place_id") == pid
        )

        tooltip_text = f"⭐ {name}" if selected else name
        radius = 8 if selected else 5
        color = "#ff8800" if selected else "#1e90ff"

        marker = folium.CircleMarker(
            location=[plat, plon],
            radius=radius,
            popup=name,
            color=color,
            fill=True,
            fill_opacity=0.9,
        )
        folium.Tooltip(tooltip_text).add_to(marker)
        marker.add_to(google_fg)

    # --- Add groups to the map (only AFTER fully built) ---
    dataset_fg.add_to(m)
    google_fg.add_to(m)

    return m







# -------------------------------------------------
# MAIN LAYOUT: Map (left) + Details/Prediction (right)
# -------------------------------------------------
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader(" Map of Restaurants")

    if len(df_filtered) == 0:
        st.info("No restaurants match your filters.")
    else:
        # ----------------------------------------------------
        # 1. Compute default center (ONLY if we have no memory)
        # ----------------------------------------------------
        default_center = [
            df_filtered["latitude"].mean(),
            df_filtered["longitude"].mean()
        ]

        # ----------------------------------------------------
        # 2. Decide center & zoom (DO NOT override later)
        # ----------------------------------------------------
        
        # CASE A — Just selected a restaurant → force zoom + center
        if st.session_state.get("just_selected_restaurant"):

            center = st.session_state["map_center"]
            zoom = st.session_state["map_zoom"]

            # Clear the flag AFTER using the values
            st.session_state["just_selected_restaurant"] = False

        else:
            # CASE B — Normal view → keep last position or default
            center = st.session_state.get("map_center", default_center)
            zoom = st.session_state.get("map_zoom", 12)

        # ⭐ IMPORTANT:
        # From this point on, 
        # DO NOT modify "center" or "zoom" anywhere else in the file!



        # Prepare data for map
        df_for_map = df_filtered.head(2000)
        google_data = st.session_state.get("google_nearby", [])



        # ---- 2. Build map (cached, fast) ----
        # if "last_map_inputs" not in st.session_state:
        #     st.session_state["last_map_inputs"] = None
        # if "last_map_object" not in st.session_state:
        #     st.session_state["last_map_object"] = None

        # current_inputs = {
        #     "center": tuple(center),
        #     "zoom": zoom,
        #     "df_count": len(df_for_map),
        #     "google_count": len(google_data),
        # }

        # if st.session_state["last_map_inputs"] != current_inputs:
        #     # Rebuild map only when inputs CHANGE
        #     m = build_map(center, zoom, df_for_map, google_data)
        #     st.session_state["last_map_object"] = m
        #     st.session_state["last_map_inputs"] = current_inputs
        # else:
        #     # Reuse the old map (NO FLICKER)
        #     m = st.session_state["last_map_object"]

        # ---- 2. Build map (always fresh Folium map) ----
        m = build_map(center, zoom, df_for_map, google_data)


        # ---- 3. Render map ----
        map_data = st_folium(
            m,
            width="100%",
            height=500,
            key="main_map",
            returned_objects=["last_clicked", "center", "zoom"]
        )
        

        # ---- TABLE OF FILTERED RESTAURANTS ----
        st.markdown("### Restaurants in this area")

        # Choose the columns to display (cleaner)
        cols = ["dba", "boro", "zipcode", "cuisine_description", "grade", "score"]

        # Only show columns that exist
        cols = [c for c in cols if c in df_filtered.columns]

        # Show the table (interactive, scrollable)
        st.dataframe(
            df_filtered[cols].reset_index(drop=True),
            use_container_width=True,
            height=300
        )



        # -------------------------------------------------
        # SMART ZOOM FREEZE — avoid rebuild only when zooming
        # -------------------------------------------------
        if map_data:
            new_zoom = map_data.get("zoom")
            new_click = map_data.get("last_clicked")

            # If zoom changed AND no new click → it's a zoom gesture
            # STOP ONLY IF user is manually zooming (not during selection click)
            if (
                new_zoom != zoom 
                and new_click is None 
                and not st.session_state.get("just_selected_restaurant")
            ):
                st.stop()





        # ---- 4. Update center/zoom (SAFE: ignore zoom changes during zooming) ----
        if map_data:
            new_center = map_data.get("center")
            new_zoom = map_data.get("zoom")

            # Only save center if user dragged (not zoom)
            if new_center and tuple(new_center.values()) != tuple(center):
                st.session_state["map_center"] = [new_center["lat"], new_center["lng"]]

            # DO NOT SAVE new zoom on every event, ONLY if user clicked a marker
            # Save zoom only when the user manually zooms (not selection)
            if (
                new_zoom 
                and not st.session_state.get("just_selected_restaurant")
            ):
                st.session_state["map_zoom"] = new_zoom



        # ---- 5. Handle NEW clicks ONLY ----
                # ---- 5. Handle NEW clicks ONLY ----
        if map_data and map_data.get("last_clicked"):
            click = (
                map_data["last_clicked"]["lat"],
                map_data["last_clicked"]["lng"]
            )

            # Prevent repeated triggers from Streamlit-Folium
            if st.session_state.get("last_processed_click") != click:
                st.session_state["last_processed_click"] = click
                st.session_state["map_click"] = click

                with st.spinner("🔍 Searching nearby restaurants..."):
                    places = google_nearby_restaurants(click[0], click[1])

                st.session_state["google_nearby"] = places
                st.session_state["google_restaurant_nearby"] = None
                st.session_state["google_restaurant"] = None

                # IMPORTANT: stop RIGHT COLUMN from running this cycle
                st.rerun()

        








with right_col:
    st.subheader(" Inspect & Predict")

    import requests

    # Safety defaults
    st.session_state.setdefault("google_nearby", [])
    st.session_state.setdefault("map_click", None)

    has_click = (
        st.session_state["map_click"] is not None
    )

    # Distance helper
    def _dist2(lat1, lon1, lat2, lon2):
        return (lat1 - lat2)**2 + (lon1 - lon2)**2


    # =================================================
    # PRIORITY 1 — Dataset restaurant (CSV) click
    # =================================================
    # =================================================
    # PRIORITY 1 — Dataset restaurant (CSV) click
    # =================================================
    if has_click and len(df_filtered) > 0:
        clat, clon = st.session_state["map_click"]

        closest_row = None
        min_ds_dist = float("inf")

        # ENABLED: find nearest **dataset** restaurant to the click
        for _, row in df_filtered.iterrows():
            lat = row.get("latitude")
            lon = row.get("longitude")
            if pd.isna(lat) or pd.isna(lon):
                continue

            d2 = _dist2(clat, clon, lat, lon)

            if d2 < min_ds_dist:
                min_ds_dist = d2
                closest_row = row

        # If close to a dataset marker, select it
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

            # Make prediction input
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

        # Close to a blue marker → select nearby restaurant
        if closest_place is not None and min_nb_dist < 0.00002:

            st.session_state["just_selected_restaurant"] = True

            st.markdown("## 🍽️ Google Nearby Restaurant Selected")

            details = google_place_details(closest_place["place_id"])
            norm = normalize_place_to_restaurant(details)

            st.session_state["google_restaurant_nearby"] = norm

            cuisine = norm.get("cuisine_description", "Other") or "Other"

            st.write(f"**Name:** {norm['name']}")
            st.write(f"**Address:** {norm['address']}")
            st.write(f"**ZIP:** {norm['zipcode']}")
            st.write(f"**Borough:** {norm.get('boro', 'Unknown')}")
            st.write(f"**Cuisine:** {cuisine}")

            # Predict
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
    # PRIORITY 3 — Plain map click (no prediction)
    # =================================================
    if has_click:
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
    st.info("Select a restaurant (dataset or blue marker) or click the map to begin.")



st.markdown("---")
st.header("📊 Insights")

# ---- Grade Distribution (Pie Chart) ----

st.subheader("Grade Distribution")

if "grade" in df_filtered.columns and len(df_filtered) > 0:

    # Build dataframe manually (prevents duplicate column names)
    grade_counts = (
        df_filtered["grade"]
        .value_counts()
        .reset_index()
    )
    grade_counts.columns = ["grade", "count"]  # FORCE unique names

    import altair as alt

    pie = (
        alt.Chart(grade_counts)
        .mark_arc()
        .encode(
            theta=alt.Theta("count:Q"),
            color=alt.Color("grade:N"),
            tooltip=["grade:N", "count:Q"]
        )
    )

    st.altair_chart(pie, use_container_width=True)

else:
    st.info("No grade data available for the current filter.")




# ---- Best & Worst Cuisines (Bar Charts) ----
st.subheader("Best & Worst Cuisine Types")

if "cuisine_description" in df_filtered.columns and len(df_filtered) > 0:
    # Compute average score per cuisine
    cuisine_scores = (
        df_filtered.groupby("cuisine_description")["score"]
        .mean()
        .sort_values()
    )

    # Best (lowest score)
    best_cuisines = cuisine_scores.head(10)

    # Worst (highest score)
    worst_cuisines = cuisine_scores.tail(10).sort_values(ascending=False)

else:
    st.info("Not enough cuisine data for ranking.")
    cuisine_scores = None




# ---- Best & Worst Cuisines (Bar Charts) ----
st.subheader("Best & Worst Cuisine Types")

if "cuisine_description" in df_filtered.columns and len(df_filtered) > 0:
    # Compute average score per cuisine
    cuisine_scores = (
        df_filtered.groupby("cuisine_description")["score"]
        .mean()
        .sort_values()
    )

    # If no cuisine left after filtering
    if len(cuisine_scores) == 0:
        st.info("No cuisine data available for this filter.")
    else:
        # Best (lowest score)
        best_cuisines = cuisine_scores.head(10)

        # Worst (highest score)
        worst_cuisines = cuisine_scores.tail(10).sort_values(ascending=False)

        # --------------- Best Cuisines ---------------
        st.markdown("#### 🥇 Top 10 Best Cuisines (Lowest Average Score)")

        best_df = best_cuisines.reset_index()
        best_df.columns = ["cuisine_description", "score"]

        chart_best = (
            alt.Chart(best_df)
            .mark_bar()
            .encode(
                x=alt.X("cuisine_description:N", sort="-y", title="Cuisine"),
                y=alt.Y("score:Q", title="Average Score"),
                color=alt.Color("cuisine_description:N", legend=None),
                tooltip=["cuisine_description:N", "score:Q"]
            )
            .properties(height=350)
        )

        st.altair_chart(chart_best, use_container_width=True)

        # --------------- Worst Cuisines ---------------
        st.markdown("#### 🚨 Top 10 Worst Cuisines (Highest Average Score)")

        worst_df = worst_cuisines.reset_index()
        worst_df.columns = ["cuisine_description", "score"]

        chart_worst = (
            alt.Chart(worst_df)
            .mark_bar()
            .encode(
                x=alt.X("cuisine_description:N", sort="-y", title="Cuisine"),
                y=alt.Y("score:Q", title="Average Score"),
                color=alt.Color("cuisine_description:N", legend=None),
                tooltip=["cuisine_description:N", "score:Q"]
            )
            .properties(height=350)
        )

        st.altair_chart(chart_worst, use_container_width=True)

else:
    # No rows after filtering → handle gracefully
    st.info("No cuisine data available for this filter.")





# ---- Most Common Violations ----
st.subheader("Most Common Violation Types")

# Ensure the column exists and dataframe not empty
if "violation_code" in df_filtered.columns and len(df_filtered) > 0:

    # Build violation count table
    violation_counts = (
        df_filtered["violation_code"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "violation_code", "violation_code": "count"})
    )

    # Show only top 10 most common violation codes
    violation_counts = violation_counts.head(10)

    if len(violation_counts) == 0:
        st.info("No violation data available for this filter.")
    else:
        # Proceed to chart (added next)
        chart_violations = (
            alt.Chart(violation_counts)
            .mark_bar()
            .encode(
                x=alt.X("violation_code:N", sort="-y", title="Violation Code"),
                y=alt.Y("count:Q", title="Count"),
                color=alt.Color("violation_code:N", legend=None),
                tooltip=["violation_code:N", "count:Q"]
            )
            .properties(height=350)
        )

        st.altair_chart(chart_violations, use_container_width=True)


else:
    st.info("No violation data available for this filter.")
