# Bordereaux Intake Validation and Exception Routing

## Purpose

This module adds an intake validation layer before the existing insurance policy parsing pipeline.

The existing pipeline focuses on transforming unstructured insurance policy wording into structured underwriting features. This intake layer checks whether incoming bordereaux records are complete, valid and safe to process before downstream parsing.

## Business Problem

Insurance bordereaux submitted by coverholders, MGAs or delegated authority partners often contain operational data quality issues.

Common issues include:

- Missing required fields
- Invalid inception dates
- Negative or invalid premium values
- Duplicate policy numbers
- Missing country or jurisdiction information
- Unsupported classes of business

If these issues are not detected early, they can create downstream problems in reporting, reconciliation, underwriting review, pricing analysis and compliance monitoring.

## Workflow Position

```text
Raw bordereaux CSV
    ↓
Intake validation
    ↓
Exception routing
    ↓
Existing cleaning / parsing pipeline
    ↓
Structured underwriting features
    ↓
SQL / analytics
