import streamlit as st

st.set_page_config(page_title="CleanKitchen Blog", layout="wide")

st.title("📝 CleanKitchen NYC — Project Blog")
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

if "selected_post" not in st.session_state:
    st.session_state.selected_post = None

selected = st.selectbox(
    "Select a post to read:",
    ["-- Select a post --"] + list(POSTS.keys()),
    key="selected_post"
)

st.markdown("---")

# ----------------------------------------------------------
# Render post in a card
# ----------------------------------------------------------

if selected and selected != "-- Select a post --":
    st.markdown(
        """
        <div style='background:white; padding:30px; border-radius:12px;
        box-shadow:0 0 12px rgba(0,0,0,0.12); margin-bottom:20px;'>
        """,
        unsafe_allow_html=True
    )

    st.markdown(POSTS[selected], unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    selected = st.selectbox(
        "Select a post to read:",
        ["-- Select a post --"] + list(POSTS.keys()),
        key="selected_post",
    )

    # Close button — correctly resets a widget-controlled session_state key
    if st.button("Close Post"):
        st.session_state["selected_post"] = "-- Select a post --"
        st.rerun()

else:
    st.info("Select a blog post from the dropdown to view details.")
