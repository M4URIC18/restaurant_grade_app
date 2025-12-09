import streamlit as st
import pandas as pd

st.set_page_config(page_title="About", layout="centered")

st.title("🍽️ CleanKitchen NYC")
st.caption("A clean and simple tool for exploring New York City restaurant health data.")

st.markdown("---")

# ------------------------------
# WHAT THIS APP DOES
# ------------------------------
st.header("What This App Does")

st.markdown("""
CleanKitchen NYC helps users explore NYC restaurant inspection data and 
predict health grades using a machine-learning model.  
The app combines:

- 🏙️ **NYC Restaurant Inspection Data**  
- 🧮 **Demographic & socioeconomic features**  
- 🧠 **ML-based grade prediction**  
- 🗺️ **Interactive maps & filters**

Everything is shown in a simple and clean layout.
""")

st.markdown("---")

# ------------------------------
# HOW IT WORKS
# ------------------------------
st.header("How It Works")

with st.expander("Data Collection"):
    st.write("""
    We gather public data from NYC Open Data (restaurant inspections) and merge it
    with ZIP-code demographic data. This provides a rich feature set for predictions.
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

st.write("""
- **NYC DOHMH Restaurant Inspection Results**  
  Public dataset containing restaurant inspection scores and grades.

- **NYC Demographic & Socioeconomic Data**  
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

# ------------------------------
# TECH STACK
# ------------------------------
st.header("Tech Stack")

col1, col2 = st.columns(2)

with col1:
    st.write("""
    - **Python**
    - **Pandas**
    - **Scikit-Learn**
    - **Streamlit**
    - **Altair Charts**
    """)

with col2:
    st.write("""
    - **Folium Maps**
    - **Google Places API**
    - **Random Forest Model**
    - **JSON / CSV Pipelines**
    """)

st.markdown("---")

# ------------------------------
# CREATOR
# ------------------------------
st.header("Creator")

st.write("""
This project was built by Mep Eus Prez as a final ML + Data Engineering project.

If you'd like to connect or see more projects:
""")

colA, colB = st.columns(2)
colA.link_button("GitHub", "https://github.com/")
colB.link_button("LinkedIn", "https://linkedin.com/")

st.markdown("---")

st.markdown("### Thanks for visiting CleanKitchen NYC!")
