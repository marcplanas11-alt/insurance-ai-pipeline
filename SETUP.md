# Setup Guide for Business Users

This document walks business users through setting up and using the Insurance AI Pipeline.

## Prerequisites

- **Python 3.9+** installed on your machine ([download here](https://www.python.org/downloads/))
- **Git** installed ([download here](https://git-scm.com/))
- A text editor or IDE (VS Code, PyCharm, etc.) — optional but recommended

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/marcplanas11-alt/insurance-ai-pipeline.git
cd insurance-ai-pipeline
```

### Step 2: Create a Virtual Environment (Recommended)

A virtual environment isolates project dependencies and prevents conflicts with other Python projects.

```bash
# On macOS/Linux:
python3 -m venv venv
source venv/bin/activate

# On Windows:
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt when activated.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- **pandas** — Data manipulation
- **openpyxl** — Excel file support
- **pytest** — Testing framework
- **anthropic** — LLM API (for optional AI-powered enrichment)

## Quick Start

### 1. Prepare Your Data

Place your bordereaux CSV or Excel file in `data/raw/`:

```
insurance-ai-pipeline/
└── data/
    └── raw/
        └── your_bordereaux.csv
```

### 2. Run the Pipeline

#### Option A: Using `run_cleaner.py` (Recommended for Quick Testing)

```bash
python run_cleaner.py data/raw/your_bordereaux.csv
```

**Output:**
- Quality report printed to terminal
- Cleaned Excel file saved as `data/raw/your_bordereaux_CLEAN_<timestamp>.xlsx`

#### Option B: Using Python Script

Create a file called `process_data.py`:

```python
from src.pipeline import ParsePipeline

# Initialize pipeline
pipeline = ParsePipeline(vetfees_column="VetFees", use_llm=False)

# Run on your data
df_output = pipeline.run(
    filepath="data/raw/your_bordereaux.csv",
    output_filepath="data/processed/your_bordereaux_parsed.csv"
)

print(f"Processed {len(df_output)} rows")
print(df_output[["policy_number", "ClaimLimit_gbp", "VetFeesExcessAmount", "parse_status"]])
```

Run it:

```bash
python process_data.py
```

### 3. Review Results

Processed data is saved to `data/processed/` with extracted fields:

| Column | Description |
|--------|-------------|
| `policy_number` | Original policy identifier |
| `ClaimLimit_gbp` | Extracted claim limit (GBP) |
| `VetFeesExcessAmount` | Extracted excess/deductible |
| `parse_status` | Quality indicator: `parsed`, `partial`, `ambiguous`, `failed` |
| `ClaimLimit_confidence` | Confidence score (0-1) |
| `VetFeesExcess_confidence` | Confidence score (0-1) |

## Testing

Run the full test suite to verify everything works:

```bash
pytest tests/ -v
```

**Expected output:**
```
============================== 62 passed in 0.94s ==============================
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'src'"

**Solution:** Make sure you're running commands from the repo root directory and have activated the virtual environment.

```bash
cd insurance-ai-pipeline
source venv/bin/activate  # or: venv\Scripts\activate on Windows
```

### "requirements not satisfied"

**Solution:** Upgrade pip and reinstall:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Data not processing

**Solution:** Check that:
1. Your CSV/Excel has required columns: `policy_number`, `insured_name`, `inception_date`, `expiry_date`, `gross_premium`, `currency`
2. The VetFees column name matches (default is `VetFees`, but you can customize it)
3. File is in `data/raw/` or specify the full path

## Advanced Usage

### Using LLM Enrichment

For ambiguous extractions, enable Claude API:

```python
import os
from src.pipeline import ParsePipeline

# Set your API key in environment:
api_key = os.environ.get("ANTHROPIC_API_KEY")

# Initialize with LLM
pipeline = ParsePipeline(
    vetfees_column="VetFees",
    use_llm=True,
    llm_api_key=api_key
)

# Run pipeline (ambiguous cases will be enriched via LLM)
df = pipeline.run(
    filepath="data/raw/input.csv",
    output_filepath="data/processed/output.csv"
)

print(f"Parse status distribution:\n{df['parse_status'].value_counts()}")
```

To get an API key:
1. Visit [Anthropic Console](https://console.anthropic.com)
2. Create an account and generate an API key
3. Set environment variable: `export ANTHROPIC_API_KEY=your_key_here`

### Customizing Column Names

If your bordereaux uses different column names:

```python
from src.pipeline import ParsePipeline

pipeline = ParsePipeline(vetfees_column="My_Coverage_Notes")  # Use your column name
df = pipeline.run_dataframe(df)
```

### SQL Analysis

After running the pipeline, load the output into your database and run `sql/analysis.sql` for advanced analytics:

- Coverage vs. premium relationships
- Parse quality distribution
- Risk segmentation (quartiles)
- Confidence audit for low-quality extractions

## File Structure

```
insurance-ai-pipeline/
├── data/
│   ├── raw/                      # Your input bordereaux files
│   ├── processed/                # Pipeline output (parsed data)
├── src/
│   ├── __init__.py               # Package initialization
│   ├── bordereaux_cleaner.py     # Data cleaning & validation
│   ├── clean.py                  # Text normalization
│   ├── parse.py                  # Regex extraction & classification
│   ├── llm.py                    # LLM fallback (optional)
│   ├── pipeline.py               # Main orchestration
├── tests/
│   ├── test_bordereaux.py        # Cleaner tests
│   ├── test_parse.py             # Parser tests
├── sql/
│   ├── analysis.sql              # Analytics queries
├── README.md                      # Project overview
├── SETUP.md                       # This file
├── requirements.txt               # Python dependencies
├── run_cleaner.py                # Quick-start script
├── conftest.py                   # pytest configuration
```

## Getting Help

- **README.md** — Full project documentation
- **Test files** — See `tests/` for usage examples
- **Source code comments** — Each module has inline documentation

## Next Steps

1. ✅ Installed dependencies
2. ✅ Ran the pipeline on sample data
3. 📝 Review parsed output in `data/processed/`
4. 🔧 Customize regex patterns in `src/parse.py` if needed
5. 🚀 Deploy to your data warehouse

---

**Questions?** Check the README.md or review the test files for usage examples.
