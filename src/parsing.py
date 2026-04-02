import re

def classify_vetfees(text):
    if "no limit" in text:
        return "no_limit"
    return "has_limit"

def extract_limit(text):
    if "no limit" in text:
        return None
    
    match = re.search(r'£([0-9,]+)', text)
    if match:
        return float(match.group(1).replace(",", ""))
    
    return None
