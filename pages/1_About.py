# pages/1_About.py
import streamlit as st
import pandas as pd

st.markdown(
    """
    <style>
    /* Force readable text in dark mode */
    .ck-card, .ck-card h3, .ck-card p, .subtext {
        color: #222222 !important;
    }

    /* Light background for cards */
    .ck-card {
        background-color: #FFFFFF !important;
    }

    /* Ensure hover stays readable */
    .ck-card:hover {
        background-color: #FFFFFF !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)



st.set_page_config(page_title="About CleanKitchen NYC", layout="wide")

# -------------------------------------------------
# GLOBAL THEME COLORS
# -------------------------------------------------
ACCENT = "#4F8BF9"     # Clean modern blue
CARD_BG = "#FFFFFF"
TEXT_LIGHT = "#666666"

# -------------------------------------------------
# GLOBAL CSS (applies to whole page)
# -------------------------------------------------
st.markdown(
    f"""
    <style>

    /* Page background */
    .main {{
        background-color: #F9FAFB !important;
    }}

    /* Card style */
    .ck-card {{
        background: {CARD_BG};
        padding: 24px;
        border-radius: 14px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        border-left: 4px solid {ACCENT};
        transition: 0.2s ease;
    }}

    .ck-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 4px 14px rgba(0,0,0,0.10);
    }}

    /* Section titles */
    .section-title {{
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 10px;
        color: #222;
    }}

    .subtext {{
        color: {TEXT_LIGHT};
        font-size: 18px;
        line-height: 1.5;
    }}

    /* Timeline style */
    .timeline {{
        border-left: 3px solid {ACCENT};
        margin-left: 10px;
        padding-left: 25px;
    }}

    .timeline-item {{
        margin-bottom: 30px;
        position: relative;
    }}

    .timeline-item::before {{
        content: "";
        width: 14px;
        height: 14px;
        background: {ACCENT};
        border-radius: 50%;
        position: absolute;
        left: -31px;
        top: 3px;
        box-shadow: 0 0 0 3px #E3ECFF;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------
# HERO SECTION
# -------------------------------------------------
st.markdown(
    f"""
    <div style='text-align:center; padding: 40px 10px;'>
        <h1 style='font-size:46px; margin-bottom:5px;'>🍽️ CleanKitchen NYC</h1>
        <p style='font-size:20px; color:{TEXT_LIGHT}; max-width:750px; margin:auto;'>
            A modern, data-driven tool that predicts NYC restaurant health grades using 
            machine learning, open data, neighborhood demographics, and interactive maps.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# -------------------------------------------------
# PROJECT HIGHLIGHTS — MODERN CARDS
# -------------------------------------------------
st.markdown("<h2 class='section-title'>✨ What This App Does</h2>", unsafe_allow_html=True)

st.markdown("""
CleanKitchen NYC helps users explore NYC restaurant inspection data and 
predict health grades using a machine-learning model.  
The app combines:
""")


col1, col2, col3 = st.columns(3)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class='ck-card' style='padding:20px; border-radius:12px;
             box-shadow:0 0 8px rgba(0,0,0,0.08); border-left:4px solid #4F8BF9;'>
            <h3 style='color:#222;'>🗺️ Interactive Map</h3>
            <p class='subtext' style='color:#444;'>
                Explore all NYC restaurants using Google Places or DOH records.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <div class='ck-card' style='padding:20px; border-radius:12px;
             box-shadow:0 0 8px rgba(0,0,0,0.08); border-left:4px solid #4F8BF9;'>
            <h3 style='color:#222;'>🧠 ML Grade Predictions</h3>
            <p class='subtext' style='color:#444;'>
                Our model uses 17+ features to predict A, B, or C grades.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        """
        <div class='ck-card' style='padding:20px; border-radius:12px;
             box-shadow:0 0 8px rgba(0,0,0,0.08); border-left:4px solid #4F8BF9;'>
            <h3 style='color:#222;'>📊 Filter & Insights</h3>
            <p class='subtext' style='color:#444;'>
                Analyze patterns across boroughs, cuisines, and violations.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )



st.markdown("---")
# -------------------------------------------------
# HOW IT WORKS — TIMELINE STYLE
# -------------------------------------------------
st.markdown("<h2 class='section-title'>🔧 How the System Works</h2>", unsafe_allow_html=True)

st.markdown("<div class='timeline'>", unsafe_allow_html=True)

with st.expander("Data Collection"):
    st.write("""
    We gather public data from NYC Open Data (restaurant inspections) and merge it
    with ZIP-code demographic data. This provides a rich feature set for predictions:
    
    - NYC DOH inspection history (292,000+ records)
    - ZIP-code demographic stats (income, poverty rate, ethnicity mix)
    - Google Places API for real-time restaurant lookup
    """)

with st.expander("Model Training"):
    st.write("""
    A Random Forest classifier is trained to predict A/B/C grades using:
    
    - restaurant score  
    - violation history  
    - ZIP-level demographics  
    - cuisine type  
    """)

with st.expander("Prediction Process"):
    st.write("""
    When you click a restaurant on the map, the app prepares its features,
    sends them to the model, and shows the predicted grade with confidence.
    """)

st.markdown("---")


# ------------------------------
# DATA SOURCES
# ------------------------------

st.header("Data Sources")

st.markdown("""
- **[NYC DOHMH Restaurant Inspection Results](https://data.cityofnewyork.us/Health/Restaurant-Inspection-Results/43nn-pn8j)**  
  Public dataset containing restaurant inspection scores and grades.

- **[NYC ZIP Code Demographic Profile](https://data.cityofnewyork.us/Business/Neighborhood-Financial-Health-Digital-Mapping-and-/r3dx-pew9/about_data)**  
  ZIP-code level statistics merged to enrich prediction quality.
""")

# Small interactivity: sample data preview
if st.button("Show Sample Restaurant Data"):
    try:
        df = pd.read_csv("data/df_merged_big.csv")
        st.dataframe(df.head())
    except:
        st.info("Sample data unavailable in this environment.")

st.markdown("---")


# -------------------------------------------------
# ROADMAP — Clean Layout
# -------------------------------------------------
st.markdown("<h2 class='section-title'>🚀 Roadmap</h2>", unsafe_allow_html=True)

st.markdown(
    f"""
    <div class='ck-card' style='border-left: 4px solid {ACCENT};'>
        <ul class='subtext'>
            <li>📱 Mobile-first redesign</li>
            <li>🌙 Dark mode</li>
            <li>🧬 More insights in prediction panel</li>
            <li>📍 Neighborhood & cuisine profile pages</li>
            <li>🕒 Real-time DOH inspection updates</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# -------------------------------------------------
# CREATOR SECTION
# -------------------------------------------------
st.markdown("<h2 class='section-title'>👤 Created By</h2>", unsafe_allow_html=True)

colA, colB = st.columns([1,2])

with colA:
    st.image("https://avatars.githubusercontent.com/u/9919?s=280&v=4", width=120)

with colB:
    st.markdown(
        f"""
        <p class='subtext'>
            Built by **Jack, Mauricio, and Dominik** — Data Science & CS Fellows.<br>
            Interested in collaboration or improvements?
        </p>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    col1.link_button("GitHub", "https://github.com/")
    col2.link_button("LinkedIn", "https://linkedin.com/")

st.markdown("---")

st.markdown("<p style='text-align:center; color:#999;'>Thanks for visiting CleanKitchen NYC!</p>", unsafe_allow_html=True)
