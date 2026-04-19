"""
clean.py
Text normalization and data cleaning for VetFees column.
"""

import pandas as pd
import re


def normalize_text(text: str) -> str:
    """
    Normalize unstructured text:
    - Convert to lowercase
    - Strip leading/trailing whitespace
    - Collapse multiple spaces
    """
    if pd.isna(text):
        return ""
    text = str(text).lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def clean_vetfees_column(df: pd.DataFrame, column: str = "VetFees") -> pd.DataFrame:
    """
    Clean and normalize VetFees (or similar) text column.

    Creates a new column: {column}_clean

    Args:
        df: Input DataFrame
        column: Name of text column to clean (default: "VetFees")

    Returns:
        DataFrame with {column}_clean added
    """
    df = df.copy()
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame")

    df[f"{column}_clean"] = df[column].apply(normalize_text)
    return df


def remove_null_vetfees(df: pd.DataFrame, column: str = "VetFees") -> pd.DataFrame:
    """Remove rows where VetFees is empty after cleaning."""
    df = df.copy()
    clean_col = f"{column}_clean"
    if clean_col in df.columns:
        df = df[df[clean_col].str.len() > 0].reset_index(drop=True)
    return df
