import streamlit as st

st.set_page_config(page_title="CleanKitchen Blog", layout="wide")

st.title("📝 CleanKitchen NYC — Project Blog")
st.caption("Explore how the app was built, the datasets used, and the ML choices made.")

st.markdown("---")

# ----------------------------------------------------------
# BLOG POSTS CONTENT
# ----------------------------------------------------------

POSTS = {
    "Post 1 — Dataset Overview & Why Multiple Sources Were Needed": """
### 📌 Post 1 — Dataset Overview & Why Multiple Sources Were Needed

CleanKitchen NYC uses **three major datasets**, each contributing a different layer of information:

---

## **1. NYC Restaurant Inspection Dataset (Primary)**
- 292,000+ inspection records  
- Includes score, grade, violation codes, violation descriptions  
- Contains location: borough, street, ZIP code, latitude, longitude  
- This is the foundation of the prediction model  

Why it's important:  
The inspection score is the **strongest predictor** of the final grade.

---

## **2. Neighborhood Financial Health (NFH) Dataset**
This dataset adds:
- Poverty rate  
- Median income  
- Ethnic composition  
- Neighborhood-level socioeconomics  

**Problem:**  
It *does not contain ZIP codes*, only neighborhood names → which forced a mapping step.

---

## **3. ZIP Code Population Dataset**
We added this to enrich:
- Population density  
- Number of residents per ZIP  
- How crowded/commercial a ZIP code is  

Population helps find patterns:
- Manhattan ZIPs have dense commercial areas → more inspections, more violations  
- Staten Island ZIPs have lower density → often cleaner profiles  

---

## Summary

By combining:
- Inspection scores  
- Demographics  
- Population density  

…the model becomes **much more stable**, especially in cases where inspection counts are low.  
""",

    "Post 2 — Data Cleaning Pipeline (Step-by-Step)": """
### 📌 Post 2 — Data Cleaning Pipeline (Step-by-Step)

To prepare the model dataset, we used the following cleaning steps:

---

## **1. Remove duplicates**
Inspection datasets often repeat rows.
We removed duplicates based on:
- `camis` (restaurant ID)
- `inspection_date`
- `violation_code`

---

## **2. Convert dates**
Converted:
- `inspection_date`
- `grade_date`
- `record_date`

into proper `datetime` objects.

---

## **3. Handle Missing Values**
- Missing ZIP → remove (cannot predict location)  
- Missing latitude/longitude → remove  
- Missing demographic features → set indicator `demo_missing = 1`  
- Missing population → set `pop_missing = 1`  

Indicator features actually **help** the model understand when data is incomplete.

---

## **4. Convert categorical values**
Converted:
- `boro`
- `cuisine_description`
- `violation_code`

into model-ready categorical features.

---

## Result
A clean dataset of **24,050 rows** ready for ML training.
""",

    "Post 3 — The Merge Problem: ZIP Codes vs Neighborhoods": """
### 📌 Post 3 — The Merge Problem: ZIP Codes vs Neighborhoods

This was the trickiest part of the entire pipeline.

---

## ❌ Problem: Demographic dataset had *no ZIP code column*
It only had:
- Borough  
- Neighborhood name  

But our restaurant dataset uses **ZIP codes**, not neighborhood names.

This means:
> We needed a bridge between ZIP codes and neighborhoods.

---

## 🔧 Solution: Neighborhood mapping
We used an additional dataset that maps:
**ZIP → Neighborhood**

Then we could:
- Map each ZIP to a neighborhood
- Bring demographic data into the restaurant dataset

---

## ⚠️ Accuracy Impact
Neighborhood boundaries do **not** perfectly match ZIP boundaries.

But:
- Neighborhoods reflect socioeconomic conditions better  
- Demographic data still provides useful signals  
- The model learns overall patterns, not exact values  

This improved accuracy, even though:
- Some rows were dropped  
- Some ZIP → neighborhood matches were approximate  

---

## ✔️ Why it STILL improves predictions
Demographics add:
- Poverty rate  
- Income  
- Racial composition  
- Indexscore (financial health)

Even if ZIP/neighborhood alignment isn’t perfect:
➡️ Restaurants in wealthier areas tend to have fewer critical violations  
➡️ Higher-poverty ZIPs show higher average scores  

The model benefits from these patterns.
""",

    "Post 4 — Feature Engineering (17+ Inputs to the Model)": """
### 📌 Post 4 — Feature Engineering (17+ Inputs to the Model)

Feature engineering is what makes the model reliable.

---

## **1. Numeric Features**
- `score`  
- `nyc_poverty_rate`  
- `median_income`  
- `perc_white`, `perc_black`, etc.  
- `population`  
- `indexscore`  

These capture:
- Cleanliness indicators  
- Socioeconomic environment  

---

## **2. Categorical Features**
- `boro`  
- `zipcode`  
- `cuisine_description`  
- `violation_code`  

Converted with one-hot encoding (handled automatically by Random Forests).

---

## **3. Indicator Flags**
- `pop_missing`  
- `demo_missing`  

These tell the model:
> “This ZIP or neighborhood had incomplete data.”

Models perform better when they *know* something is missing.

---

## **Result**
We created a **17-feature vector** that provides a complete picture of a restaurant’s environment.
""",

    "Post 5 — Population Density Dataset: Why It Matters": """
### 📌 Post 5 — Population Density Dataset: Why It Matters

Population helps explain patterns in restaurant cleanliness.

---

## **1. Crowded ZIPs have more inspections**
Dense ZIP codes (like Manhattan):
- More daily customers  
- More violations  
- More frequent inspections  

Low-density ZIPs (like Staten Island) often show:
- Fewer violations  
- More A grades  

---

## **2. Adding Population Improved Model Stability**
Even if population doesn’t directly predict a grade:
➡️ It stabilizes the model  
➡️ It helps distinguish restaurants in different types of neighborhoods  

---

## **3. `pop_missing` is also valuable**
If population was missing for a ZIP:
- This often indicates rare or special-case ZIPs  
- The model learns not to overtrust demographic features  

---

## Result
Population density became an important “context feature.”
""",

    "Post 6 — Model Training & Validation": """
### 📌 Post 6 — Model Training & Validation

---

## **Why Random Forest?**
Because it:
- Handles categorical + numeric features  
- Handles missing flags automatically  
- Reduces overfitting  
- Gives feature importance  

Perfect for mixed NYC data.

---

## **Feature Importances**
The most important were:
1. **score**  
2. **zipcode**  
3. **critical_flag**  
4. **cuisine_description**  
5. **poverty_rate**  

Which confirms:
➡️ Cleanliness score is the strongest predictor  
➡️ Demographics add meaningful signal  

---

## **Validation**
- Train-test split  
- Multiple experiments  
- Stable accuracy across subsets  

Model performs reliably.
""",

    "Post 7 — Prediction Pipeline End-to-End": """
### 📌 Post 7 — Prediction Pipeline End-to-End

---

## **1. User clicks a restaurant**
Either:
- From the dataset  
- From Google Places  

---

## **2. Reverse Geocode (if Google mode)**
We extract:
- Address  
- Borough  
- ZIP code  

---

## **3. Normalize Google data**
We convert Google’s format into our model’s format:
- Cuisine  
- ZIP  
- Borough  
- Score placeholder  
- Violation placeholder  

---

## **4. Build feature vector**
We fill:
- demographics  
- population  
- missing flags  
- categorical encodings  

---

## **5. Make prediction**
Model outputs:
- Grade (A/B/C)  
- Probabilities for each grade  

---

## Result
The pipeline is fast, accurate, and works seamlessly with both dataset and live Google results.
""",

    "Post 8 — Lessons Learned": """
### 📌 Post 8 — Lessons Learned

---

## **1. Merging datasets is messy**
ZIPs and neighborhoods don’t align perfectly.
But demographics still improved accuracy.

---

## **2. More data ≠ better data**
We lost many rows during merging  
…but the resulting dataset was:
- cleaner  
- more consistent  
- more interpretable  

---

## **3. Adding demographic and population data helps**
Even if approximate, the model becomes:
- more stable  
- less overfitted  
- better at edge cases  

---

## **4. Future Improvements**
- Add DOH real-time updates  
- More cuisine-level analysis  
- Deep learning models  
- Predict violation types, not just grade  
"""
}

# ----------------------------------------------------------
# Dropdown UI
# ----------------------------------------------------------

selected_post = st.selectbox(
    "Select a blog post to read:",
    ["-- Select a post --"] + list(POSTS.keys()),
)

st.markdown("---")

if selected_post != "-- Select a post --":
    st.markdown(POSTS[selected_post], unsafe_allow_html=True)

    if st.button("Close Post"):
        st.experimental_set_query_params()  # resets selection
        st.rerun()
else:
    st.info("Select a post from the dropdown to begin.")
