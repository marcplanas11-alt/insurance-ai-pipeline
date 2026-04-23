"""
Bordereaux Cleaner — Web Interface
Streamlit app for cleaning and parsing insurance bordereaux files.
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime

from src.bordereaux_cleaner import clean_bordereaux
from src.clean import clean_vetfees_column, remove_null_vetfees
from src.parse import parse_vetfees

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Bordereaux Cleaner",
    page_icon="📋",
    layout="wide",
)

# ── Styles ────────────────────────────────────────────────────
st.markdown("""
<style>
  .metric-card {
    background: #1a2744;
    color: white;
    padding: 18px;
    border-radius: 8px;
    text-align: center;
  }
  .metric-card .value { font-size: 32px; font-weight: bold; }
  .metric-card .label { font-size: 12px; color: #ccc; margin-top: 4px; }
  .status-parsed    { background:#16a34a; color:white; padding:3px 10px; border-radius:12px; font-size:12px; }
  .status-partial   { background:#2563eb; color:white; padding:3px 10px; border-radius:12px; font-size:12px; }
  .status-ambiguous { background:#d97706; color:white; padding:3px 10px; border-radius:12px; font-size:12px; }
  .status-failed    { background:#dc2626; color:white; padding:3px 10px; border-radius:12px; font-size:12px; }
  .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    return buf.getvalue()


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


# ── Header ────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 8])
with col_title:
    st.markdown("## 📋 Bordereaux Cleaner")
    st.caption("Upload a raw insurance bordereaux (CSV or XLSX) to clean, validate and parse VetFees wording.")

st.divider()

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Options")
    parse_vetfees_col = st.toggle("Parse VetFees column", value=True,
                                  help="Extract claim limits and excess from unstructured text")
    vetfees_col_name = st.text_input("VetFees column name", value="VetFees",
                                     help="Exact column name in your file")
    min_match_score = st.slider("Min parse confidence (%)", 0, 100, 70,
                                help="Flag extractions below this confidence threshold")
    st.divider()
    st.markdown("### 📥 Sample Data")
    if st.button("Load sample bordereaux"):
        sample = pd.DataFrame({
            "Policy Number":      ["POL001","POL001","POL003","POL004","POL005","POL006","POL007","POL008","POL009"],
            "Insured Name":       ["Acme Pet Ltd","Acme Pet Ltd","Beta Animal Care","Gamma Vets SA","Delta Paws","Epsilon Dogs","Zeta Cats","Eta Reptiles","Theta Birds"],
            "Inception Date":     ["01/01/2025","01/01/2025","15/03/2025","2025-06-01","01/09/2025","01/01/2025","01/02/2025","01/03/2025","01/04/2025"],
            "Expiry Date":        ["01/01/2026","01/01/2026","14/03/2025","2026-06-01","01/09/2026","01/01/2026","01/02/2026","01/03/2026","01/04/2026"],
            "Gross Premium":      ["£1,200.00","£1,200.00","€850.50","(500.00)","3400","£2,100.00","£875.50","£650.00","£1,800.00"],
            "Currency":           ["GBP","GBP","eur","PESO","USD","GBP","GBP","GBP","GBP"],
            "VetFees":            [
                "limit of £5,000 per condition excess £250",
                "limit of £5,000 per condition excess £250",
                "maximum cover £10,000 annual excess £500",
                "unlimited coverage for all conditions",
                "coverage £2,500 no excess",
                "limit £8,000 per condition excess £100",
                "maximum £3,000 excess £200",
                "cover up to £4,500 excess £150",
                "limit of £12,000 excess £350",
            ],
        })
        st.session_state["sample_df"] = sample
        st.success("Sample loaded!")

    st.divider()
    st.markdown("### ℹ️ About")
    st.markdown("""
    Cleans and validates Lloyd's/EU insurance bordereaux:
    - Column normalisation
    - Duplicate removal
    - Premium parsing
    - Date validation
    - Currency checks
    - VetFees text parsing (AI-ready)
    """)

# ── Upload ────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Drop your bordereaux file here",
    type=["csv", "xlsx", "xls"],
    help="Accepts CSV or Excel files",
)

# Load either uploaded or sample
df_raw = None
if uploaded:
    try:
        if uploaded.name.endswith(".csv"):
            df_raw = pd.read_csv(uploaded)
        else:
            df_raw = pd.read_excel(uploaded)
        st.success(f"Loaded **{uploaded.name}** — {len(df_raw):,} rows, {len(df_raw.columns)} columns")
    except Exception as e:
        st.error(f"Could not read file: {e}")
elif "sample_df" in st.session_state:
    df_raw = st.session_state["sample_df"]
    st.info("Using built-in sample data. Upload your own file above.")

# ── Preview ───────────────────────────────────────────────────
if df_raw is not None:
    with st.expander("📄 Raw data preview", expanded=False):
        st.dataframe(df_raw.head(10), use_container_width=True)

    st.divider()

    # ── Run pipeline ──────────────────────────────────────────
    with st.spinner("Running cleaning pipeline..."):
        try:
            df_clean, report, issues = clean_bordereaux(df_raw)
        except Exception as e:
            st.error(f"Pipeline error: {e}")
            st.stop()

    # ── Metrics ───────────────────────────────────────────────
    st.markdown("### 📊 Quality Report")
    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        st.metric("Rows (clean)", report["total_rows"], delta=f"{report['total_rows'] - len(df_raw)} from raw")
    with m2:
        st.metric("Date Errors", report["date_errors"],
                  delta=None if report["date_errors"] == 0 else "⚠️ review",
                  delta_color="inverse")
    with m3:
        st.metric("Invalid Currencies", report["invalid_currencies"],
                  delta_color="inverse")
    with m4:
        if report.get("total_premium"):
            st.metric("Total Premium", f"£{report['total_premium']:,.0f}")
        else:
            st.metric("Total Premium", "N/A")
    with m5:
        if report.get("avg_premium"):
            st.metric("Avg Premium", f"£{report['avg_premium']:,.0f}")
        else:
            st.metric("Avg Premium", "N/A")

    # Issues
    if issues:
        for issue in issues:
            st.warning(f"⚠️ {issue}")
    else:
        st.success("✅ No structural issues found.")

    # ── VetFees parsing ───────────────────────────────────────
    if parse_vetfees_col:
        vetfees_normalized = vetfees_col_name.lower().replace(" ", "_")
        if vetfees_normalized in df_clean.columns:
            st.divider()
            st.markdown("### 🔍 VetFees Parse Results")

            with st.spinner("Parsing VetFees wording..."):
                df_clean = clean_vetfees_column(df_clean, column=vetfees_normalized)
                df_clean = parse_vetfees(df_clean, column=f"{vetfees_normalized}_clean")

            status_counts = df_clean["parse_status"].value_counts()
            total = len(df_clean)

            p1, p2, p3, p4 = st.columns(4)
            with p1:
                n = status_counts.get("parsed", 0)
                st.metric("Parsed", f"{n}", delta=f"{n/total*100:.0f}%")
            with p2:
                n = status_counts.get("partial", 0)
                st.metric("Partial", f"{n}", delta=f"{n/total*100:.0f}%")
            with p3:
                n = status_counts.get("ambiguous", 0)
                st.metric("Ambiguous", f"{n}", delta=f"{n/total*100:.0f}%")
            with p4:
                n = status_counts.get("failed", 0)
                st.metric("Failed", f"{n}", delta=f"{n/total*100:.0f}%")

            parse_cols = [c for c in ["policy_number", vetfees_normalized, "claimlimit_gbp",
                                       "vetfeesexcessamount", "parse_status", "claimlimit_confidence"]
                          if c in df_clean.columns]
            st.dataframe(
                df_clean[parse_cols].rename(columns={
                    "claimlimit_gbp": "Claim Limit (£)",
                    "vetfeesexcessamount": "Excess (£)",
                    "parse_status": "Status",
                    "claimlimit_confidence": "Confidence",
                }),
                use_container_width=True,
            )
        elif vetfees_col_name:
            st.info(f"Column '{vetfees_col_name}' not found in file. VetFees parsing skipped.")

    # ── Error rows ────────────────────────────────────────────
    st.divider()
    st.markdown("### ⚠️ Flagged Rows")

    error_mask = pd.Series(False, index=df_clean.index)
    for col in ["date_error", "has_missing_required"]:
        if col in df_clean.columns:
            error_mask = error_mask | df_clean[col].fillna(False)
    if "currency_valid" in df_clean.columns:
        error_mask = error_mask | (~df_clean["currency_valid"].fillna(True))

    if error_mask.sum() > 0:
        st.warning(f"{error_mask.sum()} row(s) flagged for review:")
        st.dataframe(df_clean[error_mask], use_container_width=True)
    else:
        st.success("No rows flagged.")

    # ── Clean data preview ────────────────────────────────────
    st.divider()
    st.markdown("### ✅ Cleaned Data")
    st.dataframe(df_clean, use_container_width=True)

    # ── Downloads ─────────────────────────────────────────────
    st.divider()
    st.markdown("### 📥 Download Results")

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    d1, d2, d3 = st.columns(3)

    with d1:
        st.download_button(
            label="⬇️ Download Clean File (XLSX)",
            data=to_excel_bytes(df_clean),
            file_name=f"bordereaux_CLEAN_{ts}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with d2:
        if error_mask.sum() > 0:
            st.download_button(
                label="⬇️ Download Errors (XLSX)",
                data=to_excel_bytes(df_clean[error_mask]),
                file_name=f"bordereaux_ERRORS_{ts}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        else:
            st.button("No Errors to Download", disabled=True, use_container_width=True)
    with d3:
        st.download_button(
            label="⬇️ Download Clean File (CSV)",
            data=to_csv_bytes(df_clean),
            file_name=f"bordereaux_CLEAN_{ts}.csv",
            mime="text/csv",
            use_container_width=True,
        )

else:
    # ── Empty state ───────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;color:#6b7280;">
        <div style="font-size:48px;">📁</div>
        <h3>Upload a bordereaux file to get started</h3>
        <p>Supports CSV and Excel (.xlsx, .xls)</p>
        <p>Or load the built-in sample data from the sidebar →</p>
    </div>
    """, unsafe_allow_html=True)
