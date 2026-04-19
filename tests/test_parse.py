"""
test_parse.py
Unit tests for policy parsing extraction logic.
"""

import pytest
import pandas as pd
from src.parse import (
    extract_claim_limit,
    extract_excess,
    classify_parse_status,
    parse_vetfees,
)


class TestExtractClaimLimit:
    """Tests for claim limit extraction from text."""

    def test_extract_limit_with_pounds_keyword(self):
        text = "limit of £5,000 per condition"
        amount, conf = extract_claim_limit(text)
        assert amount == 5000.0
        assert conf > 0.9

    def test_extract_limit_with_coverage_keyword(self):
        text = "coverage: £10,000 per year"
        amount, conf = extract_claim_limit(text)
        assert amount == 10000.0
        assert conf > 0.9

    def test_extract_limit_with_max_keyword(self):
        text = "max: £2,500"
        amount, conf = extract_claim_limit(text)
        assert amount == 2500.0
        assert conf > 0.9

    def test_unlimited_coverage(self):
        text = "unlimited coverage for all conditions"
        amount, conf = extract_claim_limit(text)
        assert amount is None
        assert conf > 0.9

    def test_no_limit_coverage(self):
        text = "no limit on claims"
        amount, conf = extract_claim_limit(text)
        assert amount is None
        assert conf > 0.9

    def test_fully_covered(self):
        text = "fully covered - comprehensive protection"
        amount, conf = extract_claim_limit(text)
        assert amount is None
        assert conf > 0.9

    def test_no_amount_found(self):
        text = "coverage details unclear in policy wording"
        amount, conf = extract_claim_limit(text)
        assert amount is None
        assert conf == 0.0

    def test_empty_string(self):
        amount, conf = extract_claim_limit("")
        assert amount is None
        assert conf == 0.0

    def test_null_input(self):
        import pandas as pd
        amount, conf = extract_claim_limit(pd.NA)
        assert amount is None
        assert conf == 0.0

    def test_decimal_amount(self):
        text = "maximum limit £3,250.50 per incident"
        amount, conf = extract_claim_limit(text)
        assert amount == 3250.50
        assert conf > 0.9


class TestExtractExcess:
    """Tests for excess extraction from text."""

    def test_extract_excess_with_keyword(self):
        text = "excess: £250 per claim"
        amount, conf = extract_excess(text)
        assert amount == 250.0
        assert conf > 0.9

    def test_extract_excess_with_space(self):
        text = "excess £500"
        amount, conf = extract_excess(text)
        assert amount == 500.0
        assert conf > 0.9

    def test_excess_with_commas(self):
        text = "excess amount: £1,200 per claim"
        amount, conf = extract_excess(text)
        assert amount == 1200.0
        assert conf > 0.9

    def test_no_excess_found(self):
        text = "no excess, claims paid in full"
        amount, conf = extract_excess(text)
        assert amount is None
        assert conf == 0.0

    def test_empty_string(self):
        amount, conf = extract_excess("")
        assert amount is None
        assert conf == 0.0

    def test_null_input(self):
        import pandas as pd
        amount, conf = extract_excess(pd.NA)
        assert amount is None
        assert conf == 0.0


class TestClassifyParseStatus:
    """Tests for parse_status classification logic."""

    def test_both_fields_extracted(self):
        status = classify_parse_status(
            "limit £5000 excess £250",
            claim_limit=5000.0,
            excess=250.0,
            claim_confidence=0.95,
            excess_confidence=0.95,
        )
        assert status == "parsed"

    def test_only_limit_extracted(self):
        status = classify_parse_status(
            "limit £5000",
            claim_limit=5000.0,
            excess=None,
            claim_confidence=0.95,
            excess_confidence=0.0,
        )
        assert status == "partial"

    def test_only_excess_extracted(self):
        status = classify_parse_status(
            "excess £250",
            claim_limit=None,
            excess=250.0,
            claim_confidence=0.0,
            excess_confidence=0.95,
        )
        assert status == "partial"

    def test_low_confidence_fields(self):
        status = classify_parse_status(
            "maybe coverage around 5000",
            claim_limit=5000.0,
            excess=None,
            claim_confidence=0.5,
            excess_confidence=0.0,
        )
        assert status == "ambiguous"

    def test_no_fields_found(self):
        status = classify_parse_status(
            "policy wording unclear",
            claim_limit=None,
            excess=None,
            claim_confidence=0.0,
            excess_confidence=0.0,
        )
        assert status == "failed"

    def test_empty_text(self):
        status = classify_parse_status(
            "",
            claim_limit=None,
            excess=None,
            claim_confidence=0.0,
            excess_confidence=0.0,
        )
        assert status == "failed"


class TestParseVetfeesDataFrame:
    """Integration tests for full parsing on DataFrames."""

    def test_parse_single_row(self):
        df = pd.DataFrame({
            "policy_id": [1],
            "VetFees_clean": ["limit of £5,000 excess £250"],
        })
        result = parse_vetfees(df, column="VetFees_clean")

        assert result["ClaimLimit_gbp"].iloc[0] == 5000.0
        assert result["VetFeesExcessAmount"].iloc[0] == 250.0
        assert result["parse_status"].iloc[0] == "parsed"

    def test_parse_multiple_rows(self):
        df = pd.DataFrame({
            "policy_id": [1, 2, 3],
            "VetFees_clean": [
                "limit of £5,000 excess £250",
                "limit of £10,000",
                "coverage unclear",
            ],
        })
        result = parse_vetfees(df, column="VetFees_clean")

        assert len(result) == 3
        assert result["parse_status"].tolist() == ["parsed", "partial", "failed"]

    def test_missing_column_raises_error(self):
        df = pd.DataFrame({"policy_id": [1]})
        with pytest.raises(ValueError):
            parse_vetfees(df, column="VetFees_clean")

    def test_null_values_handled(self):
        df = pd.DataFrame({
            "policy_id": [1, 2],
            "VetFees_clean": ["limit £5000", None],
        })
        result = parse_vetfees(df, column="VetFees_clean")

        assert result["ClaimLimit_gbp"].iloc[0] == 5000.0
        assert pd.isna(result["ClaimLimit_gbp"].iloc[1])
        assert result["parse_status"].iloc[1] == "failed"
