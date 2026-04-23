"""
app.py
FastAPI web interface for the Insurance AI Pipeline.
Serves three modules: VetFees Parser, Bordereaux Cleaner, SQL Analytics.
"""

import io
import os
import re
import sys
import uuid
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

sys.path.insert(0, str(Path(__file__).parent))

from src.bordereaux_cleaner import clean_bordereaux
from src.pipeline import ParsePipeline

app = FastAPI(title="Insurance AI Pipeline", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory job store: job_id → temp file path
_jobs: dict[str, str] = {}


def _read_upload(file_bytes: bytes, filename: str) -> pd.DataFrame:
    if filename.endswith(".csv"):
        return pd.read_csv(io.BytesIO(file_bytes))
    elif filename.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(file_bytes))
    raise HTTPException(status_code=400, detail="Unsupported file type. Use .csv or .xlsx")


def _save_job(df: pd.DataFrame, label: str) -> str:
    job_id = str(uuid.uuid4())
    path = f"/tmp/{job_id}_{label}.xlsx"
    df_out = df.copy()
    for col in df_out.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns:
        df_out[col] = df_out[col].dt.strftime("%Y-%m-%d")
    df_out.to_excel(path, index=False)
    _jobs[job_id] = path
    return job_id


# ─────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/vetfees/parse")
async def parse_vetfees(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        df = _read_upload(contents, file.filename)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read file: {exc}")

    try:
        pipeline = ParsePipeline()
        result = pipeline.run_dataframe(df)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Pipeline error: {exc}")

    job_id = _save_job(result, "vetfees_parsed")

    status_counts = {}
    if "parse_status" in result.columns:
        status_counts = result["parse_status"].value_counts().to_dict()

    avg_limit_conf = (
        round(float(result["claim_limit_confidence"].mean()), 3)
        if "claim_limit_confidence" in result.columns else None
    )
    avg_excess_conf = (
        round(float(result["excess_confidence"].mean()), 3)
        if "excess_confidence" in result.columns else None
    )

    priority_cols = [
        "VetFees", "VetFees_clean", "ClaimLimit_gbp",
        "VetFeesExcessAmount", "parse_status",
        "claim_limit_confidence", "excess_confidence",
    ]
    preview_cols = [c for c in priority_cols if c in result.columns]
    preview_df = result[preview_cols].head(200).fillna("")

    return {
        "job_id": job_id,
        "total_rows": len(result),
        "status_counts": status_counts,
        "avg_limit_confidence": avg_limit_conf,
        "avg_excess_confidence": avg_excess_conf,
        "preview_columns": preview_cols,
        "preview": preview_df.to_dict(orient="records"),
    }


@app.post("/api/bordereaux/clean")
async def clean_bordereaux_api(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        df = _read_upload(contents, file.filename)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read file: {exc}")

    try:
        cleaned_df, report, issues = clean_bordereaux(df)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Cleaning error: {exc}")

    job_id = _save_job(cleaned_df, "bordereaux_cleaned")

    preview_cols = list(cleaned_df.columns[:14])
    preview_df = cleaned_df[preview_cols].head(200).copy()
    for col in preview_df.select_dtypes(include=["datetime64[ns]"]).columns:
        preview_df[col] = preview_df[col].dt.strftime("%Y-%m-%d")

    # Ensure report values are JSON-serialisable
    serialisable_report = {}
    for k, v in report.items():
        if isinstance(v, float) and (v != v):  # NaN check
            serialisable_report[k] = None
        else:
            serialisable_report[k] = v

    return {
        "job_id": job_id,
        "report": serialisable_report,
        "issues": issues,
        "total_rows": len(cleaned_df),
        "all_columns": list(cleaned_df.columns),
        "preview_columns": preview_cols,
        "preview": preview_df.fillna("").to_dict(orient="records"),
    }


@app.get("/api/analytics/queries")
async def get_analytics_queries():
    sql_path = Path(__file__).parent / "sql" / "analysis.sql"
    sql_text = sql_path.read_text()

    meta = [
        ("Coverage vs Premium Analysis",
         "Segments policies by claim limit tier and surfaces premium distribution per tier."),
        ("Parse Quality Segmentation",
         "Shows distribution of parsing outcomes (parsed / partial / ambiguous / failed) with business metrics."),
        ("Excess Distribution — Window Functions",
         "Ranks policies by excess amount within coverage tiers using RANK() and CUME_DIST()."),
        ("Risk Segmentation — NTILE Quartiles",
         "Classifies policies into four risk quartiles using NTILE(4) based on premium × coverage exposure."),
        ("Confidence Quality Audit",
         "Identifies low-confidence extractions (< 0.70) that are candidates for LLM enrichment review."),
        ("Premium Efficiency by Coverage Level",
         "Calculates premium cost per £1,000 of coverage for each coverage bracket."),
    ]

    raw_blocks = re.findall(
        r"(SELECT[\s\S]+?)(?=\n\n\n--|$)", sql_text
    )

    queries = []
    for i, (title, desc) in enumerate(meta):
        queries.append({
            "id": i + 1,
            "title": title,
            "description": desc,
            "sql": raw_blocks[i].strip() if i < len(raw_blocks) else "",
        })

    return {"queries": queries}


@app.get("/api/download/{job_id}")
async def download_file(job_id: str):
    path = _jobs.get(job_id)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Job not found or file has expired")
    filename = os.path.basename(path)
    return FileResponse(
        path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
