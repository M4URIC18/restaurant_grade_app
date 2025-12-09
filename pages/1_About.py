# pages/1_About.py
import streamlit as st

st.set_page_config(page_title="About – CleanKitchen NYC", layout="wide")

# ----------------------------------
# Header
# ----------------------------------
st.title("🍽️ CleanKitchen NYC")
st.subheader("Restaurant Grade Prediction & NYC Food Safety Insights")

st.write("""
CleanKitchen NYC is an interactive web app that helps users explore and predict NYC restaurant 
health inspection grades using real data from the NYC Open Data program and Google Places API.

This project combines:
- 🔍 **Data analytics**
- 🗺️ **Interactive maps**
- 🤖 **Machine learning**
- 📊 **NYC census & demographic data**
""")

st.divider()

# ----------------------------------
# Project Purpose
# ----------------------------------
st.header("🎯 Project Purpose")

st.write("""
NYC performs thousands of restaurant inspections every year.  
While this data is public, it can be hard for everyday users to explore.

**CleanKitchen NYC** makes this easier by:

- Mapping restaurants across the city  
- Letting you filter by borough, cuisine, score, and grade  
- Showing insights about violation patterns  
- Predicting a restaurant’s expected **A/B/C grade** using ML  
- Allowing real-time predictions for **Google restaurants not in the dataset**  
""")

st.divider()

# ----------------------------------
# How It Works
# ----------------------------------
st.header("⚙️ How the System Works")

st.write("""
### 1️⃣ **Data Sources**
The app uses multiple datasets:
- 🏛 **NYC Restaurant Inspection Results** (292k+ records)  
- 📍 **Google Places API** for restaurants not in the dataset  
- 🧮 **ZIP-Code Demographics** (income, poverty rate, racial distribution, etc.)

All datasets are cleaned and merged into a single modeling dataset.

### 2️⃣ **Machine Learning Model**
A trained **Random Forest Classifier** predicts a restaurant’s grade (“A”, “B”, or “C”) using:
- Inspection score  
- ZIP demographic features  
- Cuisine type  
- Violation type  
- Borough / ZIP  
- Critical flag indicators  

### 3️⃣ **Prediction Pipeline**
When a user selects a restaurant:
1. The app extracts available restaurant features  
2. Missing ZIP demographic fields are filled using lookup tables  
3. A clean feature vector is generated  
4. The Random Forest model returns:  
   - Predicted grade  
   - Confidence % for A, B, C  

""")

st.divider()

# ----------------------------------
# How to Use the App
# ----------------------------------
st.header("🧭 How to Use This App")

st.write("""
### 🔹 **Main Page – Prediction Map**
- Explore NYC on the interactive map  
- Click a restaurant to see its predicted grade  
- Toggle **Google Mode** to select restaurants not in the dataset  
- See score, violation history, cuisine type, and demographics  

### 🔹 **Filter & Analytics Page**
- Apply borough, ZIP, score, and cuisine filters  
- See the Grade Distribution, Scores Histogram, and Cuisine Rankings  
- Explore patterns in NYC restaurant quality  

### 🔹 **Blog Page (optional)**
- Updates, notes, and development logs  
""")

st.divider()

# ----------------------------------
# Technologies Used
# ----------------------------------
st.header("🛠️ Technologies Used")

st.write("""
- **Python**  
- **Streamlit**  
- **Altair** / **Folium** for visualization  
- **Pandas / NumPy** for data wrangling  
- **Scikit-Learn** (Random Forest)  
- **Google Places API**  
- **NYC Open Data API**  
""")

st.divider()

# ----------------------------------
# Project Motivation / Credits
# ----------------------------------
st.header("💡 Project Motivation")

st.write("""
This project was built to bring transparency to NYC food safety and provide an easy way 
for users to understand how scores and demographics relate to restaurant grades.

It also demonstrates real-world machine learning applied to a public data problem.
""")

st.write("Developed by **Mep Eus Prez** — 2025")

