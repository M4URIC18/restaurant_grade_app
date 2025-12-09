# pages/1_About.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="About · CleanKitchen NYC", layout="centered")

# --------------------------------
# THEME ACCENTS
# --------------------------------
ACCENT = "#4C9AFF"       # soft blue
SECTION_BG = "rgba(0,0,0,0.03)"
CARD_BG = "rgba(255,255,255,0.85)"

# Add subtle global style
st.markdown(
    f"""
    <style>
        .section-box {{
            background: {SECTION_BG};
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 25px;
            border-left: 5px solid {ACCENT};
        }}
        .card-box {{
            background: {CARD_BG};
            padding: 16px;
            border-radius: 10px;
            margin-bottom: 12px;
            border: 1px solid rgba(0,0,0,0.05);
        }}
        .small-caption {{
            color: grey;
            font-size: 0.9rem;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------
# TOP HEADER
# --------------------------------
st.title("🍽️ CleanKitchen NYC")
st.caption("A clean and simple tool for exploring New York City restaurant health data.")

st.markdown("---")

# --------------------------------
# WHAT THIS APP DOES
# --------------------------------
st.markdown(f"<div class='section-box'>", unsafe_allow_html=True)
st.header("What This App Does")
st.write(
    """
CleanKitchen NYC helps users explore NYC restaurant inspection data and 
predict health grades using a machine-learning model.  
The app combines:

- 🏙️ **NYC Restaurant Inspection Data**
- 🧮 **Demographic & socioeconomic features**
- 🧠 **ML-based grade prediction**
- 🗺️ **Interactive maps & filters**

Everything is shown in a simple, clean layout.
"""
)
st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------
# HOW IT WORKS
# --------------------------------
st.markdown(f"<div class='section-box'>", unsafe_allow_html=True)
st.header("How It Works")

with st.expander("🔎 Data Collection"):
    st.write("""
We gather public data from NYC Open Data (restaurant inspections) and merge it
with ZIP-code demographic data. This provides a rich feature set for predictions.
""")

with st.expander("🧠 Model Training"):
    st.write("""
A Random Forest classifier is trained to predict A/B/C grades using:

- restaurant score  
- violation history  
- ZIP-level demographics  
- cuisine type  
""")

with st.expander("⚙️ Prediction Process"):
    st.write("""
When you click a restaurant on the map, the app prepares its features,
sends them to the model, and shows the predicted grade with confidence.
""")
st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------
# DATA SOURCES
# --------------------------------
st.markdown(f"<div class='section-box'>", unsafe_allow_html=True)
st.header("Data Sources")

st.write("""
- **NYC DOHMH Restaurant Inspection Results**  
  Public dataset containing restaurant inspection scores and grades.

- **NYC Demographic & Socioeconomic Data**  
  ZIP-code level statistics merged to enrich prediction quality.
""")

# interactive button
if st.button("📄 Show Sample Restaurant Data"):
    try:
        df = pd.read_csv("data/df_merged_big.csv")
        st.dataframe(df.head())
    except:
        st.info("Sample data unavailable in this environment.")
st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------
# TECH STACK
# --------------------------------
st.markdown(f"<div class='section-box'>", unsafe_allow_html=True)
st.header("Tech Stack")

col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.write("""
**Backend & Data Tools**
- Python
- Pandas
- Scikit-Learn
- JSON/CSV Pipelines
    """)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.write("""
**Frontend & Visualization**
- Streamlit
- Altair Charts
- Folium Maps
- Google Places API
    """)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------
# CREATOR
# --------------------------------
st.markdown(f"<div class='section-box'>", unsafe_allow_html=True)
st.header("Creator")

st.write("""
This project was built by **Mep Eus Prez** as a final Machine Learning  
and Data Engineering project.

If you'd like to connect or see more projects:
""")

colA, colB = st.columns(2)
colA.link_button("🔗 GitHub", "https://github.com/")
colB.link_button("💼 LinkedIn", "https://linkedin.com/")

st.markdown("<p class='small-caption'>Thanks for visiting CleanKitchen NYC!</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
