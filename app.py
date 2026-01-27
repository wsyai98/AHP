# app.py
from __future__ import annotations

import io
import numpy as np
import pandas as pd
import streamlit as st

# ---------------- Page config ----------------
st.set_page_config(page_title="AHP (Saaty) — Paper Section 3 (GM + Consistency)", layout="wide")

# ---------------- Minimal styling (keep your purple theme) ----------------
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
    display:inline-block;
    padding:6px 10px;
    border-radius:999px;
    border:1px solid rgba(196,181,253,.9);
    background: rgba(237,233,254,.75);
    color:#111;
    font-weight:900;
    font-size:12px;
    margin-right:8px;
    margin-bottom:8px;
  }
  .ok { color:#16a34a; font-weight: 900; }
  .bad { color:#dc2626; font-weight: 900; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------- Saaty RI table ----------------
RI_TABLE = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
    11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59
}

def RI(m: int) -> float:
    if m in RI_TABLE:
        return RI_TABLE[m]
    if m <= 2:
        return 0.0
    # common approximation if m>15
    return 1.98 * (m - 2) / m

# ---------------- Sample CSV (pairwise matrix) ----------------
SAMPLE = """B,B1,B2,B3,B4,B5,B6,B7
B1,1,1/2,1/3,1/3,1/3,1/5,1
B2,2,1,1/3,1,1/3,1/5,1
B3,3,3,1,3,1,1,1
B4,3,1,1/3,1,1/3,1/3,1/3
B5,3,3,1,3,1,1,1
B6,5,5,1,3,1,1,1
B7,1,1,1,3,1,1,1
"""

# ---------------- Helpers ----------------
def parse_ratio(x) -> float:
    """
    Accept: 3, 0.5, '1/3', ' 2 / 5 '
    Return float > 0.
    """
    if pd.isna(x):
        raise ValueError("Empty cell detected.")
    s = str(x).strip()
    if s == "":
        raise ValueError("Empty cell detected.")
    s = s.replace("\\", "/")

    if "/" in s:
        parts = s.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid fraction: {s}")
        num = float(parts[0].strip())
        den = float(parts[1].strip())
        if den == 0:
            raise ValueError(f"Division by zero: {s}")
        v = num / den
    else:
        v = float(s)

    if not np.isfinite(v) or v <= 0:
        raise ValueError(f"Value must be positive: {s}")
    return float(v)

def read_pairwise_csv(uploaded_bytes: bytes) -> pd.DataFrame:
    """
    Read square matrix with row labels in first column.
    Accept separators: comma, tab, semicolon.
    """
    text = uploaded_bytes.decode("utf-8", errors="ignore")
    for sep in [",", "\t", ";"]:
        try:
            df = pd.read_csv(io.StringIO(text), sep=sep, header=0, index_col=0)
            if df.shape[0] >= 2 and df.shape[0] == df.shape[1]:
                df.columns = [str(c).strip() for c in df.columns]
                df.index = [str(i).strip() for i in df.index]
                return df
        except Exception:
            pass
    raise ValueError("CSV not recognized. Need square matrix with row labels in first column.")

def to_numeric_df(df_raw: pd.DataFrame) -> pd.DataFrame:
    mat = np.zeros(df_raw.shape, dtype=float)
    for i in range(df_raw.shape[0]):
        for j in range(df_raw.shape[1]):
            mat[i, j] = parse_ratio(df_raw.iat[i, j])
    return pd.DataFrame(mat, index=df_raw.index, columns=df_raw.columns)

def check_square_and_labels(df: pd.DataFrame) -> None:
    if df.shape[0] != df.shape[1]:
        raise ValueError("Matrix is not square.")
    # recommended (not forced): index == columns
    # we'll compute anyway

def check_reciprocal(P: np.ndarray) -> tuple[bool, float]:
    m = P.shape[0]
    errs = []
    for i in range(m):
        errs.append(abs(P[i, i] - 1.0))
        for j in range(i + 1, m):
            errs.append(abs(P[i, j] * P[j, i] - 1.0))
    mx = float(max(errs)) if errs else 0.0
    return (mx <= 1e-6), mx

# ---------------- Paper Section 3 steps ----------------
def step2_row_product(P: np.ndarray) -> np.ndarray:
    # Π_i = ∏_j p_ij
    return np.prod(P, axis=1)

def step3_gm(Pi: np.ndarray, m: int) -> np.ndarray:
    # GM_i = (Π_i)^(1/m)
    return Pi ** (1.0 / m)

def step4_weights(GM: np.ndarray) -> np.ndarray:
    # ω_i = GM_i / Σ GM
    s = float(np.sum(GM))
    if s == 0:
        raise ValueError("Sum(GM) is zero.")
    return GM / s

def step5_full_multiply(P: np.ndarray, w: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Build full table of p_ij * w_j, then row-sum gives (Pω)_i.
    This is exactly the 'matrix multiply' intuition from the paper.
    """
    M = P * w.reshape(1, -1)         # each column j scaled by w_j
    Pw = np.sum(M, axis=1)           # row sums
    return M, Pw

def step6_lambda(Pw: np.ndarray, w: np.ndarray) -> tuple[np.ndarray, float]:
    lam = Pw / np.where(w == 0, 1e-18, w)
    lam_max = float(np.mean(lam))
    return lam, lam_max

def step7_consistency(lam_max: float, m: int) -> tuple[float, float, float]:
    if m <= 2:
        return 0.0, RI(m), 0.0
    SI = (lam_max - m) / (m - 1)
    ri = RI(m)
    CR = 0.0 if ri == 0 else SI / ri
    return float(SI), float(ri), float(CR)

# ---------------- UI ----------------
st.markdown("## AHP — Step-by-Step (Follow Paper Section 3)")
st.markdown(
    "<span class='pill'>Step 1 Upload P</span>"
    "<span class='pill'>Step 2 Π</span>"
    "<span class='pill'>Step 3 GM</span>"
    "<span class='pill'>Step 4 ω</span>"
    "<span class='pill'>Step 5 P×ω</span>"
    "<span class='pill'>Step 6 λmax</span>"
    "<span class='pill'>Step 7 SI & CR</span>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Upload Pairwise Matrix CSV")
    st.download_button(
        "⬇️ Download sample CSV",
        data=SAMPLE.encode("utf-8"),
        file_name="sample_pairwise_matrix.csv",
        mime="text/csv",
        use_container_width=True,
    )
    uploaded = st.file_uploader("📤 Choose CSV", type=["csv", "txt"])
    st.caption("Format: square matrix, first col = row labels, cells can be 1/3 etc.")

if uploaded is None:
    st.info("Upload CSV dulu.")
    st.stop()

# ---------------- Read + compute ----------------
try:
    df_raw = read_pairwise_csv(uploaded.getvalue())
    df_num = to_numeric_df(df_raw)
    check_square_and_labels(df_num)

    P = df_num.values.astype(float)
    names = list(df_num.index)
    m = P.shape[0]

    recip_ok, recip_err = check_reciprocal(P)

    # Step 2
    Pi = step2_row_product(P)

    # Step 3
    GM = step3_gm(Pi, m)

    # Step 4
    w = step4_weights(GM)

    # Step 5
    mult_table, Pw = step5_full_multiply(P, w)

    # Step 6
    lam, lam_max = step6_lambda(Pw, w)

    # Step 7
    SI, ri, CR = step7_consistency(lam_max, m)

except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

# ---------------- Show Step 1 ----------------
st.markdown("### Step 1 — Pairwise comparison matrix P (raw & numeric)")
c1, c2 = st.columns([1, 1], gap="large")
with c1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("**Step 1A: Raw CSV values**")
    st.dataframe(df_raw, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("**Step 1B: Numeric P (float)**")
    st.dataframe(df_num.style.format("{:.6g}"), use_container_width=True)
    st.write(f"m = **{m}**")
    if list(df_num.index) != list(df_num.columns):
        st.warning("Row labels != Column labels (recommended to match, but calculation continues).")
    if recip_ok:
        st.success("Reciprocal OK (pij*pji≈1, diag≈1)")
    else:
        st.warning(f"Reciprocal not perfect (max error={recip_err:.2e})")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Step 2 ----------------
st.markdown("### Step 2 — Row products  Πᵢ = ∏ⱼ pᵢⱼ")
df_step2 = pd.DataFrame({"Π_i": Pi}, index=names)
st.dataframe(df_step2.style.format("{:.9f}"), use_container_width=True)

# ---------------- Step 3 ----------------
st.markdown("### Step 3 — Geometric mean  GMᵢ = (Πᵢ)^(1/m)")
df_step3 = pd.DataFrame({"GM_i": GM}, index=names)
st.dataframe(df_step3.style.format("{:.9f}"), use_container_width=True)

# ---------------- Step 4 ----------------
st.markdown("### Step 4 — Weights  ωᵢ = GMᵢ / ΣGM")
sumGM = float(np.sum(GM))
df_step4 = pd.DataFrame(
    {"GM_i": GM, "ΣGM": [sumGM]*m, "ω_i": w},
    index=names
)
st.dataframe(df_step4.style.format({"GM_i": "{:.9f}", "ΣGM": "{:.9f}", "ω_i": "{:.9f}"}), use_container_width=True)
st.write(f"Check: Σω = **{float(np.sum(w)):.9f}** (must be 1.000000000)")

# ---------------- Step 5 (paper-like) ----------------
st.markdown("### Step 5 — Matrix multiplication: (pᵢⱼ × ωⱼ) then row-sum ⇒ (Pω)ᵢ")
st.caption("Table below shows **each cell**:  pᵢⱼ × ωⱼ  (column j scaled by ωⱼ). Then sum across row i gives (Pω)ᵢ.")

df_mult = pd.DataFrame(mult_table, index=names, columns=names)
st.dataframe(df_mult.style.format("{:.9f}"), use_container_width=True)

df_Pw = pd.DataFrame({"(Pω)_i (row-sum)": Pw}, index=names)
st.dataframe(df_Pw.style.format("{:.9f}"), use_container_width=True)

# ---------------- Step 6 ----------------
st.markdown("### Step 6 — λᵢ = (Pω)ᵢ / ωᵢ ,  λmax = average(λᵢ)")
df_step6 = pd.DataFrame(
    {"ω_i": w, "(Pω)_i": Pw, "λ_i": lam},
    index=names
)
st.dataframe(df_step6.style.format({"ω_i": "{:.9f}", "(Pω)_i": "{:.9f}", "λ_i": "{:.9f}"}), use_container_width=True)
st.write(f"**λmax = {lam_max:.9f}**")

# ---------------- Step 7 ----------------
st.markdown("### Step 7 — Consistency: SI and CR")
ok = CR <= 0.10
st.markdown(
    f"""
<div class="cardLight">
  <div><b>SI</b> = (λmax − m)/(m − 1) = <b>{SI:.9f}</b></div>
  <div><b>RI</b> = <b>{ri:.4f}</b></div>
  <div><b>CR</b> = SI/RI = <b>{CR:.9f}</b>
    &nbsp;→&nbsp; {"<span class='ok'>ACCEPTABLE (≤ 0.10)</span>" if ok else "<span class='bad'>NOT OK (> 0.10)</span>"}
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------- Export (everything) ----------------
st.markdown("### Download full step tables (CSV)")
export = pd.DataFrame(
    {
        "Π_i": Pi,
        "GM_i": GM,
        "ω_i": w,
        "(Pω)_i": Pw,
        "λ_i": lam,
    },
    index=names
)
st.download_button(
    "⬇️ Download summary results CSV",
    data=export.to_csv(index=True).encode("utf-8"),
    file_name="ahp_section3_results.csv",
    mime="text/csv",
    use_container_width=True,
)
