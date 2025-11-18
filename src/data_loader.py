import pandas as pd
import os
import streamlit as st

# -------------------------------------------------
# BASE PATHS
# -------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# ✔️ Updated filenames based on your correction
RESTAURANT_DATA_PATH = os.path.join(DATA_DIR, "df_merged_big.csv")
NFH_DATA_PATH = os.path.join(DATA_DIR, "df_demo_clean.csv")


# -------------------------------------------------
# 1. Load datasets with Streamlit caching
# -------------------------------------------------

@st.cache_data
def load_restaurant_data():
    """
    Loads the cleaned restaurant dataset.
    Must include: borough, zipcode, cuisine_description, score,
    critical_flag_bin, and coordinates for mapping.
    """
    df = pd.read_csv(RESTAURANT_DATA_PATH)

    # Clean/standardize core fields
    df['borough'] = df['borough'].astype(str).str.strip()

    df['cuisine_description'] = df['cuisine_description'].astype(str).str.strip().str.title()

    # Ensure zipcode is numeric
    df['zipcode'] = pd.to_numeric(df['zipcode'], errors='coerce').fillna(0).astype(int)

    return df


@st.cache_data
def load_nfh_data():
    """
    Loads the NFH demographic dataset.
    Standardizes borough & neighborhood columns.
    Uses 'neighborhood_simple' as the normalized neighborhood field.
    """

    df = pd.read_csv(NFH_DATA_PATH)

    # Standardize borough
    df["borough"] = df["borough"].astype(str).str.title().str.strip()

    # Use the cleaned neighborhood column: 'neighborhood_simple'
    if "neighborhood_simple" in df.columns:
        df["neighborhood"] = (
            df["neighborhood_simple"]
            .astype(str)
            .str.lower()
            .str.replace(r"[^a-z\s]", "", regex=True)
            .str.strip()
        )
    else:
        raise KeyError("❌ 'neighborhood_simple' column not found in NFH dataset.")

    return df



# -------------------------------------------------
# 2. Merge Restaurant + NFH datasets
# -------------------------------------------------

@st.cache_data
def load_merged_data():
    """
    Merges restaurant data (df_merged_big.csv) with NFH demographics (df_demo_clean.csv)
    using borough + neighborhood, and safely fills missing demo values.
    """

    df_rest = load_restaurant_data()
    df_nfh = load_nfh_data()

    # ----------------------------
    # Normalize RESTAURANT neighborhood
    # ----------------------------
    rest_neigh_col = None
    for col in ["neighborhood", "neighborhoods", "neighborhood_simple"]:
        if col in df_rest.columns:
            rest_neigh_col = col
            break

    if rest_neigh_col:
        df_rest["neighborhood"] = (
            df_rest[rest_neigh_col]
            .astype(str)
            .str.lower()
            .str.replace(r"[^a-z\s]", "", regex=True)
            .str.strip()
        )
    else:
        # If no neighborhood column exists, still create it so merge doesn't break
        df_rest["neighborhood"] = None

    # ----------------------------
    # Merge with NFH data on borough + neighborhood
    # ----------------------------
    df_merged = pd.merge(
        df_rest,
        df_nfh,
        on=["borough", "neighborhood"],
        how="left",
        suffixes=("", "_nfh")
    )

    # ----------------------------
    # Ensure required demographic columns exist
    # ----------------------------
    required_demo_cols = [
        "nyc_poverty_rate",
        "median_income",
        "perc_white",
        "perc_black",
        "perc_asian",
        "perc_hispanic",
        "indexscore",
    ]

    for col in required_demo_cols:
        if col not in df_merged.columns:
            # If the column is missing entirely, create it as NaN so code doesn't crash
            df_merged[col] = pd.NA

        # Fill missing demographic values using borough-level averages
        df_merged[col] = df_merged.groupby("borough")[col].transform(
            lambda x: x.fillna(x.mean())
        )

    return df_merged



# -------------------------------------------------
# Public function app will import
# -------------------------------------------------

def get_data():
    return load_merged_data()
