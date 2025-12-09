import streamlit as st

import pandas as pd
import altair as alt

from src.data_loader import get_data
from src.utils import VIOLATION_SHORT, UNKNOWN_VIOLATION_LABEL

df = get_data()




st.set_page_config(page_title="CleanKitchen Blog", layout="wide")

st.title("CleanKitchen NYC — Blog")
st.caption("Learn how the dataset was built, how the model works, and how predictions are made.")

st.markdown("---")

# ----------------------------------------------------------
# BLOG POSTS (clean paragraphs + bullet points)
# ----------------------------------------------------------

POSTS = {
    "Post 1 — Dataset Overview & Why Multiple Sources Were Needed": """
### **Dataset Overview & Why Multiple Sources Were Needed**

CleanKitchen NYC combines several datasets to create a strong prediction system.
Each dataset provides a different layer of insight.

#### **1. NYC Restaurant Inspection Dataset**
This is the main dataset, containing:
- Inspection scores
- Violation codes
- Violation descriptions
- Letter grades (A/B/C)
- Restaurant location (borough, ZIP code, coordinates)

This dataset forms the **core features** for the ML model.

#### **2. Neighborhood Financial Health Dataset (NFH)**
Adds neighborhood-level socioeconomic data:
- Poverty rate  
- Median income  
- Ethnicity mix  
- Financial health index  

It does not include ZIP codes, which introduces challenges during merging.

#### **3. ZIP Code Population Dataset**
Adds ZIP-level population and density.

Population helps model:
- How busy an area is
- Patterns in inspection frequency

#### **Why All 3 Are Needed**
Combining all datasets gives:
- Cleaner signals  
- Less noise  
- More stable predictions  
""",

    "Post 2 — Data Cleaning Pipeline (Step-by-Step)": """
### **Data Cleaning Pipeline (Step-by-Step)**

Data cleaning ensured the dataset was consistent and ready for ML.

#### **1. Removing Duplicates**
- Duplicate inspection rows were removed based on `camis`, `violation_code`, and `inspection_date`.

#### **2. Converting Dates**
Converted to datetime:
- `inspection_date`
- `grade_date`
- `record_date`

#### **3. Handling Missing Values**
- Missing ZIP → drop  
- Missing latitude/longitude → drop  
- Missing demographics → `demo_missing = 1`  
- Missing population → `pop_missing = 1`  

The missing flags help the model understand incomplete data.

#### **4. Converting Categorical Values**
Cleaned and standardized:
- borough  
- cuisine type  
- violation codes  
""",

    "Post 3 — The Merge Problem: ZIP Codes vs Neighborhoods": """
### **The Merge Problem: ZIP Codes vs Neighborhoods**

A major challenge was merging the demographic dataset.

#### ❌ **Problem**
The demographic dataset uses:
- Neighborhood names  
- Borough names  

But the inspection dataset uses:
- ZIP codes

This mismatch prevents a direct merge.

#### 🔧 **Solution**
We used a helper dataset that maps:
- ZIP codes → neighborhood names  

With this:
- Restaurants inherit demographic values from their neighborhood  

#### ⚠️ **Does This Reduce Accuracy?**
A little — but the benefits outweigh the mapping inaccuracy.

#### ✔️ **Why It Still Helps**
- ZIP codes and neighborhoods share similar economic patterns  
- Demographic trends help the model generalize  
- Socioeconomic features stabilize predictions under low data  
""",

    "Post 4 — Feature Engineering (17+ Inputs to the Model)": """
### **Feature Engineering (17+ Inputs to the Model)**

We created a rich feature vector for each restaurant.

#### **Numeric Features**
- inspection score  
- poverty rate  
- median income  
- percent race distribution  
- population  
- financial indexscore  

#### **Categorical Features**
- borough  
- ZIP code  
- cuisine description  
- violation code  

#### **Missing-Value Indicators**
- `pop_missing`  
- `demo_missing`  

These help the model avoid guessing during missing information.

#### **Result**
The model receives a complete 17+ feature set describing both:
- the restaurant  
- its neighborhood  
""",

    "Post 5 — Population Density Dataset: Why It Matters": """
### **Population Density Dataset: Why It Matters**

Adding population greatly improved dataset quality.

#### **1. High-Density ZIPs**
Such as Manhattan ZIPs:
- More customers  
- More inspections  
- More chances for violations  

#### **2. Low-Density ZIPs**
Such as Staten Island ZIPs:
- Fewer inspections  
- Cleaner records in many cases  

#### **3. `pop_missing` Indicator**
Missing population data taught the model:
> “Don’t depend heavily on demographics for this ZIP.”

#### **Overall Benefit**
Population adds context to inspection patterns and improves prediction stability.
""",

    "Post 6 — Model Training & Validation": """
### **Model Training & Validation**

#### **Why Random Forest?**
Random Forest works well because:
- It handles categorical + numeric values
- It handles missing flags
- It reduces overfitting
- It gives feature importance

#### **Most Important Features**
1. inspection score  
2. ZIP code  
3. critical_flag  
4. cuisine_description  
5. poverty rate  

This matches real inspection patterns.

#### **Validation Approach**
- Train-test split  
- Checked model stability  
- Evaluated prediction confidence  

The final model is reliable and robust.
""",

    "Post 7 — Prediction Pipeline End-to-End": """
### **Prediction Pipeline End-to-End**

Here's what happens when a user clicks a restaurant:

#### **1. Restaurant Selected**
Either from:
- DOHMH dataset  
- Google Places  

#### **2. Reverse Geocoding**
Extracts borough, ZIP code, and address for Google results.

#### **3. Data Normalization**
Google data is converted to match our model's expected format.

#### **4. Feature Vector Construction**
The system attaches:
- demographics  
- population  
- missing flags  

#### **5. Final Prediction**
Model outputs:
- grade prediction (A/B/C)  
- probabilities for each grade  

Fast and seamless.
""",

    "Post 8 — Lessons Learned": """
### **Lessons Learned**

#### **1. Merging Datasets Is Hard**
ZIPs and neighborhoods rarely align perfectly.
But the merge was still worthwhile.

#### **2. More Data ≠ Better Data**
Losing rows during merging improved:
- consistency  
- stability  
- clarity  

#### **3. Demographic + Population Features Help**
They improved accuracy even if imperfect.

#### **4. Next Steps**
- Real-time DOH updates  
- Neighborhood prediction pages  
- Cuisine-level health profiles  
- Expanded ML model  
"""
}

# ----------------------------------------------------------
# UI — Dropdown + Display Logic
# ----------------------------------------------------------

# 1) Initialize session_state keys
if "selected_post" not in st.session_state:
    st.session_state.selected_post = "-- Select a post --"

if "close_post_flag" not in st.session_state:
    st.session_state.close_post_flag = False

# 2) If we requested a reset on a previous run, do it NOW (before widget)
if st.session_state.close_post_flag:
    st.session_state.selected_post = "-- Select a post --"
    st.session_state.close_post_flag = False

# 3) Render the dropdown
selected = st.selectbox(
    "Select a post to read:",
    ["-- Select a post --"] + list(POSTS.keys()),
    key="selected_post",
)


# ----------------------------------------------------------
# Render post in a card
# ----------------------------------------------------------

if selected and selected != "-- Select a post --":
    st.markdown(
        """
        <div style='background:white; padding:15px; border-radius:12px;
        box-shadow:0 0 12px rgba(0,0,0,0.12); margin-bottom:20px;'>
        """,
        unsafe_allow_html=True
    )

    st.markdown(POSTS[selected], unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)



    # Close button — correctly resets a widget-controlled session_state key
    # 4) Close button — set a flag and rerun (do NOT touch selected_post here)
    if st.button("Close Post"):
        st.session_state.close_post_flag = True
        st.rerun()


else:
    st.info("Select a blog post from the dropdown to view details.")











st.markdown("---")
st.markdown("## 🔮 Future Improvements")

st.write("""
The current version of *CleanKitchen NYC* predicts restaurant health grades using
inspection scores, violation codes, demographics, and population patterns.
Below are improvements planned for future versions to enhance prediction accuracy,
explainability, and user experience.
""")

# ========== Improvement Cards ==========
import streamlit as st

def improvement_card(title, description):
    st.markdown(
        f"""
        <div style='background:#3d9df333; padding:20px; border-radius:12px;
                    box-shadow:0 0 5px rgba(0,0,0,0.08); margin-bottom:15px;'>
            <h4>{title}</h4>
            <p style='color:#555;'>{description}</p>
        </div>
        """,
      "  unsafe_allow_html=True
    )

improvement_card(
        "1. Smarter Google Predictions"
        "We will improve how Google Places data is normalized for the model. This will reduce mismatches in cuisine, ZIP, and borough fields. The goal is more accurate predictions for restaurants not found in the NYC dataset."

        "2. Real-Time Inspection Updates"
        "The app will connect to NYC’s live DOHMH API. New violations and re-inspections will update instantly in the map and predictions. This keeps grade predictions fresh and reliable."

        "3. Better Explainability & Risk Forecasting"
        "We plan to add SHAP/LIME so users can see why a grade was predicted. A risk model will estimate the chance of critical violations or failed inspections. This helps users understand hidden patterns and future risks."
    
)



st.markdown("---")




# -------------------------------------------------
# 5. 🎯 Fun Stats at a Glance
# -------------------------------------------------
st.markdown("## 🎯 Fun Stats at a Glance")
st.markdown(
    "Quick facts computed directly from the current dataset. "
    "These numbers update automatically if the dataset changes."
)

col1, col2, col3 = st.columns(3)

# ---- Most inspected cuisine ----
with col1:
    if "cuisine_description" in df.columns:
        cuisine_counts = df["cuisine_description"].value_counts()
        most_inspected_cuisine = cuisine_counts.idxmax()
        count_cuisine = int(cuisine_counts.max())
        st.metric(
            "🍕 Most inspected cuisine",
            most_inspected_cuisine,
            help=f"Appears {count_cuisine:,} times in the dataset."
        )
    else:
        st.info("No cuisine_description column in data.")

# ---- Most common violation ----
with col2:
    if "violation_code" in df.columns:
        viol_counts = df["violation_code"].value_counts()
        top_code = viol_counts.idxmax()
        top_count = int(viol_counts.max())
        short_desc = VIOLATION_SHORT.get(top_code, UNKNOWN_VIOLATION_LABEL)
        st.metric(
            "🚨 Most common violation",
            top_code,
            help=f"{short_desc} (seen {top_count:,} times)"
        )
    else:
        st.info("No violation_code column in data.")

# ---- Borough with highest avg score ----
with col3:
    if "boro" in df.columns and "score" in df.columns:
        boro_scores = (
            df.groupby("boro")["score"]
            .mean()
            .sort_values(ascending=False)
        )
        top_boro = boro_scores.index[0]
        top_boro_score = boro_scores.iloc[0]
        st.metric(
            "🏢 Borough with highest avg score",
            top_boro,
            help=f"Average score ≈ {top_boro_score:.1f} (higher score = more violations)"
        )
    else:
        st.info("No boro / score columns in data.")

# Second row of fun stats
col4, col5 = st.columns(2)

# ---- Best / worst cuisines by score ----
with col4:
    st.markdown("### 🥇 Best & 😬 Worst Cuisines (by avg score)")

    if "cuisine_description" in df.columns and "score" in df.columns:
        cuisine_stats = (
            df.groupby("cuisine_description")["score"]
            .agg(["mean", "count"])
        )

        # Only consider cuisines with enough samples
        cuisine_stats = cuisine_stats[cuisine_stats["count"] >= 30]

        if len(cuisine_stats) > 0:
            best_row = cuisine_stats.sort_values("mean").iloc[0]
            worst_row = cuisine_stats.sort_values("mean").iloc[-1]
            best_name = cuisine_stats.sort_values("mean").index[0]
            worst_name = cuisine_stats.sort_values("mean").index[-1]

            st.write(
                f"**Best cuisine (lowest avg score):** {best_name} "
                f"(avg score ≈ {best_row['mean']:.1f})"
            )
            st.write(
                f"**Worst cuisine (highest avg score):** {worst_name} "
                f"(avg score ≈ {worst_row['mean']:.1f})"
            )
            st.caption("Lower inspection scores generally indicate fewer violations.")
        else:
            st.info("Not enough data per cuisine to compute robust stats.")
    else:
        st.info("No cuisine / score columns in data.")

# ---- % missing demographic data ----
with col5:
    st.markdown("### ☑️ Data completeness")

    # Prefer the explicit demo_missing flag if present
    pct_demo_missing = None

    if "demo_missing" in df.columns:
        # demo_missing should be 0/1
        pct_demo_missing = df["demo_missing"].mean() * 100.0
    else:
        # Fallback: treat rows as "missing" if key demo columns are NaN
        demo_cols = [
            "nyc_poverty_rate",
            "median_income",
            "perc_white",
            "perc_black",
            "perc_asian",
            "perc_hispanic",
        ]
        demo_cols = [c for c in demo_cols if c in df.columns]
        if demo_cols:
            missing_mask = df[demo_cols].isna().any(axis=1)
            pct_demo_missing = missing_mask.mean() * 100.0

    if pct_demo_missing is not None:
        st.metric(
            "☑️ % of restaurants missing demographic data",
            f"{pct_demo_missing:.1f}%",
            help="These rows still contribute to training via a demo_missing flag."
        )
    else:
        st.info("Demographic missingness not available in this dataset.")

st.markdown("---")





# -------------------------------------------------
# 6. 🧪 Interactive Mini-Experiments
# -------------------------------------------------
st.markdown("## 🧪 Try Small Experiments")
st.markdown(
    "Play with the data: select a cuisine, borough, or ZIP code and see how "
    "scores, violations, and demographics change."
)

# -------------------------
# Experiment 1 — Cuisine ⮕ Avg score & grade chart
# -------------------------
with st.expander("🍽️ Pick a cuisine → see its average score & grade mix"):
    if "cuisine_description" in df.columns and "score" in df.columns:
        cuisines_sorted = sorted(df["cuisine_description"].dropna().unique())
        selected_cuisine = st.selectbox(
            "Choose a cuisine:",
            ["(Select a cuisine)"] + cuisines_sorted,
        )

        if selected_cuisine != "(Select a cuisine)":
            sub_df = df[df["cuisine_description"] == selected_cuisine]

            st.write(
                f"**Restaurants with cuisine `{selected_cuisine}`:** {len(sub_df):,}"
            )

            avg_score = sub_df["score"].mean()
            st.write(f"**Average inspection score:** {avg_score:.1f}")

            if "grade" in sub_df.columns:
                grade_counts = (
                    sub_df["grade"]
                    .value_counts()
                    .reset_index()
                )
                grade_counts.columns = ["grade", "count"]

                chart = (
                    alt.Chart(grade_counts)
                    .mark_bar()
                    .encode(
                        x=alt.X("grade:N", title="Grade"),
                        y=alt.Y("count:Q", title="Count"),
                        color=alt.Color("grade:N", legend=None),
                        tooltip=["grade:N", "count:Q"],
                    )
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No grade column available for this dataset.")
    else:
        st.info("Cuisine/score data not found in dataset.")


# -------------------------
# Experiment 2 — Borough ⮕ Top 5 violations
# -------------------------
with st.expander("🏙️ Pick a borough → see top 5 violations"):
    if "boro" in df.columns and "violation_code" in df.columns:
        boro_options = sorted(df["boro"].dropna().unique())
        selected_boro = st.selectbox(
            "Choose a borough:",
            ["(Select a borough)"] + boro_options,
        )

        if selected_boro != "(Select a borough)":
            sub_df = df[df["boro"] == selected_boro]

            st.write(f"**Restaurants in {selected_boro}:** {len(sub_df):,}")

            vio_counts = (
                sub_df["violation_code"]
                .value_counts()
                .reset_index()
                .head(5)
            )
            vio_counts.columns = ["violation_code", "count"]
            vio_counts["description"] = vio_counts["violation_code"].apply(
                lambda c: VIOLATION_SHORT.get(c, UNKNOWN_VIOLATION_LABEL)
            )

            chart_vio = (
                alt.Chart(vio_counts)
                .mark_bar()
                .encode(
                    x=alt.X("violation_code:N", title="Violation Code"),
                    y=alt.Y("count:Q", title="Count"),
                    tooltip=["violation_code:N", "description:N", "count:Q"],
                    color=alt.Color("violation_code:N", legend=None),
                )
            )
            st.altair_chart(chart_vio, use_container_width=True)

            st.write("**Descriptions:**")
            for _, row in vio_counts.iterrows():
                st.write(f"- `{row['violation_code']}` — {row['description']}")
    else:
        st.info("Borough/violation data not found in dataset.")


# -------------------------
# Experiment 3 — ZIP ⮕ Demographic profile
# -------------------------
with st.expander("📮 Pick a ZIP → see demographic profile"):
    if "zipcode" in df.columns:
        # cast to string so selection is clean
        df["zipcode"] = df["zipcode"].astype(str)
        zip_options = sorted(df["zipcode"].dropna().unique())
        selected_zip = st.selectbox(
            "Choose a ZIP code:",
            ["(Select a ZIP)"] + zip_options,
        )

        if selected_zip != "(Select a ZIP)":
            zip_df = df[df["zipcode"] == selected_zip]

            st.write(f"**Rows for ZIP {selected_zip}:** {len(zip_df):,}")

            # Show mean of key demo columns if available
            demo_cols = [
                "nyc_poverty_rate",
                "median_income",
                "perc_white",
                "perc_black",
                "perc_asian",
                "perc_hispanic",
                "population",
            ]
            demo_cols = [c for c in demo_cols if c in zip_df.columns]

            if demo_cols:
                summary = zip_df[demo_cols].mean().to_frame("value")
                summary.index.name = "metric"
                st.dataframe(summary.style.format({"value": "{:.3f}"}))
            else:
                st.info("No demographic columns available for this ZIP.")
    else:
        st.info("ZIP code information not available in dataset.")


# -------------------------
# Experiment 4 — Google Places restaurant (if available)
# -------------------------
with st.expander("📍 See latest Google Places restaurant (if selected in main page)"):
    # This depends on the main prediction page saving a normalized restaurant
    # (e.g. under this key). If not present, we show a message.
    google_rest = st.session_state.get("google_restaurant_nearby")

    if google_rest is None:
        st.info(
            "No Google Places restaurant found in this session.\n\n"
            "Try this:\n"
            "1. Go to the **main prediction page**.\n"
            "2. Turn on **Google mode**.\n"
            "3. Click a nearby restaurant on the map.\n"
            "4. Come back here to see an auto-generated restaurant card."
        )
    else:
        st.markdown("### Last Google Places Restaurant Selected")
        st.write(f"**Name:** {google_rest.get('name', 'Unknown')}")
        st.write(f"**Address:** {google_rest.get('address', 'Unknown')}")
        st.write(f"**ZIP:** {google_rest.get('zipcode', 'Unknown')}")
        st.write(f"**Borough:** {google_rest.get('boro', 'Unknown')}")
        st.write(f"**Cuisine:** {google_rest.get('cuisine_description', 'Unknown')}")

        score = google_rest.get("score", None)
        if score is not None:
            st.write(f"**Synthetic score used for prediction:** {score}")

        st.caption(
            "This card shows how the app normalizes Google Places data "
            "into the same structure as NYC inspection records."
        )

st.markdown("---")


# -------------------------------------------------
# 7. 🧠 How the Model Thinks (Illustration)
# -------------------------------------------------
st.markdown("## 🧠 How the Model Thinks (Illustration)")

st.write(
    "This chart is a simplified view of how different feature groups might "
    "influence a prediction for a restaurant with an inspection score around **15**."
)

feature_importance_example = pd.DataFrame(
    {
        "feature_group": [
            "Inspection Score",
            "Violation History",
            "Neighborhood Income / Poverty",
            "Cuisine Type",
            "Population / Density",
        ],
        "influence_percent": [45, 22, 18, 10, 5],
    }
)

chart_importance = (
    alt.Chart(feature_importance_example)
    .mark_bar()
    .encode(
        x=alt.X("influence_percent:Q", title="Estimated Influence (%)"),
        y=alt.Y("feature_group:N", sort="-x", title="Feature Group"),
        tooltip=["feature_group:N", "influence_percent:Q"],
        color=alt.Color("feature_group:N", legend=None),
    )
)

st.altair_chart(chart_importance, use_container_width=True)

st.caption(
    "Note: This is an illustrative example, not exact SHAP values. "
    "In practice, the Random Forest uses many trees and splits to "
    "combine these signals into a final A/B/C prediction."
)

st.markdown("---")
