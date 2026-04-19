"""
parse.py
Extract structured fields from unstructured VetFees text using regex patterns.
"""

import re
import pandas as pd


# Pattern definitions
PATTERN_CLAIM_LIMIT = r'(?:limit|coverage|max)[\s:]*(?:of\s+)?[£$€][\s]*([0-9,]+(?:\.\d{2})?)'
PATTERN_EXCESS = r'excess[\s:]*(?:amount)?[\s:]*[£$€][\s]*([0-9,]+(?:\.\d{2})?)'
PATTERN_UNLIMITED = r'(?:unlimited|no limit|no\s+limit|fully covered|comprehensive)'

# Confidence thresholds
CONFIDENCE_HIGH = 0.95
CONFIDENCE_MED = 0.70
CONFIDENCE_LOW = 0.40


def extract_claim_limit(text: str) -> tuple[float | None, float]:
    """
    Extract claim limit from text.

    Args:
        text: Cleaned VetFees text

    Returns:
        (amount, confidence) - amount in GBP or None, confidence score 0-1
    """
    try:
        if pd.isna(text):
            return None, 0.0
    except (TypeError, ValueError):
        pass

    if not text:
        return None, 0.0

    if re.search(PATTERN_UNLIMITED, text):
        return None, CONFIDENCE_HIGH

    match = re.search(PATTERN_CLAIM_LIMIT, text)
    if match:
        try:
            amount_str = match.group(1).replace(",", "")
            amount = float(amount_str)
            return amount, CONFIDENCE_HIGH
        except (ValueError, AttributeError):
            pass

    # Fallback: look for any £ amount
    fallback_match = re.search(r'£[\s]*([0-9,]+(?:\.\d{2})?)', text)
    if fallback_match:
        try:
            amount_str = fallback_match.group(1).replace(",", "")
            amount = float(amount_str)
            return amount, CONFIDENCE_MED
        except (ValueError, AttributeError):
            pass

    return None, 0.0


def extract_excess(text: str) -> tuple[float | None, float]:
    """
    Extract excess amount from text.

    Args:
        text: Cleaned VetFees text

    Returns:
        (amount, confidence) - amount in GBP or None, confidence score 0-1
    """
    try:
        if pd.isna(text):
            return None, 0.0
    except (TypeError, ValueError):
        pass

    if not text:
        return None, 0.0

    match = re.search(PATTERN_EXCESS, text)
    if match:
        try:
            amount_str = match.group(1).replace(",", "")
            amount = float(amount_str)
            return amount, CONFIDENCE_HIGH
        except (ValueError, AttributeError):
            pass

    return None, 0.0


def classify_parse_status(
    text: str,
    claim_limit: float | None,
    excess: float | None,
    claim_confidence: float,
    excess_confidence: float,
) -> str:
    """
    Classify parsing success based on extracted fields and confidence.

    Returns one of:
        - parsed: Both limit and excess extracted with high confidence
        - partial: One field extracted with high confidence, other missing
        - ambiguous: Fields extracted but with low confidence
        - failed: Neither field extracted
    """
    if not text or pd.isna(text):
        return "failed"

    has_limit = claim_limit is not None and claim_confidence >= CONFIDENCE_HIGH
    has_excess = excess is not None and excess_confidence >= CONFIDENCE_HIGH

    if has_limit and has_excess:
        return "parsed"

    if has_limit or has_excess:
        return "partial"

    if claim_confidence > 0 or excess_confidence > 0:
        return "ambiguous"

    return "failed"


def parse_vetfees(df: pd.DataFrame, column: str = "VetFees_clean") -> pd.DataFrame:
    """
    Extract all fields from cleaned VetFees text.

    Creates columns:
        - ClaimLimit_gbp: Extracted claim limit in GBP
        - ClaimLimit_confidence: Extraction confidence (0-1)
        - VetFeesExcessAmount: Extracted excess in GBP
        - VetFeesExcess_confidence: Extraction confidence (0-1)
        - parse_status: Classification (parsed/partial/ambiguous/failed)

    Args:
        df: DataFrame with {column}
        column: Name of cleaned text column

    Returns:
        DataFrame with extracted fields added
    """
    df = df.copy()
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame")

    df["ClaimLimit_gbp"] = None
    df["ClaimLimit_confidence"] = 0.0
    df["VetFeesExcessAmount"] = None
    df["VetFeesExcess_confidence"] = 0.0
    df["parse_status"] = "failed"

    for idx, text in enumerate(df[column]):
        limit, limit_conf = extract_claim_limit(text)
        excess, excess_conf = extract_excess(text)

        df.loc[idx, "ClaimLimit_gbp"] = limit
        df.loc[idx, "ClaimLimit_confidence"] = limit_conf
        df.loc[idx, "VetFeesExcessAmount"] = excess
        df.loc[idx, "VetFeesExcess_confidence"] = excess_conf
        df.loc[idx, "parse_status"] = classify_parse_status(
            text, limit, excess, limit_conf, excess_conf
        )

    return df
