import pandas as pd

def load_data(path):
    return pd.read_csv(path)

def clean_vetfees(df):
    df = df.copy()
    df["VetFees_clean"] = df["VetFees"].fillna("").astype(str).str.lower()
    return df
