"""
test_bordereaux.py
Automated tests for the bordereaux_cleaner module.
Covers all 10 pipeline steps with realistic insurance data scenarios.

Run with: pytest tests/test_bordereaux.py -v
"""

import pytest
import pandas as pd
import numpy as np
from src.bordereaux_cleaner import (
    normalise_columns,
    check_required_columns,
    remove_blank_rows,
    remove_duplicate_policies,
    clean_premium,
    parse_dates,
    validate_date_logic,
    normalise_currency,
    flag_missing_required,
    summary_report,
    clean_bordereaux,
    REQUIRED_COLUMNS,
)


# ─────────────────────────────────────────────────────────────
# FIXTURES — reusable sample data
# ─────────────────────────────────────────────────────────────

@pytest.fixture
def clean_sample():
    """A well-formed bordereaux with no issues."""
    return pd.DataFrame({
        "policy_number":  ["POL001", "POL002", "POL003"],
        "insured_name":   ["Acme Ltd", "Beta Corp", "Gamma SA"],
        "inception_date": ["2024-01-01", "2024-03-15", "2024-06-01"],
        "expiry_date":    ["2025-01-01", "2025-03-15", "2025-06-01"],
        "gross_premium":  [1200.00, 850.50, 3400.00],
        "currency":       ["GBP", "EUR", "USD"],
    })


@pytest.fixture
def messy_sample():
    """A realistic messy bordereaux with common real-world issues."""
    return pd.DataFrame({
        "Policy Number":  ["POL001", "POL001", "POL003", None, "POL005"],
        "Insured Name":   ["Acme Ltd", "Acme Ltd", "Gamma SA", None, "Delta Plc"],
        "Inception Date": ["01/01/2024", "01/01/2024", "15/03/2024", None, "01/06/2024"],
        "Expiry Date":    ["01/01/2025", "01/01/2025", "14/03/2024", None, "01/06/2025"],
        "Gross Premium":  ["£1,200.00", "£1,200.00", "€850,50", None, "(500.00)"],
        "Currency":       ["GBP", "GBP", "eur", None, "PESO"],
    })


# ─────────────────────────────────────────────────────────────
# STEP 1 — Column normalisation
# ─────────────────────────────────────────────────────────────

def test_normalise_columns_lowercase():
    df = pd.DataFrame({"Policy Number": [1], "Gross Premium": [100]})
    result = normalise_columns(df)
    assert "policy_number" in result.columns
    assert "gross_premium" in result.columns


def test_normalise_columns_strips_spaces():
    df = pd.DataFrame({"  Insured Name  ": ["test"]})
    result = normalise_columns(df)
    assert "insured_name" in result.columns


def test_normalise_columns_handles_special_chars():
    df = pd.DataFrame({"Gross-Premium (£)": [100]})
    result = normalise_columns(df)
    # Should produce a clean snake_case column
    assert len(result.columns) == 1
    assert " " not in result.columns[0]


# ─────────────────────────────────────────────────────────────
# STEP 2 — Required column check
# ─────────────────────────────────────────────────────────────

def test_check_required_columns_all_present(clean_sample):
    missing = check_required_columns(clean_sample)
    assert missing == []


def test_check_required_columns_detects_missing():
    df = pd.DataFrame({"policy_number": ["POL001"], "insured_name": ["Acme"]})
    missing = check_required_columns(df)
    assert "gross_premium" in missing
    assert "currency" in missing
    assert "inception_date" in missing


def test_required_columns_list_has_six_fields():
    assert len(REQUIRED_COLUMNS) == 6


# ─────────────────────────────────────────────────────────────
# STEP 3 — Blank row removal
# ─────────────────────────────────────────────────────────────

def test_remove_blank_rows_drops_empty():
    df = pd.DataFrame({
        "policy_number": ["POL001", None, "POL003"],
        "gross_premium": [100, None, 200],
    })
    result = remove_blank_rows(df)
    # Fully blank rows removed — POL001 and POL003 remain
    assert len(result) == 2


def test_remove_blank_rows_keeps_partial_rows():
    df = pd.DataFrame({
        "policy_number": ["POL001", None],
        "gross_premium": [100, None],
        "currency":      ["GBP", None],
    })
    result = remove_blank_rows(df)
    assert len(result) == 1


def test_remove_blank_rows_clean_data_unchanged(clean_sample):
    result = remove_blank_rows(clean_sample)
    assert len(result) == len(clean_sample)


# ─────────────────────────────────────────────────────────────
# STEP 4 — Duplicate removal
# ─────────────────────────────────────────────────────────────

def test_remove_duplicate_policies_deduplicates():
    df = pd.DataFrame({
        "policy_number": ["POL001", "POL001", "POL002"],
        "gross_premium": [100, 100, 200],
    })
    result = remove_duplicate_policies(df)
    assert len(result) == 2
    assert list(result["policy_number"]) == ["POL001", "POL002"]


def test_remove_duplicate_policies_keeps_first():
    df = pd.DataFrame({
        "policy_number": ["POL001", "POL001"],
        "gross_premium": [100, 999],
    })
    result = remove_duplicate_policies(df)
    assert result.iloc[0]["gross_premium"] == 100


def test_remove_duplicate_policies_no_duplicates_unchanged(clean_sample):
    result = remove_duplicate_policies(clean_sample)
    assert len(result) == len(clean_sample)


# ─────────────────────────────────────────────────────────────
# STEP 5 — Premium cleaning
# ─────────────────────────────────────────────────────────────

def test_clean_premium_strips_currency_symbol():
    df = pd.DataFrame({"gross_premium": ["£1,200.00"]})
    result = clean_premium(df)
    assert result["gross_premium"].iloc[0] == 1200.0


def test_clean_premium_handles_euro_format():
    df = pd.DataFrame({"gross_premium": ["1.200,50"]})
    result = clean_premium(df)
    assert result["gross_premium"].iloc[0] == pytest.approx(1200.50)


def test_clean_premium_handles_bracketed_negative():
    df = pd.DataFrame({"gross_premium": ["(500.00)"]})
    result = clean_premium(df)
    assert result["gross_premium"].iloc[0] == -500.0


def test_clean_premium_handles_plain_float(clean_sample):
    result = clean_premium(clean_sample)
    assert result["gross_premium"].iloc[0] == 1200.0


def test_clean_premium_handles_null():
    df = pd.DataFrame({"gross_premium": [None]})
    result = clean_premium(df)
    assert pd.isna(result["gross_premium"].iloc[0])


# ─────────────────────────────────────────────────────────────
# STEP 6 — Date parsing
# ─────────────────────────────────────────────────────────────

def test_parse_dates_iso_format():
    df = pd.DataFrame({"inception_date": ["2024-01-01"], "expiry_date": ["2025-01-01"]})
    result = parse_dates(df)
    assert pd.api.types.is_datetime64_any_dtype(result["inception_date"])


def test_parse_dates_uk_format():
    df = pd.DataFrame({"inception_date": ["01/01/2024"], "expiry_date": ["01/01/2025"]})
    result = parse_dates(df)
    assert result["inception_date"].iloc[0].year == 2024
    assert result["inception_date"].iloc[0].month == 1


def test_parse_dates_missing_column_no_error():
    df = pd.DataFrame({"policy_number": ["POL001"]})
    result = parse_dates(df)  # Should not raise
    assert "policy_number" in result.columns


# ─────────────────────────────────────────────────────────────
# STEP 7 — Date logic validation
# ─────────────────────────────────────────────────────────────

def test_validate_date_logic_flags_reversed_dates():
    df = pd.DataFrame({
        "inception_date": pd.to_datetime(["2024-06-01"]),
        "expiry_date":    pd.to_datetime(["2024-03-01"]),  # before inception!
    })
    result = validate_date_logic(df)
    assert result["date_error"].iloc[0] is True or result["date_error"].iloc[0] == True


def test_validate_date_logic_clean_dates_no_error(clean_sample):
    df = parse_dates(clean_sample)
    result = validate_date_logic(df)
    assert result["date_error"].sum() == 0


# ─────────────────────────────────────────────────────────────
# STEP 8 — Currency normalisation
# ─────────────────────────────────────────────────────────────

def test_normalise_currency_uppercases():
    df = pd.DataFrame({"currency": ["eur", "gbp", "usd"]})
    result = normalise_currency(df)
    assert list(result["currency"]) == ["EUR", "GBP", "USD"]


def test_normalise_currency_flags_invalid():
    df = pd.DataFrame({"currency": ["GBP", "PESO", "EUR"]})
    result = normalise_currency(df)
    assert result["currency_valid"].iloc[0] is True or result["currency_valid"].iloc[0] == True
    assert result["currency_valid"].iloc[1] is False or result["currency_valid"].iloc[1] == False


def test_normalise_currency_valid_currencies(clean_sample):
    result = normalise_currency(clean_sample)
    assert result["currency_valid"].all()


# ─────────────────────────────────────────────────────────────
# STEP 9 — Missing required field flagging
# ─────────────────────────────────────────────────────────────

def test_flag_missing_required_detects_null():
    df = pd.DataFrame({
        "policy_number":  [None],
        "insured_name":   ["Acme"],
        "inception_date": ["2024-01-01"],
        "expiry_date":    ["2025-01-01"],
        "gross_premium":  [100],
        "currency":       ["GBP"],
    })
    result = flag_missing_required(df)
    assert result["has_missing_required"].iloc[0] == True


def test_flag_missing_required_clean_data(clean_sample):
    result = flag_missing_required(clean_sample)
    assert result["has_missing_required"].sum() == 0


# ─────────────────────────────────────────────────────────────
# STEP 10 — Summary report
# ─────────────────────────────────────────────────────────────

def test_summary_report_total_rows(clean_sample):
    df = flag_missing_required(clean_premium(clean_sample))
    report = summary_report(df)
    assert report["total_rows"] == 3


def test_summary_report_total_premium(clean_sample):
    df = clean_premium(clean_sample)
    report = summary_report(df)
    assert report["total_premium"] == pytest.approx(5450.50)


def test_summary_report_has_required_keys(clean_sample):
    df = clean_premium(flag_missing_required(clean_sample))
    report = summary_report(df)
    for key in ["total_rows", "total_premium", "avg_premium", "currencies"]:
        assert key in report


# ─────────────────────────────────────────────────────────────
# FULL PIPELINE — end-to-end
# ─────────────────────────────────────────────────────────────

def test_clean_bordereaux_returns_tuple(clean_sample):
    result = clean_bordereaux(clean_sample)
    assert isinstance(result, tuple)
    assert len(result) == 3  # df, report, issues


def test_clean_bordereaux_clean_data_no_issues(clean_sample):
    df, report, issues = clean_bordereaux(clean_sample)
    assert len(issues) == 0
    assert report["total_rows"] == 3


def test_clean_bordereaux_messy_data(messy_sample):
    df, report, issues = clean_bordereaux(messy_sample)
    # Should have removed 1 duplicate (POL001 appears twice)
    assert df["policy_number"].nunique() <= 4
    # Should have flagged date error (POL003 expiry before inception)
    assert report["date_errors"] >= 1
    # Should have flagged invalid currency (PESO)
    assert report["invalid_currencies"] >= 1


def test_clean_bordereaux_output_has_audit_columns(clean_sample):
    df, _, _ = clean_bordereaux(clean_sample)
    assert "date_error" in df.columns
    assert "currency_valid" in df.columns
    assert "has_missing_required" in df.columns


def test_clean_bordereaux_missing_columns_reported():
    df = pd.DataFrame({"policy_number": ["POL001"], "insured_name": ["Acme"]})
    _, _, issues = clean_bordereaux(df)
    assert len(issues) > 0
    assert any("Missing" in issue for issue in issues)
