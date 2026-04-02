"""
run_cleaner.py
Drop-and-run script for the bordereaux cleaner.
Place this in the repo root. Run with: python run_cleaner.py

Usage options:
  python run_cleaner.py                          # prompts you to enter a file path
  python run_cleaner.py data/my_bordereaux.csv   # pass file path directly
"""

import sys
import os
import pandas as pd
from datetime import datetime
from src.bordereaux_cleaner import clean_bordereaux

# ── Colour output for terminal ────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def main():
    # ── Get file path ─────────────────────────────────────────
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        print(f"\n{BOLD}Bordereaux Cleaner — Marc Planas Insurance AI Pipeline{RESET}")
        print("─" * 55)
        filepath = input("\nDrop your file path here (CSV or XLSX): ").strip().strip('"')

    if not os.path.exists(filepath):
        print(f"\n{RED}File not found: {filepath}{RESET}")
        sys.exit(1)

    print(f"\n{YELLOW}Loading {os.path.basename(filepath)}...{RESET}")

    # ── Load file ─────────────────────────────────────────────
    try:
        if filepath.endswith(".csv"):
            df_raw = pd.read_csv(filepath)
        elif filepath.endswith((".xlsx", ".xls")):
            df_raw = pd.read_excel(filepath)
        else:
            print(f"{RED}Unsupported format. Use .csv or .xlsx{RESET}")
            sys.exit(1)
    except Exception as e:
        print(f"{RED}Could not read file: {e}{RESET}")
        sys.exit(1)

    print(f"  Rows loaded:    {len(df_raw)}")
    print(f"  Columns found:  {list(df_raw.columns)[:6]}{'...' if len(df_raw.columns) > 6 else ''}")

    # ── Run cleaner ───────────────────────────────────────────
    print(f"\n{YELLOW}Running cleaning pipeline (10 steps)...{RESET}")
    df_clean, report, issues = clean_bordereaux(df_raw)

    # ── Print report ──────────────────────────────────────────
    print(f"\n{BOLD}{'─'*55}")
    print("  QUALITY REPORT")
    print(f"{'─'*55}{RESET}")
    print(f"  Total rows (clean):    {report['total_rows']}")
    print(f"  Total columns:         {report['total_columns']}")
    print(f"  Date errors flagged:   {report['date_errors']}")
    print(f"  Invalid currencies:    {report['invalid_currencies']}")

    if report.get("total_premium") is not None:
        print(f"  Total gross premium:   {report['total_premium']:,.2f}")
        print(f"  Average premium:       {report['avg_premium']:,.2f}")

    if report.get("currencies"):
        print(f"  Currencies found:      {report['currencies']}")

    if issues:
        print(f"\n{RED}  Structural issues:{RESET}")
        for issue in issues:
            print(f"    ⚠  {issue}")
    else:
        print(f"\n{GREEN}  No structural issues found.{RESET}")

    # ── Audit flags summary ───────────────────────────────────
    if "date_error" in df_clean.columns and df_clean["date_error"].sum() > 0:
        bad = df_clean[df_clean["date_error"]][["policy_number","inception_date","expiry_date"]]
        print(f"\n{RED}  Policies with date errors:{RESET}")
        print(bad.to_string(index=False))

    if "currency_valid" in df_clean.columns and (~df_clean["currency_valid"]).sum() > 0:
        bad = df_clean[~df_clean["currency_valid"]][["policy_number","currency"]]
        print(f"\n{RED}  Policies with invalid currency:{RESET}")
        print(bad.to_string(index=False))

    if "has_missing_required" in df_clean.columns and df_clean["has_missing_required"].sum() > 0:
        n = df_clean["has_missing_required"].sum()
        print(f"\n{YELLOW}  {n} row(s) have missing required fields — review before submission.{RESET}")

    # ── Save output ───────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    base      = os.path.splitext(os.path.basename(filepath))[0]
    out_dir   = os.path.dirname(filepath) or "."
    out_path  = os.path.join(out_dir, f"{base}_CLEAN_{timestamp}.xlsx")

    df_clean.to_excel(out_path, index=False)
    print(f"\n{GREEN}{BOLD}  Saved → {out_path}{RESET}")
    print(f"{'─'*55}\n")


if __name__ == "__main__":
    main()
