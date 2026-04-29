from src.parse import extract_claim_limit

def test_extract_limit():
    """Legacy test - now using extract_claim_limit from parse.py"""
    # Pattern with keyword: high confidence
    amount, conf = extract_claim_limit("limit of £2,000 per condition")
    assert amount == 2000
    assert conf >= 0.95

    # Unlimited keyword: high confidence
    amount, conf = extract_claim_limit("no limit")
    assert amount is None
    assert conf >= 0.95
