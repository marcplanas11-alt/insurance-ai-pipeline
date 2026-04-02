from src.parsing import extract_limit

def test_extract_limit():
    assert extract_limit("£2,000 per condition") == 2000
    assert extract_limit("no limit") is None
