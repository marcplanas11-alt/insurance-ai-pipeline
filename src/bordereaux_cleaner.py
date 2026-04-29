"""
bordereaux_cleaner.py
Cleans and validates raw bordereaux data for MGA/reinsurance operations.
Handles common data quality issues found in Lloyd's and EU carrier bordereau files.

Author: Marc Planas — AI-Enabled Insurance Operations
"""

import pandas as pd
import re
from datetime import datetime


# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────

REQUIRED_COLUMNS = [
    "policy_number",
    "insured_name",
    "inception_date",
    "expiry_date",
    "gross_premium",
    "currency",
]

VALID_CURRENCIES = ["GBP", "EUR", "USD", "CHF", "NOK", "SEK", "DKK"]

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%Y%m%d"]


# ─────────────────────────────────────────────────────────────
# CLEANING FUNCTIONS
# ─────────────────────────────────────────────────────────────

def load_bordereaux(filepath: str) -> pd.DataFrame:
    """Load a bordereaux CSV or Excel file into a DataFrame."""
    if filepath.endswith(".csv"):
        df = pd.read_csv(filepath)
    elif filepath.endswith((".xlsx", ".xls")):
        df = pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath}. Use .csv or .xlsx")
    return df


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Standardise column names: lowercase, strip spaces, replace spaces with underscores."""
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
        .str.replace(r"[^\w]", "", regex=True)
    )
    return df


def check_required_columns(df: pd.DataFrame) -> list:
    """Return list of any required columns that are missing."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    return missing


def remove_blank_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows that are entirely empty."""
    return df.dropna(how="all").reset_index(drop=True)


def remove_duplicate_policies(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate policy numbers, keeping the first occurrence."""
    if "policy_number" not in df.columns:
        return df
    before = len(df)
    df = df.drop_duplicates(subset=["policy_number"], keep="first").reset_index(drop=True)
    removed = before - len(df)
    if removed > 0:
        print(f"  Removed {removed} duplicate policy number(s)")
    return df


def clean_premium(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert gross_premium to float.
    Handles values like '£1,200.50', '1.200,50', '$500', '(200)' (negative).
    """
    if "gross_premium" not in df.columns:
        return df

    def parse_premium(val):
        if pd.isna(val):
            return None
        s = str(val).strip()
        # Handle bracketed negatives e.g. (200.00)
        negative = s.startswith("(") and s.endswith(")")
        # Strip currency symbols, spaces, commas used as thousands separators
        s = re.sub(r"[£$€\s]", "", s)
        s = re.sub(r"[()]", "", s)
        # Handle European format: 1.200,50 → 1200.50
        if re.match(r"^\d{1,3}(\.\d{3})*(,\d+)?$", s):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
        try:
            result = float(s)
            return -result if negative else result
        except ValueError:
            return None

    df = df.copy()
    df["gross_premium"] = df["gross_premium"].apply(parse_premium)
    return df


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse inception_date and expiry_date columns to datetime,
    trying multiple common date formats used in EU/Lloyd's bordereau files.
    """
    df = df.copy()
    for col in ["inception_date", "expiry_date"]:
        if col not in df.columns:
            continue
        parsed = None
        for fmt in DATE_FORMATS:
            try:
                parsed = pd.to_datetime(df[col], format=fmt, errors="coerce")
                if parsed.notna().sum() > 0:
                    break
            except Exception:
                continue
        if parsed is not None:
            df[col] = parsed
    return df


def validate_date_logic(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag rows where expiry_date is before inception_date.
    Adds a boolean column 'date_error'.
    """
    df = df.copy()
    if "inception_date" in df.columns and "expiry_date" in df.columns:
        df["date_error"] = (
            pd.to_datetime(df["expiry_date"], errors="coerce") <
            pd.to_datetime(df["inception_date"], errors="coerce")
        )
    return df


def normalise_currency(df: pd.DataFrame) -> pd.DataFrame:
    """Uppercase and strip currency codes. Flag invalid currencies."""
    if "currency" not in df.columns:
        return df
    df = df.copy()
    df["currency"] = df["currency"].str.strip().str.upper()
    df["currency_valid"] = df["currency"].isin(VALID_CURRENCIES)
    invalid = df[~df["currency_valid"]]["currency"].unique()
    if len(invalid) > 0:
        print(f"  Invalid currency codes found: {list(invalid)}")
    return df


def flag_missing_required(df: pd.DataFrame) -> pd.DataFrame:
    """Add a 'has_missing_required' column flagging rows with any missing required field."""
    df = df.copy()
    present_required = [c for c in REQUIRED_COLUMNS if c in df.columns]
    df["has_missing_required"] = df[present_required].isnull().any(axis=1)
    return df


# ─────────────────────────────────────────────────────────────
# SUMMARY REPORT
# ─────────────────────────────────────────────────────────────

def summary_report(df: pd.DataFrame, blank_rows_removed: int = 0) -> dict:
    """Return a dict of key data quality metrics."""
    report = {
        "total_rows":          len(df),
        "total_columns":       len(df.columns),
        "blank_rows_removed":  blank_rows_removed,
        "date_errors":         int(df["date_error"].sum()) if "date_error" in df.columns else 0,
        "invalid_currencies":  int((~df["currency_valid"]).sum()) if "currency_valid" in df.columns else 0,
        "total_premium":       round(df["gross_premium"].sum(), 2) if "gross_premium" in df.columns else None,
        "avg_premium":         round(df["gross_premium"].mean(), 2) if "gross_premium" in df.columns else None,
        "currencies":          df["currency"].value_counts().to_dict() if "currency" in df.columns else {},
    }
    return report


# ─────────────────────────────────────────────────────────────
# MAIN PIPELINE — run all steps in sequence
# ─────────────────────────────────────────────────────────────

def clean_bordereaux(df: pd.DataFrame) -> tuple:
    """
    Run the full cleaning pipeline on a bordereaux DataFrame.

    Returns:
        cleaned_df  (pd.DataFrame): cleaned and validated data
        report      (dict):         data quality summary
        issues      (list):         list of any structural issues found
    """
    issues = []

    # Step 1 — normalise column names
    df = normalise_columns(df)

    # Step 2 — check required columns
    missing_cols = check_required_columns(df)
    if missing_cols:
        issues.append(f"Missing required columns: {missing_cols}")

    # Step 3 — remove blank rows
    _before_blank = len(df)
    df = remove_blank_rows(df)
    blank_rows_removed = _before_blank - len(df)

    # Step 4 — remove duplicates
    df = remove_duplicate_policies(df)

    # Step 5 — clean premium values
    df = clean_premium(df)

    # Step 6 — parse dates
    df = parse_dates(df)

    # Step 7 — validate date logic
    df = validate_date_logic(df)

    # Step 8 — normalise currency
    df = normalise_currency(df)

    # Step 9 — flag missing required fields
    df = flag_missing_required(df)

    # Step 10 — build report
    report = summary_report(df, blank_rows_removed=blank_rows_removed)

    return df, report, issues
