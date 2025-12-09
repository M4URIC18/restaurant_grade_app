# pages/2_Filter.py

import streamlit as st
import pandas as pd
import altair as alt

from src.data_loader import get_data
from src.utils import (
    VIOLATION_SHORT,
    UNKNOWN_VIOLATION_LABEL,
    get_grade_color
)

# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(page_title="Filter & Analytics", layout="wide")

st.title("🔍 Filter & Analyze NYC Restaurants")
st.write(
    "Use the filters on the left to narrow restaurants and explore insights. "
    "Charts update automatically based on your selections."
)

# ==========================================================
# LOAD DATA
# ==========================================================
df = get_data()

# Safety guard
if df is None or len(df) == 0:
    st.error("❌ Could not load restaurant dataset.")
    st.stop()

# ==========================================================
# SIDEBAR FILTERS
# ==========================================================
st.sidebar.header("📌 Filters")

# ---- Borough filter ----
boroughs = sorted(df["borough"].dropna().unique())
select_borough = st.sidebar.multiselect(
    "Borough",
    boroughs,
    default=boroughs
)

# ---- ZIP filter ----
valid_zip_df = df[df["borough"].isin(select_borough)]
zips = sorted(valid_zip_df["zipcode"].dropna().unique().astype(str))

select_zip = st.sidebar.multiselect(
    "ZIP Codes",
    zips,
    default=zips[:20]  # avoid selecting thousands at once
)

# ---- Cuisine filter ----
cuisines = sorted(df["cuisine_description"].dropna().unique())
select_cuisine = st.sidebar.multiselect(
    "Cuisine Type",
    cuisines,
)

# ---- Score range filter ----
min_score = float(df["score"].min())
max_score = float(df["score"].max())

score_range = st.sidebar.slider(
    "Inspection Score Range",
    min_score,
    max_score,
    (min_score, max_score),
)

# ---- Critical flag filter ----
crit_vals = ["0 (Not Critical)", "1 (Critical)"]
select_critical = st.sidebar.multiselect(
    "Critical Flag",
    crit_vals,
)

# ---- Reset button ----
if st.sidebar.button("🔄 Reset Filters"):
    st.rerun()

# ==========================================================
# APPLY FILTERS
# ==========================================================
df_filtered = df.copy()

if select_borough:
    df_filtered = df_filtered[df_filtered["borough"].isin(select_borough)]

if select_zip:
    df_filtered = df_filtered[df_filtered["zipcode"].astype(str).isin(select_zip)]

if select_cuisine:
    df_filtered = df_filtered[df_filtered["cuisine_description"].isin(select_cuisine)]

# Score filter
df_filtered = df_filtered[
    (df_filtered["score"] >= score_range[0]) &
    (df_filtered["score"] <= score_range[1])
]

# Critical flag filter
if select_critical:
    crit_map = {
        "0 (Not Critical)": 0,
        "1 (Critical)": 1
    }
    df_filtered = df_filtered[
        df_filtered["critical_flag_bin"].isin([crit_map[i] for i in select_critical])
    ]

# ==========================================================
# TOP INFO CARDS
# ==========================================================
st.markdown("---")
st.subheader("📊 Summary")

colA, colB, colC, colD = st.columns(4)

total_rest = len(df_filtered)
avg_score = df_filtered["score"].mean() if total_rest > 0 else 0
top_cuisine = (
    df_filtered["cuisine_description"].value_counts().idxmax()
    if total_rest > 0 else "N/A"
)
borough_count = df_filtered["borough"].value_counts().to_dict()

# Card A
colA.metric("Total Restaurants", f"{total_rest:,}")

# Card B
colB.metric("Average Score", f"{avg_score:.1f}")

# Card C
colC.metric("Top Cuisine", top_cuisine)

# Card D
colD.write("**Borough Count:**")
for boro, ct in borough_count.items():
    colD.write(f"- {boro}: {ct}")

# If nothing is found
if total_rest == 0:
    st.warning("⚠️ No restaurants match your filters.")
    st.stop()

# ==========================================================
# CHARTS — ANALYTICS DASHBOARD
# ==========================================================
st.markdown("---")
st.header("📈 Analytics Dashboard")

# ====================================================================
# 1. Grade Distribution Pie Chart
# ====================================================================
st.subheader("🎯 Grade Distribution")

if "grade" in df_filtered.columns:
    grade_counts = df_filtered["grade"].value_counts().reset_index()
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

    st.altair_chart(pie, use_container_width=True)
else:
    st.info("No grade data available.")

# ====================================================================
# 2. Violation Breakdown
# ====================================================================
st.subheader("⚠️ Most Common Violations")

if "violation_code" in df_filtered.columns:
    violation_counts = df_filtered["violation_code"].value_counts().reset_index()
    violation_counts.columns = ["violation_code", "count"]

    violation_counts["description"] = violation_counts["violation_code"].apply(
        lambda code: VIOLATION_SHORT.get(code, UNKNOWN_VIOLATION_LABEL)
    )

    violation_counts = violation_counts.head(10)

    chart_violations = (
        alt.Chart(violation_counts)
        .mark_bar()
        .encode(
            x=alt.X("violation_code:N", sort="-y", title="Violation Code"),
            y=alt.Y("count:Q", title="Count"),
            color=alt.Color("violation_code:N", legend=None),
            tooltip=["violation_code:N", "description:N", "count:Q"],
        )
        .properties(height=350)
    )

    st.altair_chart(chart_violations, use_container_width=True)
else:
    st.info("No violation data available.")

# ====================================================================
# 3. Score Distribution Histogram
# ====================================================================
st.subheader("📉 Score Distribution")

hist = (
    alt.Chart(df_filtered)
    .mark_bar()
    .encode(
        x=alt.X("score:Q", bin=True, title="Score"),
        y=alt.Y("count()", title="Count"),
        tooltip=["score:Q"]
    )
    .properties(height=300)
)

st.altair_chart(hist, use_container_width=True)

# ====================================================================
# 4. Cuisine Ranking
# ====================================================================
st.subheader("🍽️ Best & Worst Cuisine Types")

cuisine_scores = (
    df_filtered.groupby("cuisine_description")["score"].mean().sort_values()
)

best = cuisine_scores.head(10).reset_index()
best.columns = ["cuisine_description", "score"]

worst = cuisine_scores.tail(10).sort_values(ascending=False).reset_index()
worst.columns = ["cuisine_description", "score"]

c1, c2 = st.columns(2)

with c1:
    st.markdown("#### 🥇 Best 10 Cuisines")
    chart_best = (
        alt.Chart(best)
        .mark_bar()
        .encode(
            x=alt.X("cuisine_description:N", sort="-y", title="Cuisine"),
            y=alt.Y("score:Q", title="Average Score"),
            tooltip=["cuisine_description:N", "score:Q"],
        )
        .properties(height=300)
    )
    st.altair_chart(chart_best, use_container_width=True)

with c2:
    st.markdown("#### 🚨 Worst 10 Cuisines")
    chart_worst = (
        alt.Chart(worst)
        .mark_bar()
        .encode(
            x=alt.X("cuisine_description:N", sort="-y", title="Cuisine"),
            y=alt.Y("score:Q", title="Average Score"),
            tooltip=["cuisine_description:N", "score:Q"],
        )
        .properties(height=300)
    )
    st.altair_chart(chart_worst, use_container_width=True)

# ====================================================================
# 5. Borough Comparison
# ====================================================================
st.subheader("🏙️ Borough Comparison")

borough_chart = (
    alt.Chart(df_filtered)
    .mark_bar()
    .encode(
        x=alt.X("borough:N", title="Borough"),
        y=alt.Y("mean(score):Q", title="Average Score"),
        tooltip=["borough:N", "mean(score):Q"]
    )
    .properties(height=300)
)

st.altair_chart(borough_chart, use_container_width=True)

