"""
llm.py
LLM-based fallback parsing for ambiguous or failed extractions.
Currently a placeholder. Can be integrated with Claude API or other LLM.

Migration note (May 2026):
When implementing Claude integration, use claude-sonnet-4-6 or claude-opus-4-7.
The 1M context window is now generally available (not beta) on these models.
No longer use context-1m-2025-08-07 header—it has been retired.
"""

import pandas as pd


def enrich_with_llm(
    df: pd.DataFrame,
    text_column: str = "VetFees_clean",
    parse_status_column: str = "parse_status",
    api_key: str | None = None,
) -> pd.DataFrame:
    """
    Use LLM to re-parse rows where parse_status is 'ambiguous' or 'failed'.

    PLACEHOLDER: Currently returns input unchanged.
    To enable, integrate with Anthropic Claude, OpenAI, or similar.

    Args:
        df: DataFrame with parsed fields
        text_column: Column containing cleaned text
        parse_status_column: Column with parse_status classification
        api_key: API key for LLM service

    Returns:
        DataFrame with LLM-enriched fields (if enabled)
    """
    if not api_key:
        return df

    df = df.copy()

    # Filter rows needing LLM enrichment
    needs_llm = df[parse_status_column].isin(["ambiguous", "failed"])
    if not needs_llm.any():
        return df

    # TODO: Implement LLM call
    # For each row in needs_llm:
    #   - Extract claim limit via LLM
    #   - Extract excess via LLM
    #   - Update ClaimLimit_gbp, VetFeesExcessAmount
    #   - Update parse_status to "llm_parsed"

    return df


def batch_llm_parse(texts: list[str], api_key: str | None = None) -> list[dict]:
    """
    Batch LLM parsing for multiple texts.

    Args:
        texts: List of cleaned VetFees texts
        api_key: API key for LLM service

    Returns:
        List of dicts with extracted fields (placeholder)
    """
    if not api_key:
        return [{"claim_limit": None, "excess": None}] * len(texts)

    results = []
    for text in texts:
        # TODO: Implement LLM call
        results.append({"claim_limit": None, "excess": None, "source": "llm"})

    return results
