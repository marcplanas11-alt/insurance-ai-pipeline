import pandas as pd

from src.intake_validation import (
    get_duplicated_policy_numbers,
    is_valid_date,
    validate_required_columns,
    validate_row,
)
from src.exception_routing import route_exception, requires_review


def test_is_valid_date_accepts_valid_date():
    assert is_valid_date("2026-01-01") is True


def test_is_valid_date_rejects_invalid_date():
    assert is_valid_date("invalid-date") is False


def test_get_duplicated_policy_numbers_detects_duplicates():
    df = pd.DataFrame({"policy_number": ["POL-001", "POL-002", "POL-002"]})
    assert get_duplicated_policy_numbers(df) == {"POL-002"}


def test_validate_required_columns_detects_missing_columns():
    df = pd.DataFrame({"policy_number": ["POL-001"], "insured_name": ["Alpha Ltd"]})

    missing_columns = validate_required_columns(df)

    assert "premium" in missing_columns
    assert "country" in missing_columns
    assert "class_of_business" in missing_columns


def test_validate_row_detects_negative_premium():
    row = pd.Series(
        {
            "policy_number": "POL-001",
            "insured_name": "Alpha Ltd",
            "inception_date": "2026-01-01",
            "premium": -1000,
            "country": "UK",
            "class_of_business": "Marine",
            "coverholder": "London Coverholder A",
        }
    )

    errors = validate_row(row, duplicated_policy_numbers=set())

    assert "negative_premium" in errors


def test_validate_row_detects_invalid_class_of_business():
    row = pd.Series(
        {
            "policy_number": "POL-001",
            "insured_name": "Alpha Ltd",
            "inception_date": "2026-01-01",
            "premium": 1000,
            "country": "UK",
            "class_of_business": "Aviation",
            "coverholder": "London Coverholder A",
        }
    )

    errors = validate_row(row, duplicated_policy_numbers=set())

    assert "invalid_class_of_business" in errors


def test_route_exception_sends_negative_premium_to_finance():
    assert route_exception(["negative_premium"]) == "finance_review"


def test_route_exception_sends_invalid_class_to_underwriting():
    assert route_exception(["invalid_class_of_business"]) == "underwriting_review"


def test_route_exception_accepts_clean_record():
    assert route_exception([]) == "accepted"


def test_requires_review_false_for_accepted():
    assert requires_review("accepted") is False


def test_requires_review_true_for_exception_queue():
    assert requires_review("data_quality_issue") is True