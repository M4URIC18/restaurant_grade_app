# pages/2_Filter.py

import streamlit as st
import altair as alt
import pandas as pd

from src.data_loader import get_data
from src.utils import VIOLATION_SHORT, UNKNOWN_VIOLATION_LABEL, get_grade_color

# -------------------------------------------------
# Load data
# -------------------------------------------------
df = get_data()

st.title("Filter & Insights")

st.markdown(
    """
Use the filters on the left to narrow down NYC restaurants, 
then explore grade patterns, violations, and cuisine rankings.
"""
)

st.markdown("---")

# -------------------------------------------------
# Sidebar Filters (with explicit keys)
# -------------------------------------------------
st.sidebar.header("Filters")

# Widget keys (so we can reset them)
BOROUGH_KEY = "filter_borough"
CUISINE_KEY = "filter_cuisine"
ZIP_KEY = "filter_zipcode"
CRIT_KEY = "filter_critical"
SCORE_KEY = "filter_score_range"

# Boroughs
if "boro" in df.columns:
    all_boros = sorted(df["boro"].dropna().unique())
    selected_boros = st.sidebar.multiselect(
        "Borough",
        options=all_boros,
        key=BOROUGH_KEY,
    )
else:
    selected_boros = []
    st.sidebar.info("No borough column found in data.")

# Cuisine
if "cuisine_description" in df.columns:
    all_cuisines = sorted(df["cuisine_description"].dropna().unique())
    selected_cuisines = st.sidebar.multiselect(
        "Cuisine",
        options=all_cuisines,
        key=CUISINE_KEY,
    )
else:
    selected_cuisines = []
    st.sidebar.info("No cuisine column found in data.")

# Zipcode
if "zipcode" in df.columns:
    # ensure string for consistent filter
    df["zipcode"] = df["zipcode"].astype(str)
    all_zips = sorted(df["zipcode"].dropna().unique())
    selected_zips = st.sidebar.multiselect(
        "ZIP Code",
        options=all_zips,
        key=ZIP_KEY,
    )
else:
    selected_zips = []
    st.sidebar.info("No zipcode column found in data.")

# Score range
if "score" in df.columns:
    min_score = int(df["score"].min())
    max_score = int(df["score"].max())
    score_range = st.sidebar.slider(
        "Inspection Score Range",
        min_value=min_score,
        max_value=max_score,
        value=(min_score, max_score),
        key=SCORE_KEY,
    )
else:
    score_range = None
    st.sidebar.info("No score column found in data.")



# Critical flag (works with critical_flag or critical_flag_bin)
critical_col = None
if "critical_flag_bin" in df.columns:
    critical_col = "critical_flag_bin"
elif "critical_flag" in df.columns:
    critical_col = "critical_flag"

critical_choice = "All"
if critical_col is not None:
    critical_choice = st.sidebar.radio(
        "Critical Violations",
        options=["All", "Critical only", "Non-critical only"],
        key=CRIT_KEY,
    )
else:
    st.sidebar.info("No critical flag column found in data.")


# -------------------------------------------------
# Clear Filters Button
# -------------------------------------------------
if st.sidebar.button("Clear filters"):
    # Remove widget state so they reset to defaults
    for key in [BOROUGH_KEY, CUISINE_KEY, ZIP_KEY, SCORE_KEY, CRIT_KEY]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# -------------------------------------------------
# Apply Filters
# -------------------------------------------------
df_filtered = df.copy()

# Borough filter
if selected_boros:
    df_filtered = df_filtered[df_filtered["boro"].isin(selected_boros)]

# Cuisine filter
if selected_cuisines:
    df_filtered = df_filtered[df_filtered["cuisine_description"].isin(selected_cuisines)]

# ZIP filter
if selected_zips and "zipcode" in df_filtered.columns:
    df_filtered["zipcode"] = df_filtered["zipcode"].astype(str)
    df_filtered = df_filtered[df_filtered["zipcode"].isin(selected_zips)]

# Score filter
if score_range is not None and "score" in df_filtered.columns:
    low, high = score_range
    df_filtered = df_filtered[
        (df_filtered["score"] >= low) & (df_filtered["score"] <= high)
    ]

st.write("Unique critical_flag values:", df["critical_flag"].unique().tolist())
# Critical filter
if critical_col is not None and critical_choice != "All":
    if critical_choice == "Critical only":
        df_filtered = df_filtered[df_filtered[critical_col] == 1]
    elif critical_choice == "Non-critical only":
        df_filtered = df_filtered[df_filtered[critical_col] == 0]


# -------------------------------------------------
# Summary
# -------------------------------------------------
st.markdown("<h3 style='text-align:center;'>Current Filter Summary</h3>", unsafe_allow_html=True)

st.markdown("---")

total = len(df)
current = len(df_filtered)

st.markdown(
    f"""
    <p style='text-align:center; font-size:18px;'>
        Showing <strong>{current}</strong> restaurants out of <strong>{total}</strong> total.
    </p>
    """,
    unsafe_allow_html=True
)


if current == 0:
    st.warning("No data matches your filters. Try relaxing the filters.")
    st.stop()

# -------------------------------------------------
# Layout: Overview metrics + charts
# -------------------------------------------------
col1, col2 = st.columns(2)

# ---- Grade distribution ----
with col1:
    st.subheader("Grade Distribution")
    if "grade" in df_filtered.columns:
        grade_counts = (
            df_filtered["grade"]
            .value_counts()
            .reset_index()
        )
        grade_counts.columns = ["grade", "count"]

        chart = (
            alt.Chart(grade_counts)
            .mark_arc()
            .encode(
                theta=alt.Theta("count:Q", stack=True),
                color=alt.Color("grade:N"),
                tooltip=["grade:N", "count:Q"],
            )
        )
        st.altair_chart(chart, width="stretch")
    else:
        st.info("No grade column in current data.")

# ---- Average score by borough ----
with col2:
    st.subheader("Average Score by Borough")
    if "boro" in df_filtered.columns and "score" in df_filtered.columns:
        boro_scores = (
            df_filtered.groupby("boro")["score"]
            .mean()
            .reset_index()
            .sort_values("score")
        )

        chart_boro = (
            alt.Chart(boro_scores)
            .mark_bar()
            .encode(
                x=alt.X("boro:N", sort="-y", title="Borough"),
                y=alt.Y("score:Q", title="Average Score"),
                tooltip=["boro:N", "score:Q"],
                color=alt.Color("boro:N", legend=None),
            )
            .properties(height=300)
        )

        st.altair_chart(chart_boro, width="stretch")
    else:
        st.info("No borough/score data to plot.")

# -------------------------------------------------
# Most common violations
# -------------------------------------------------
st.markdown("---")
st.subheader("Top Violations")

if "violation_code" in df_filtered.columns:
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

    chart_viol = (
        alt.Chart(violation_counts)
        .mark_bar()
        .encode(
            x=alt.X("violation_code:N", sort="-y", title="Violation Code"),
            y=alt.Y("count:Q", title="Count"),
            tooltip=["violation_code:N", "description:N", "count:Q"],
            color=alt.Color("violation_code:N", legend=None),
        )
        .properties(height=350)
    )

    st.altair_chart(chart_viol, width="stretch")
else:
    st.info("No violation_code column in current data.")

st.markdown("---")
# -------------------------------------------------
# Best & Worst Cuisines
# -------------------------------------------------

st.markdown("<h3 style='text-align:center;'>Best & Worst Cuisines (Average Score)</h3>", unsafe_allow_html=True)
st.markdown("---")

if "cuisine_description" in df_filtered.columns and "score" in df_filtered.columns:
    cuisine_scores = (
        df_filtered.groupby("cuisine_description")["score"]
        .mean()
        .sort_values()
    )

    if len(cuisine_scores) == 0:
        st.info("No cuisine data for current filters.")
    else:
        best_cuisines = cuisine_scores.head(10)
        worst_cuisines = cuisine_scores.tail(10).sort_values(ascending=False)


        
        st.markdown("#### 🥇 Top 10 Best Cuisines")
        best_df = best_cuisines.reset_index()
        best_df.columns = ["cuisine_description", "score"]

        chart_best = (
            alt.Chart(best_df)
            .mark_bar()
            .encode(
                x=alt.X("cuisine_description:N", sort="-y", title="Cuisine"),
                y=alt.Y("score:Q", title="Average Score (lower is better)"),
                tooltip=["cuisine_description:N", "score:Q"],
                color=alt.Color("cuisine_description:N", legend=None),
            )
            .properties(height=300)
        )
        st.altair_chart(chart_best, width="stretch")

        
        st.markdown("#### 🚨 Top 10 Worst Cuisines")
        worst_df = worst_cuisines.reset_index()
        worst_df.columns = ["cuisine_description", "score"]

        chart_worst = (
            alt.Chart(worst_df)
            .mark_bar()
            .encode(
                x=alt.X("cuisine_description:N", sort="-y", title="Cuisine"),
                y=alt.Y("score:Q", title="Average Score (higher is worse)"),
                tooltip=["cuisine_description:N", "score:Q"],
                color=alt.Color("cuisine_description:N", legend=None),
            )
            .properties(height=300)
        )
        st.altair_chart(chart_worst, width="stretch")
else:
    st.info("Not enough data to rank cuisines.")
