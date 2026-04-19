"""
load.py
Load and validate raw insurance bordereaux data.
"""

import pandas as pd


def load_data(filepath: str) -> pd.DataFrame:
    """
    Load insurance bordereaux from CSV or Excel.

    Args:
        filepath: Path to CSV or XLSX file

    Returns:
        pd.DataFrame with raw data
    """
    if filepath.endswith(".csv"):
        return pd.read_csv(filepath)
    elif filepath.endswith((".xlsx", ".xls")):
        return pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported format: {filepath}. Use .csv or .xlsx")


def validate_required_columns(df: pd.DataFrame, required: list[str]) -> None:
    """
    Verify all required columns are present.

    Raises:
        ValueError if any required column is missing
    """
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
