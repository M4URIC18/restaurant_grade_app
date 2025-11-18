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
    Merges restaurants with NFH demographic data.
    Matching is done by borough + neighborhood primarily.
    Fallback logic fills missing demographic values using borough-level means.
    """

    df_rest = load_restaurant_data()
    df_nfh = load_nfh_data()

    # Clean restaurant neighborhood field if present
    # Restaurant dataset neighborhood column (if present)
    possible_rest_neigh_cols = ["neighborhood", "neighborhoods", "neighborhood_simple"]

    rest_neigh_col = None
    for col in possible_rest_neigh_cols:
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
        # Fallback: manually create missing neighborhood so merge still works
        df_rest["neighborhood"] = None


    # First merge by borough + neighborhood
    df_merged = pd.merge(
        df_rest,
        df_nfh,
        on=["borough", "neighborhood"],
        how="left"
    )

    # Fallback if demographic values missing
    missing = df_merged['median_income'].isna().sum()
    if missing > 0:
        print(f"⚠️ {missing} rows missing NFH match, applying borough-level fallback...")

        # Borough-level mean demographic stats
        borough_stats = (
            df_nfh.groupby("borough")
            .mean(numeric_only=True)
            .reset_index()
        )

        df_merged = pd.merge(
            df_merged,
            borough_stats,
            on="borough",
            suffixes=("", "_boroughfallback"),
            how="left"
        )

        # Fill missing values
        for col in [
            'median_income', 'indexscore', 'nyc_poverty_rate',
            'perc_white', 'perc_black', 'perc_asian', 'perc_hispanic'
        ]:
            df_merged[col] = df_merged[col].fillna(df_merged[col + "_boroughfallback"])

    return df_merged


# -------------------------------------------------
# Public function app will import
# -------------------------------------------------

def get_data():
    return load_merged_data()
