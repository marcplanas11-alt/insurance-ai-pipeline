# Quick Start (5 minutes)

## 1. Install

```bash
git clone https://github.com/marcplanas11-alt/insurance-ai-pipeline.git
cd insurance-ai-pipeline
pip install -r requirements.txt
```

## 2. Test with Sample Data

```bash
python run_cleaner.py data/raw/sample_bordereaux.csv
```

You'll see:
- Quality report in the terminal
- Output Excel file: `data/raw/sample_bordereaux_CLEAN_<timestamp>.xlsx`

## 3. Process Your Own Data

Place your CSV/Excel in `data/raw/` and run:

```bash
python run_cleaner.py data/raw/your_file.csv
```

**Required columns in your data:**
- `policy_number`
- `insured_name`
- `inception_date`
- `expiry_date`
- `gross_premium`
- `currency`
- `VetFees` (or your custom column name)

## 4. Parse Insurance Details

Create `parse_data.py`:

```python
from src.pipeline import ParsePipeline

pipeline = ParsePipeline(vetfees_column="VetFees")
df = pipeline.run("data/raw/sample_bordereaux.csv", "data/processed/output.csv")

print(df[["policy_number", "ClaimLimit_gbp", "VetFeesExcessAmount", "parse_status"]])
```

Run:
```bash
python parse_data.py
```

Output includes:
- `ClaimLimit_gbp` — Extracted claim limit
- `VetFeesExcessAmount` — Extracted excess
- `parse_status` — Quality: `parsed`, `partial`, `ambiguous`, or `failed`

## 5. Verify Installation

```bash
pytest tests/
```

Should show: `62 passed`

---

For full documentation, see [SETUP.md](SETUP.md) or [README.md](README.md).
