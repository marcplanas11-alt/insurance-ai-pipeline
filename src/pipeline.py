"""
pipeline.py
Main orchestration layer for the insurance policy parsing pipeline.
"""

import pandas as pd
from typing import Optional

from src.load import load_data, validate_required_columns
from src.clean import clean_vetfees_column, remove_null_vetfees
from src.parse import parse_vetfees
from src.llm import enrich_with_llm


class ParsePipeline:
    """
    End-to-end policy parsing pipeline.

    Flow:
        1. Load raw data
        2. Clean VetFees text
        3. Extract claim limits and excess via regex
        4. Assign parse_status classification
        5. Optionally enrich with LLM fallback
        6. Output structured dataset
    """

    def __init__(
        self,
        vetfees_column: str = "VetFees",
        use_llm: bool = False,
        llm_api_key: Optional[str] = None,
    ):
        self.vetfees_column = vetfees_column
        self.use_llm = use_llm
        self.llm_api_key = llm_api_key

    def run(self, filepath: str, output_filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Execute full pipeline on a bordereaux file.

        Args:
            filepath: Path to input CSV/XLSX
            output_filepath: Optional path to save processed data

        Returns:
            pd.DataFrame with all extracted fields
        """
        # Step 1: Load
        df = load_data(filepath)
        validate_required_columns(df, [self.vetfees_column])

        # Step 2: Clean
        df = clean_vetfees_column(df, column=self.vetfees_column)
        df = remove_null_vetfees(df, column=self.vetfees_column)

        # Step 3: Parse
        clean_col = f"{self.vetfees_column}_clean"
        df = parse_vetfees(df, column=clean_col)

        # Step 4: LLM enrichment (optional)
        if self.use_llm and self.llm_api_key:
            df = enrich_with_llm(
                df,
                text_column=clean_col,
                parse_status_column="parse_status",
                api_key=self.llm_api_key,
            )

        # Step 5: Save
        if output_filepath:
            df.to_csv(output_filepath, index=False)

        return df

    def run_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Execute pipeline on an already-loaded DataFrame.

        Args:
            df: Input DataFrame with VetFees column

        Returns:
            pd.DataFrame with extracted fields
        """
        df = df.copy()

        # Step 2: Clean
        df = clean_vetfees_column(df, column=self.vetfees_column)
        df = remove_null_vetfees(df, column=self.vetfees_column)

        # Step 3: Parse
        clean_col = f"{self.vetfees_column}_clean"
        df = parse_vetfees(df, column=clean_col)

        # Step 4: LLM enrichment (optional)
        if self.use_llm and self.llm_api_key:
            df = enrich_with_llm(
                df,
                text_column=clean_col,
                parse_status_column="parse_status",
                api_key=self.llm_api_key,
            )

        return df
