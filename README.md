# Insurance AI Pipeline

Portfolio project for insurance data operations: bordereaux intake validation, exception routing, VetFees parsing, bordereaux cleaning and a FastAPI browser interface.

> **Positioning:** this is a local portfolio prototype. It demonstrates deterministic insurance operations logic, validation rules, exception routing, test coverage and a browser-based demo. It is not a live production carrier deployment.

---

## Executive Summary

Insurance bordereaux and policy data often arrive with inconsistent columns, missing mandatory values, duplicate policy numbers, invalid dates, malformed premiums and unclear wording.

This repository shows how those operational problems can be converted into a structured Python workflow:

```text
Raw CSV / Excel input
   ↓
Data loading and cleaning
   ↓
Validation rules
   ↓
Exception routing
   ↓
Output report / downloadable Excel
   ↓
Human review
```

The project demonstrates practical Business Analyst and insurance operations value:

* clear validation rules;
* repeatable local execution;
* automated exception routing;
* testable Python logic;
* sample outputs for interview demonstration;
* FastAPI browser interface for file upload and result download.

The workflow does not make underwriting, legal, finance or compliance decisions automatically. It supports human review by surfacing issues earlier and routing them to the right operational queue.

---

## What This Repo Demonstrates

* Bordereaux data quality validation.
* Exception routing for insurance operations.
* VetFees wording parsing.
* CSV / Excel processing.
* FastAPI browser interface.
* SQL analytics examples.
* Unit testing with pytest.
* Portfolio-ready framing for insurance BA / AI-enabled operations roles.

---

## Architecture

```text
Input files
   ↓
src/load.py
   ↓
src/clean.py / src/bordereaux_cleaner.py
   ↓
src/parse.py / src/intake_validation.py
   ↓
src/exception_routing.py
   ↓
outputs/
   ↓
FastAPI browser UI
```

---

## Main Files

| File / Folder                     | Purpose                                                                          |
| --------------------------------- | -------------------------------------------------------------------------------- |
| `app.py`                          | FastAPI web interface for uploads, processing and downloads                      |
| `src/intake_validation.py`        | Validates sample bordereaux intake records and writes a validation report        |
| `src/exception_routing.py`        | Routes failed records to operational queues                                      |
| `src/bordereaux_cleaner.py`       | Cleans bordereaux files and validates dates, premiums, currencies and duplicates |
| `src/pipeline.py`                 | Orchestrates the VetFees parsing pipeline                                        |
| `src/load.py`                     | Loads CSV / Excel input files                                                    |
| `src/clean.py`                    | Cleans VetFees wording before parsing                                            |
| `src/parse.py`                    | Extracts claim limits, excess values and parse status                            |
| `src/llm.py`                      | Optional LLM enrichment layer for ambiguous records                              |
| `tests/test_intake_validation.py` | Unit tests for validation and routing logic                                      |
| `input/`                          | Synthetic sample input files                                                     |
| `outputs/`                        | Generated validation reports                                                     |
| `templates/index.html`            | HTML template used by FastAPI                                                    |
| `static/`                         | Front-end assets                                                                 |
| `sql/analysis.sql`                | SQL analysis examples                                                            |
| `requirements.txt`                | Python dependencies                                                              |

---

## Validation Checks

The intake validation layer checks for:

* missing mandatory columns;
* missing required row-level values;
* missing country;
* invalid inception date;
* invalid or negative premium;
* invalid class of business;
* duplicate policy number.

---

## Exception Routing Logic

| Queue                 | Meaning                                                                   |
| --------------------- | ------------------------------------------------------------------------- |
| `accepted`            | Clean record, no review needed                                            |
| `finance_review`      | Premium issue, negative premium or invalid premium                        |
| `underwriting_review` | Invalid class of business                                                 |
| `data_quality_issue`  | Missing fields, missing country, invalid dates or duplicate policy number |
| `manual_review`       | Fallback queue for unclassified issues                                    |

---

## Full Setup and Execution Guide

Use this section when cloning the repository from GitHub and running it locally from zero.

### 1. Clone the repository

```bash
git clone https://github.com/marcplanas11-alt/insurance-ai-pipeline.git
cd insurance-ai-pipeline
```

---

### 2. Create a virtual environment

#### Windows CMD / PowerShell

```bash
python -m venv .venv
```

#### macOS / Linux

```bash
python3 -m venv .venv
```

---

### 3. Activate the virtual environment

#### Windows CMD

```bash
.venv\Scripts\activate
```

#### Windows PowerShell

```bash
.venv\Scripts\Activate.ps1
```

#### macOS / Linux

```bash
source .venv/bin/activate
```

---

### 4. Upgrade pip

```bash
python -m pip install --upgrade pip
```

---

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Run the Intake Validation CLI

Run the sample validation flow:

```bash
python -m src.intake_validation
```

Expected result:

```text
Validation completed. Report generated: outputs/validation_report_sample.csv
```

The output report contains:

* policy number;
* insured name;
* validation status;
* validation errors;
* routing queue;
* review required flag.

---

## Run Tests

```bash
python -m pytest tests/test_intake_validation.py
```

Expected result:

```text
all tests passed
```

---

## Run the FastAPI Browser Interface

Start the local server:

```bash
python -m uvicorn app:app --reload
```

Expected output:

```text
Uvicorn running on http://127.0.0.1:8000
```

Open in your browser:

```text
http://127.0.0.1:8000
```

The browser interface supports:

* VetFees parser upload;
* bordereaux cleaner upload;
* SQL analytics query viewing;
* Excel download of processed outputs.

---

## Complete Command Formula

### Windows CMD

```bash
git clone https://github.com/marcplanas11-alt/insurance-ai-pipeline.git
cd insurance-ai-pipeline
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m src.intake_validation
python -m pytest tests/test_intake_validation.py
python -m uvicorn app:app --reload
```

### Windows PowerShell

```bash
git clone https://github.com/marcplanas11-alt/insurance-ai-pipeline.git
cd insurance-ai-pipeline
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m src.intake_validation
python -m pytest tests/test_intake_validation.py
python -m uvicorn app:app --reload
```

### macOS / Linux

```bash
git clone https://github.com/marcplanas11-alt/insurance-ai-pipeline.git
cd insurance-ai-pipeline
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m src.intake_validation
python -m pytest tests/test_intake_validation.py
python -m uvicorn app:app --reload
```

---

## Troubleshooting

### `Input file not found`

You are probably running the command from the wrong folder.

Correct:

```bash
cd insurance-ai-pipeline
python -m src.intake_validation
```

---

### `uvicorn` is not recognized

Use:

```bash
python -m uvicorn app:app --reload
```

---

### Missing Python package

Run:

```bash
pip install -r requirements.txt
```

---

### Browser opens but upload fails

Check that the uploaded file is CSV, XLSX or XLS and that the expected columns are present.

---

## Cleanup Notes

* Keep only synthetic/sample files in the repository.
* Do not commit real bordereaux, policyholder data or client information.
* `outputs/` should contain demo reports only.
* This project is suitable for portfolio demonstration, not production use.

---

## Author

Built by Marc Planas Callico — Insurance Operations, Business Analysis and AI-enabled transformation.
