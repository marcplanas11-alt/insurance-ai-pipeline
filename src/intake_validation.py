import os
import sys
from datetime import datetime
from typing import List, Set

import pandas as pd

from src.exception_routing import route_exception, requires_review


REQUIRED_FIELDS = [
    "policy_number",
    "insured_name",
    "inception_date",
    "premium",
    "country",
    "class_of_business",
    "coverholder",
]

ALLOWED_CLASSES_OF_BUSINESS = {
    "Marine",
    "Property",
    "Liability",
    "Cyber",
    "Motor",
}


def is_valid_date(value: str) -> bool:
    """
    Checks whether a value follows the YYYY-MM-DD date format.
    """
    try:
        datetime.strptime(str(value), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def get_duplicated_policy_numbers(df: pd.DataFrame) -> Set[str]:
    """
    Returns policy numbers that appear more than once in the bordereaux.
    """
    if "policy_number" not in df.columns:
        return set()

    duplicated = df[df.duplicated(subset=["policy_number"], keep=False)]
    return set(duplicated["policy_number"].astype(str))


def validate_required_columns(df: pd.DataFrame) -> List[str]:
    """
    Checks whether the input file contains all mandatory columns.
    """
    return [field for field in REQUIRED_FIELDS if field not in df.columns]


def validate_row(row: pd.Series, duplicated_policy_numbers: Set[str]) -> List[str]:
    """
    Applies intake validation rules to one bordereaux row.

    Returns a list of error codes.
    """
    errors = []

    for field in REQUIRED_FIELDS:
        if pd.isna(row[field]) or str(row[field]).strip() == "":
            errors.append("missing_required_field")

    if pd.isna(row["country"]) or str(row["country"]).strip() == "":
        errors.append("missing_country")

    if not is_valid_date(row["inception_date"]):
        errors.append("invalid_inception_date")

    try:
        premium = float(row["premium"])
        if premium <= 0:
            errors.append("negative_premium")
    except (ValueError, TypeError):
        errors.append("invalid_premium")

    if row["class_of_business"] not in ALLOWED_CLASSES_OF_BUSINESS:
        errors.append("invalid_class_of_business")

    if str(row["policy_number"]) in duplicated_policy_numbers:
        errors.append("duplicate_policy_number")

    return sorted(set(errors))


def validate_bordereaux_file(input_filepath: str, output_filepath: str) -> pd.DataFrame:
    """
    Runs intake validation against a bordereaux CSV file and writes a validation report.
    """
    if not os.path.exists(input_filepath):
        raise FileNotFoundError(f"Input file not found: {input_filepath}")

    df = pd.read_csv(input_filepath)

    missing_columns = validate_required_columns(df)
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    duplicated_policy_numbers = get_duplicated_policy_numbers(df)

    validation_results = []

    for _, row in df.iterrows():
        errors = validate_row(row, duplicated_policy_numbers)
        routing_queue = route_exception(errors)

        validation_results.append(
            {
                "policy_number": row["policy_number"],
                "insured_name": row["insured_name"],
                "validation_status": "passed" if not errors else "failed",
                "validation_errors": "; ".join(errors),
                "routing_queue": routing_queue,
                "review_required": requires_review(routing_queue),
            }
        )

    report = pd.DataFrame(validation_results)

    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    report.to_csv(output_filepath, index=False)

    return report


def main() -> None:
    """
    CLI entry point for local execution.
    """
    input_filepath = "input/sample_bordereaux_intake.csv"
    output_filepath = "outputs/validation_report_sample.csv"

    try:
        report = validate_bordereaux_file(input_filepath, output_filepath)
    except Exception as exc:
        print(f"Intake validation failed: {exc}")
        sys.exit(1)

    print(f"Validation completed. Report generated: {output_filepath}")
    print(report)


if __name__ == "__main__":
    main()