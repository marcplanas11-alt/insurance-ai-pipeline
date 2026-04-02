# 🚀 Insurance AI Data Pipeline

## Objective
Transform unstructured insurance policy data into structured features for risk analysis and underwriting insights.

## Problem
Insurance datasets often contain unstructured text (e.g. coverage descriptions) that cannot be directly analysed.

## Solution
This project builds a Python pipeline to:
- Clean raw insurance data
- Classify policy coverage (limited vs unlimited)
- Extract coverage limits from text
- Convert unstructured data into structured variables

## Technologies
- Python (pandas)
- Regex (text parsing)
- Jupyter Notebook

## Business Impact
- Enables underwriting analysis
- Supports risk segmentation
- Reduces manual data processing

## Example Insight
Smokers or higher-risk profiles can be better analysed once coverage limits are structured.
## Author
Marc Planas — AI-Enabled Insurance Operations
## 📊 Example Output

| VetFees_type | Avg Limit (£) |
|-------------|--------------|
| no_limit    | Unlimited    |
| has_limit   | 4,500        |

## 💡 Key Insight

Policies with "no limit" coverage represent higher exposure and require different underwriting strategies compared to fixed-limit policies.

## 🚀 Business Use Case

This pipeline allows insurers or MGAs to:
- Standardize policy wording across providers
- Compare coverage levels consistently
- Identify high-risk policies automatically
## ✅ Validation

The pipeline is tested using pytest and automatically validated via GitHub Actions on each commit.
