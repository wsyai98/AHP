# app.py
from __future__ import annotations

import io
import math
from pathlib import Path
from typing import Tuple, Optional

import numpy as np
import pandas as pd
import streamlit as st

# ---------------- Page config ----------------
st.set_page_config(page_title="AHP (Saaty) — Step-by-Step (GM + Consistency)", layout="wide")

# ---------------- Styling (purple pastel-ish) ----------------
st.markdown(
    """
<style>
  .stApp {
    background:
      radial-gradient(1200px 600px at 20% 0%, rgba(167,139,250,.22), transparent 55%),
      radial-gradient(900px 500px at 85% 10%, rgba(196,181,253,.18), transparent 60%),
      linear-gradient(180deg, #0b0b10 0%, #141227 55%, rgba(243,232,255,.25) 140%) !important;
  }
  [data-testid="stSidebar"] {
    background: rgba(237, 233, 254, 0.08) !important;
    backdrop-filter: blur(6px);
  }
  .block-container { padding-top: 1.25rem; }
  .card {
    border-radius: 16px;
    padding: 16px;
    border: 1px solid rgba(226,232,240,.25);
    background: rgba(255,255,255,.06);
    backdrop-filter: blur(8px);
  }
  .cardLight {
    border-radius: 16px;
    padding: 16px;
    border: 1px solid rgba(226,232,240,.7);
    background: rgba(255,255,255,.78);
    color: #111;
  }
  .pill {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    border: 1px solid rgba(196,181,253,.9);
    background: rgba(237,233,254,.75);
    color: #111;
    font-weight: 800;
    font-size: 12px;
    margin-right: 8px;
    margin-bottom: 8px;
  }
  .ok { color: #16a34a; font-weight: 900; }
  .bad { color: #dc2626; font-weight: 900; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------- RI / SA table (Saaty) ----------------
# (Paper uses SA for RI; same role)
RI_TABLE = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
    11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59
}

def approx_RI(m: int) -> float:
    # For m > 15, common approximation: RI ≈ 1.98*(m-2)/m
    # (same as paper mentions for SA when m > 15)
    if m in RI_TABLE:
        return RI_TABLE[m]
    if m <= 2:
        return 0.0
    return 1.98 * (m - 2) / m

# ---------------- Helpers ----------------
def parse_ratio(x) -> float:
    """
    Accept: 3, 0.5, "1/3", "  2 / 5  "
    Return float > 0, or raise ValueError.
    """
    if pd.isna(x):
        raise ValueError("Empty cell detected.")
    s = str(x).strip()
    if s == "":
        raise ValueError("Empty cell detected.")
    s = s.replace("\\", "/")  # just in case user typed 1\3
    if "/" in s:
        parts = s.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid fraction: {s}")
        num = float(parts[0].strip())
        den = float(parts[1].strip())
        if den == 0:
            raise ValueError(f"Division by zero fraction: {s}")
        v = num / den
    else:
        v = float(s)

    if not np.isfinite(v) or v <= 0:
        raise ValueError(f"Value must be positive. Got: {s}")
    return float(v)

def read_pairwise_csv(uploaded_bytes: bytes) -> pd.DataFrame:
    """
    Try to read as CSV (comma) and TSV. Expect square matrix with labels.
    First column should be row labels.
    """
    text = uploaded_bytes.decode("utf-8", errors="ignore")
    # try comma
    for sep in [",", "\t", ";"]:
        try:
            df = pd.read_csv(io.StringIO(text), sep=sep, header=0, index_col=0)
            if df.shape[0] >= 2 and df.shape[0] == df.shape[1]:
                return df
        except Exception:
            pass
    raise ValueError("CSV format not recognized. Make sure it is a square pairwise matrix with row labels in first column.")

def numeric_matrix_from_df(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    # strip headers/index
    df.columns = [str(c).strip() for c in df.columns]
    df.index = [str(i).strip() for i in df.index]

    # convert each cell via parse_ratio
    mat = np.zeros(df.shape, dtype=float)
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            mat[i, j] = parse_ratio(df.iat[i, j])
    return pd.DataFrame(mat, index=df.index, columns=df.columns)

def check_square_labels(df: pd.DataFrame) -> Tuple[bool, str]:
    if df.shape[0] != df.shape[1]:
        return False, "Matrix is not square."
    if list(df.index) != list(df.columns):
        return False, "Row labels and column labels are not identical (recommended to match)."
    return True, "OK"

def check_reciprocal(P: np.ndarray, tol: float = 1e-6) -> Tuple[bool, float]:
    """
    Check p_ij * p_ji ≈ 1 for i!=j, diagonal ≈ 1.
    Returns (ok, max_abs_error)
    """
    m = P.shape[0]
    errs = []
    for i in range(m):
        errs.append(abs(P[i, i] - 1.0))
        for j in range(i + 1, m):
            errs.append(abs(P[i, j] * P[j, i] - 1.0))
    max_err = float(max(errs)) if errs else 0.0
    return (max_err <= tol), max_err

def ahp_geometric_mean(P: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Step 2–4:
    Pi_i = product of row
    root_i = (Pi_i)^(1/m)
    w_i = root_i / sum(root)
    """
    m = P.shape[0]
    Pi = np.prod(P, axis=1)
    root = Pi ** (1.0 / m)
    s = root.sum()
    if s == 0:
        raise ValueError("Sum of roots is zero (unexpected). Check matrix values.")
    w = root / s
    return Pi, root, w

def ahp_consistency(P: np.ndarray, w: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float, float, float]:
    """
    Step 5–7:
    Pw, lambda_i, lambda_max, SI, CR
    """
    Pw = P @ w
    lam = Pw / np.where(w == 0, 1e-18, w)
    lam_max = float(np.mean(lam))
    m = P.shape[0]
    if m <= 1:
        SI = 0.0
    else:
        SI = (lam_max - m) / (m - 1)
    RI = approx_RI(m)
    CR = 0.0 if RI == 0 else SI / RI
    return Pw, lam, lam_max, SI, CR

# ---------------- Sample CSV (your B1..B7 example) ----------------
SAMPLE = """B,B1,B2,B3,B4,B5,B6,B7
B1,1,1/2,1/3,1/3,1/3,1/5,1
B2,2,1,1/3,1,1/3,1/5,1
B3,3,3,1,3,1,1,1
B4,3,1,1/3,1,1/3,1/3,1/3
B5,3,3,1,3,1,1,1
B6,5,5,1,3,1,1,1
B7,1,1,1,3,1,1,1
"""

# ---------------- UI ----------------
st.markdown("## AHP (Saaty) — Step-by-Step (Geometric Mean + Consistency)")
st.caption("Input: **CSV pairwise comparison matrix** (no alternatives). Output: **weights, Pω, λmax, SI, CR**.")

left, right = st.columns([1, 1.2], gap="large")

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Step 1 — Upload CSV (Pairwise Matrix P)")
    st.write("CSV mesti **square** (m×m), ada **row label** pada kolum pertama, dan value boleh `1/3`.")
    st.download_button(
        "⬇️ Download Sample CSV",
        data=SAMPLE.encode("utf-8"),
        file_name="sample_pairwise_matrix.csv",
        mime="text/csv",
        use_container_width=True,
    )
    uploaded = st.file_uploader("📤 Choose CSV", type=["csv", "txt"])
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card" style="margin-top:14px;">', unsafe_allow_html=True)
    st.markdown("### Nota pasal ‘benefit/cost’")
    st.write(
        "Dalam **AHP untuk weight kriteria**, kau compare **kepentingan** kriteria guna skala Saaty. "
        "Label benefit/cost tu biasanya masuk **masa evaluate alternatives** (bukan masa bina weight kriteria)."
    )
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="cardLight">', unsafe_allow_html=True)
    st.markdown("### Output akan keluar di sini (Step 2–7)")
    st.markdown(
        '<span class="pill">Step 2: Validate matrix</span>'
        '<span class="pill">Step 3: Row products Π</span>'
        '<span class="pill">Step 4: Roots & weights ω</span>'
        '<span class="pill">Step 5: Pω</span>'
        '<span class="pill">Step 6: λᵢ & λmax</span>'
        '<span class="pill">Step 7: SI & CR</span>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- Run computation if file exists ----------------
if uploaded is None:
    st.info("Upload CSV dulu. Kalau nak test cepat, download sample dan upload balik.")
    st.stop()

try:
    df_raw = read_pairwise_csv(uploaded.getvalue())
    df_num = numeric_matrix_from_df(df_raw)

    ok_lbl, msg_lbl = check_square_labels(df_num)
    P = df_num.values.astype(float)
    m = P.shape[0]

    # Step 2: validate
    recip_ok, recip_err = check_reciprocal(P, tol=1e-6)

    # Step 3-4: weights
    Pi, root, w = ahp_geometric_mean(P)

    # Step 5-7: consistency
    Pw, lam, lam_max, SI, CR = ahp_consistency(P, w)

except Exception as e:
    st.error(f"Error reading/calculating: {e}")
    st.stop()

# ---------------- Display step-by-step ----------------
st.markdown("### Step 2 — Detected Matrix P (numeric)")
c1, c2 = st.columns([1, 1])
with c1:
    st.write(f"**Matrix size:** m = {m}")
    if not ok_lbl:
        st.warning(msg_lbl + " (App masih boleh kira, tapi lebih kemas kalau label sama.)")
    else:
        st.success("Row/column labels match ✓")

with c2:
    if recip_ok:
        st.success("Reciprocal check OK: pᵢⱼ·pⱼᵢ ≈ 1 and diagonal ≈ 1 ✓")
    else:
        st.warning(f"Reciprocal check not perfect (max error ≈ {recip_err:.2e}). "
                   "Kalau kau memang isi full matrix, pastikan pji = 1/pij dan diagonal = 1.")

st.dataframe(df_num.style.format("{:.6g}"), use_container_width=True)

st.markdown("### Step 3 — Products of row elements (Πᵢ)")
df_step3 = pd.DataFrame({"Π_i (row product)": Pi}, index=df_num.index)
st.dataframe(df_step3.style.format("{:.6g}"), use_container_width=True)

st.markdown("### Step 4 — m-th root and normalized weights (ω)")
df_step4 = pd.DataFrame(
    {
        "root_i = (Π_i)^(1/m)": root,
        "ω_i = root_i / Σroot": w,
    },
    index=df_num.index,
)
st.dataframe(df_step4.style.format({"root_i = (Π_i)^(1/m)": "{:.6g}", "ω_i = root_i / Σroot": "{:.9f}"}),
             use_container_width=True)

st.markdown("### Step 5 — Multiply matrix by weights: Pω")
df_step5 = pd.DataFrame({"(Pω)_i": Pw}, index=df_num.index)
st.dataframe(df_step5.style.format("{:.9f}"), use_container_width=True)

st.markdown("### Step 6 — λᵢ = (Pω)ᵢ / ωᵢ and λmax (average)")
df_step6 = pd.DataFrame(
    {
        "λ_i": lam,
    },
    index=df_num.index,
)
st.dataframe(df_step6.style.format("{:.9f}"), use_container_width=True)
st.write(f"**λmax = average(λᵢ) = {lam_max:.9f}**")

st.markdown("### Step 7 — Consistency Index (SI) and Consistency Ratio (CR)")
RI = approx_RI(m)
ok = CR <= 0.10

st.markdown(
    f"""
<div class="cardLight">
  <div><b>m</b> = {m}</div>
  <div><b>RI (SA)</b> = {RI:.4f}</div>
  <div><b>SI</b> = (λmax − m)/(m − 1) = <b>{SI:.9f}</b></div>
  <div><b>CR</b> = SI/RI = <b>{CR:.9f}</b>
    &nbsp;→&nbsp; {'<span class="ok">ACCEPTABLE (≤ 0.10)</span>' if ok else '<span class="bad">NOT OK (> 0.10)</span>'}
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------- Export results ----------------
st.markdown("### Export")
out = pd.DataFrame(
    {
        "Π_i": Pi,
        "root_i": root,
        "ω_i": w,
        "(Pω)_i": Pw,
        "λ_i": lam,
    },
    index=df_num.index,
)
csv_bytes = out.to_csv(index=True).encode("utf-8")
st.download_button(
    "⬇️ Download Results (CSV)",
    data=csv_bytes,
    file_name="ahp_results_step_by_step.csv",
    mime="text/csv",
    use_container_width=True,
)

st.caption(
    "Kiraan ikut kaedah **Geometric Mean**: product row → m-th root → normalize; "
    "kemudian kira λmax, SI dan CR (acceptable jika CR ≤ 0.10)."
)
