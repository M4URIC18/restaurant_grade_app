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

ACCENT = "#4C9AFF"  # or whatever accent color you want

with col1:
    st.markdown(
        f"""
        <div class='card' 
             style='background:#FAFAFA; 
                    padding:20px; 
                    border-radius:12px; 
                    border-top:4px solid {ACCENT}; 
                    box-shadow:0 0 8px rgba(0,0,0,0.08);
                    color:#333;'>
            <h3 style='color:#222;'>🗺️ Interactive Map</h3>
            <p>Search and explore all NYC restaurants using Google Places or official DOH records.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"""
        <div class='card' 
             style='background:#FAFAFA; 
                    padding:20px; 
                    border-radius:12px; 
                    border-top:4px solid {ACCENT}; 
                    box-shadow:0 0 8px rgba(0,0,0,0.08);
                    color:#333;'>
            <h3 style='color:#222;'>🧠 ML Grade Predictions</h3>
            <p>Our trained model uses 17+ features to predict A, B, or C grades.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f"""
        <div class='card' 
             style='background:#FAFAFA; 
                    padding:20px; 
                    border-radius:12px; 
                    border-top:4px solid {ACCENT}; 
                    box-shadow:0 0 8px rgba(0,0,0,0.08);
                    color:#333;'>
            <h3 style='color:#222;'>📊 Filter & Insights</h3>
            <p>Analyze patterns across boroughs, cuisines, scores, and violations.</p>
        </div>
        """,
        unsafe_allow_html=True
    )


st.markdown("---")

# ----------------------------------------------
# HOW IT WORKS
# ----------------------------------------------
st.markdown("<h2 class='section-title'> How the System Works</h2>", unsafe_allow_html=True)
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
            <li><b>NYC DOH Inspection History</b> — 292k+ inspection records.</li>
            <li><b>NYC Demographics</b> — ZIP-level income, poverty rate, ethnicity mix, population.</li>
            <li><b>Google Places API</b> — Live restaurant search for current listings.</li>
        </ul>

        <p style='color:#666; font-size:15px; margin-top:-10px;'>
            These datasets are merged to build a detailed profile for each restaurant.
        </p>

        <h3>🧠 Machine Learning Model</h3>
        <p>
            A <b>Random Forest classifier</b> is trained using 17+ engineered features, including:
        </p>
        <ul>
            <li>Inspection score & critical flag</li>
            <li>Borough and ZIP code</li>
            <li>Cuisine category</li>
            <li>Demographic indicators (income, poverty, ethnicity)</li>
            <li>Violation patterns</li>
        </ul>

        <p style='margin-top:10px;'>
            The model outputs a predicted health grade (<b>A</b>, <b>B</b>, or <b>C</b>) 
            along with confidence percentages.
        </p>

        <h4>📈 Model Performance</h4>
        <ul>
            <li>Accuracy: <b>~84%</b></li>
            <li>5-fold cross-validation</li>
            <li>Feature importance weighted toward score, ZIP stats, and cuisine</li>
        </ul>

        <h3>🖥️ Technology Stack</h3>
        <p>
            <b>Python</b> · Streamlit · Scikit-Learn · Pandas · Folium · Altair · Google Places API
        </p>

        <h3>⚠️ Limitations</h3>
        <ul>
            <li>Predictions rely on past inspection patterns.</li>
            <li>Some ZIP codes and cuisines have limited data.</li>
            <li>Google Places data may not fully align with DOH records.</li>
        </ul>
        
        <h3>🔄 Prediction Pipeline</h3>
        <ol>
            <li>User selects a restaurant or clicks the map</li>
            <li>The app builds a feature vector for that location</li>
            <li>The ML model evaluates risk patterns</li>
            <li>Grade + confidence is displayed instantly</li>
        </ol>

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

