# pages/1_About.py
import streamlit as st

st.set_page_config(page_title="About CleanKitchen NYC", layout="wide")

# ----------------------------------------------
# CUSTOM STYLE (minimal but modern)
# ----------------------------------------------
ACCENT = "#3A86FF"  # choose your brand color (blue)
st.markdown(
    f"""
    <style>
        h1, h2, h3 {{
            font-family: 'Inter', sans-serif;
            letter-spacing: -0.5px;
        }}

        .section-title {{
            padding-left: 8px;
            border-left: 4px solid {ACCENT};
        }}

        .card:hover {{
            transform: translateY(-3px);
            transition: 0.15s ease-in-out;
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }}
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown(
    """
    <style>
        body {
            background-color: #F6F7FB !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)



# ----------------------------------------------
# HERO SECTION
# ----------------------------------------------
st.markdown(
    """
    <div style='text-align:center; padding: 30px 10px;'>
        <h1 style='font-size:42px; margin-bottom:10px;'>🍽️ CleanKitchen NYC</h1>
        <p style='font-size:20px; color: #666;'>
            A modern tool that predicts NYC restaurant health grades using real inspection data,<br>
            demographics, machine learning, and interactive map exploration.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# ----------------------------------------------
# PROJECT HIGHLIGHTS
# ----------------------------------------------
st.markdown("<h2 class='section-title'> What This App Does</h2>", unsafe_allow_html=True)
st.write(
    """
    CleanKitchen NYC helps users explore NYC restaurants through:
    """
)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class='card' style='background:#FAFAFA; padding:20px; border-radius:12px; border-top:4px solid {ACCENT}; box-shadow:0 0 8px rgba(0,0,0,0.08);'>
            <h3>🗺️ Interactive Map</h3>
            <p>Search and explore all NYC restaurants using Google Places or official DOH records.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <div class='card' style='background:#FAFAFA; padding:20px; border-radius:12px; border-top:4px solid {ACCENT}; box-shadow:0 0 8px rgba(0,0,0,0.08);'>
            <h3>🧠 ML Grade Predictions</h3>
            <p>Our trained model uses 17+ features to predict whether a restaurant is likely A, B, or C.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        """
        <div class='card' style='background:#FAFAFA; padding:20px; border-radius:12px; border-top:4px solid {ACCENT}; box-shadow:0 0 8px rgba(0,0,0,0.08);'>
            <h3>📊 Filter & Insights</h3>
            <p>Analyze patterns across boroughs, cuisines, scores, and violations.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")

# ----------------------------------------------
# HOW IT WORKS
# ----------------------------------------------
st.markdown("<h2 class='section-title'>🔧 How the System Works</h2>", unsafe_allow_html=True)
with st.expander("📊 See a sample distribution chart"):
    import pandas as pd
    import altair as alt

    try:
        df = pd.read_csv("data/df_merged_big.csv")
        chart = (
            alt.Chart(df.head(200))
            .mark_bar()
            .encode(
                x="score:Q",
                y="count()"
            )
        )
        st.altair_chart(chart, use_container_width=True)
    except Exception:
        st.info("Dataset not available or could not be loaded.")




st.markdown(
    """
    <div style='background:#FFFFFF; padding:25px; border-radius:12px; box-shadow:0 0 8px rgba(0,0,0,0.05);'>
        <h3>📦 Data Sources</h3>
        <ul>
            <li>NYC DOH inspection history (292,000+ records)</li>
            <li>NYC neighborhood demographic dataset (income, poverty rate, ethnicity mix)</li>
            <li>Google Places API for live restaurant search</li>
        </ul>

        <h3>🧠 Machine Learning Model</h3>
        <p>
            Trained using a Random Forest classifier, incorporating:
        </p>
        <ul>
            <li>Inspection score</li>
            <li>Demographic indicators</li>
            <li>Borough, ZIP code, and cuisine</li>
            <li>Violation history</li>
        </ul>
        <p>
            The result: fast, on-the-fly grade predictions.
        </p>

        <h3>🖥️ Technology Stack</h3>
        <p>
            Python · Streamlit · Scikit-Learn · Pandas · Folium · Google Places API
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# ----------------------------------------------
# ROADMAP
# ----------------------------------------------
st.subheader("🚀 Roadmap")

st.markdown(
    """
    Coming in the next updates:
    - 📱 Mobile-first redesign  
    - 🌙 Dark mode  
    - 🧬 More features in prediction panel (risk explanation, confidence bars)  
    - 📍 Neighborhood-level profile pages  
    - 🍲 Cuisine health profile pages  
    - 🕒 DOH real-time inspection updates  
    """
)

st.markdown("---")

# ----------------------------------------------
# CREDITS / CONTACT
# ----------------------------------------------
st.subheader("👤 Created By")

st.markdown(
    """
    **Jack, Mauricio, Dominik** — Developer, Data Scientist fellow.  
    Feel free to reach out for collaboration or improvements!
    """
)

