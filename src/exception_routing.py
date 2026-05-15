from typing import List


def route_exception(errors: List[str]) -> str:
    """
    Routes bordereaux records to the appropriate operational review queue
    based on validation errors.

    This module does not validate data. It only decides the operational queue.
    """
    if not errors:
        return "accepted"

    if "negative_premium" in errors or "invalid_premium" in errors:
        return "finance_review"

    if "invalid_class_of_business" in errors:
        return "underwriting_review"

    if (
        "missing_required_field" in errors
        or "missing_country" in errors
        or "invalid_inception_date" in errors
        or "duplicate_policy_number" in errors
    ):
        return "data_quality_issue"

    return "manual_review"


def requires_review(routing_queue: str) -> bool:
    """
    Returns True when a row needs human review before downstream processing.
    """
    return routing_queue != "accepted"