# CleanKitchen NYC

A simple and clear tool to explore NYC restaurant grades using real inspection data and machine learning.

## What This Project Does

* Shows restaurant inspection grades across New York City
* Predicts the next likely grade (A, B, C, etc.) using a trained ML model
* Lets users filter by ZIP code, cuisine, borough, and grade
* Displays restaurants on an interactive map (OpenStreetMap)
* Shows basic neighborhood data such as income and poverty rates

## Machine Learning Model

* Trained on over 290K NYC inspection records
* Uses Random Forest for multi-class prediction
* Key features include: score, ZIP code, critical flags, and demographic averages
* Outputs predicted grade and the probability for each class

## Project Structure

```
project/
│
├── app.py                   # Streamlit main app
├── README.md                # Project overview
├── models/                  # Saved ML models (.joblib)
├── data/                    # Clean datasets
├── src/
│   ├── data_loader.py       # Load and prepare data
│   ├── predictor.py         # ML prediction logic
│   ├── utils.py             # Helper functions
│   └── style.css            # Custom website styles
```

## How It Works

1. User opens the web app
2. User filters by ZIP, cuisine, or borough
3. Restaurants appear on the map
4. Clicking a restaurant sends its info to the model
5. Model returns predicted grade and explanation

## Data Sources

* NYC Open Data: Restaurant Inspection Results
* Neighborhood financial and demographic dataset

## Tech Used

* **Python** (Pandas, Scikit-Learn)
* **Streamlit** for the UI
* **Folium + OSM** for maps
* **Joblib** for model saving

## ⚙️ Setup

Install packages:

```
pip install -r requirements.txt
```

Run the app:

```
streamlit run app.py
```

## Future Work

* Add more map layers
* Improve prediction accuracy
* Add restaurant risk indicators
* Add FastAPI backend for larger scale

## Contact

For help or questions, reach out any time!
