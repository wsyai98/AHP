# app.py
from __future__ import annotations

import io
from typing import Tuple

import numpy as np
import pandas as pd
import streamlit as st

# ---------------- Page config ----------------
st.set_page_config(page_title="AHP — Section 3 (GM + Consistency)", layout="wide")

# ---------------- RI / SA table (Saaty) ----------------
RI_TABLE = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
    11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59
}

def approx_RI(m: int) -> float:
    if m in RI_TABLE:
        return RI_TABLE[m]
    if m <= 2:
        return 0.0
    return 1.98 * (m - 2) / m

# ---------------- Sample CSV (pairwise) ----------------
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
            raise ValueError(f"Division by zero fraction: {s}")
        v = num / den
    else:
        v = float(s)

    if not np.isfinite(v) or v <= 0:
        raise ValueError(f"Value must be positive. Got: {s}")
    return float(v)

def read_pairwise_csv_bytes(uploaded_bytes: bytes) -> pd.DataFrame:
    text = uploaded_bytes.decode("utf-8", errors="ignore")
    for sep in [",", "\t", ";"]:
        try:
            df = pd.read_csv(io.StringIO(text), sep=sep, header=0, index_col=0)
            if df.shape[0] >= 2 and df.shape[0] == df.shape[1]:
                return df
        except Exception:
            pass
    raise ValueError("CSV not recognized. Need square m×m with row labels in first column.")

def numeric_matrix_from_df(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df.index = [str(i).strip() for i in df.index]

    mat = np.zeros(df.shape, dtype=float)
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            mat[i, j] = parse_ratio(df.iat[i, j])
    return pd.DataFrame(mat, index=df.index, columns=df.columns)

def check_square_labels(df: pd.DataFrame) -> Tuple[bool, str]:
    if df.shape[0] != df.shape[1]:
        return False, "Matrix is not square."
    if list(df.index) != list(df.columns):
        return False, "Row labels and column labels are not identical."
    return True, "OK"

def check_reciprocal(P: np.ndarray, tol: float = 1e-6) -> Tuple[bool, float]:
    m = P.shape[0]
    errs = []
    for i in range(m):
        errs.append(abs(P[i, i] - 1.0))
        for j in range(i + 1, m):
            errs.append(abs(P[i, j] * P[j, i] - 1.0))
    max_err = float(max(errs)) if errs else 0.0
    return (max_err <= tol), max_err

def ahp_geometric_mean(P: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    # Step 2–4:
    # Π_i = ∏_j p_ij
    # GM_i = (Π_i)^(1/m)
    # ω_i = GM_i / Σ GM
    m = P.shape[0]
    Pi = np.prod(P, axis=1)
    GM = Pi ** (1.0 / m)
    s = GM.sum()
    if s == 0:
        raise ValueError("Sum of GM is zero (unexpected). Check values.")
    w = GM / s
    return Pi, GM, w

def ahp_consistency(P: np.ndarray, w: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float, float, float]:
    # Step 5–7:
    # Pω, λ_i = (Pω)_i / ω_i
    # λmax = avg(λ_i)
    # SI = (λmax - m)/(m-1)
    # CR = SI/RI
    Pw = P @ w
    lam = Pw / np.where(w == 0, 1e-18, w)
    lam_max = float(np.mean(lam))
    m = P.shape[0]
    SI = 0.0 if m <= 1 else (lam_max - m) / (m - 1)
    RI = approx_RI(m)
    CR = 0.0 if RI == 0 else SI / RI
    return Pw, lam, lam_max, SI, CR

def df_style_for_theme(df: pd.DataFrame, dark: bool):
    # Apply consistent text color for dark/light
    txt = "#f8fafc" if dark else "#0b1220"
    head_bg = "rgba(167,139,250,.22)" if dark else "rgba(167,139,250,.18)"
    body_bg = "rgba(255,255,255,.04)" if dark else "rgba(255,255,255,.82)"
    border = "rgba(226,232,240,.18)" if dark else "rgba(148,163,184,.35)"
    return (
        df.style
        .set_table_styles([
            {"selector": "th", "props": [("color", txt), ("background-color", head_bg), ("border-color", border)]},
            {"selector": "td", "props": [("color", txt), ("background-color", body_bg), ("border-color", border)]},
            {"selector": "table", "props": [("border-collapse", "collapse")]},
        ])
    )

# ---------------- Theme CSS ----------------
def inject_css(dark: bool):
    # purple pastel theme; no painful colors
    if dark:
        bg = """
        radial-gradient(1100px 600px at 15% 0%, rgba(167,139,250,.22), transparent 60%),
        radial-gradient(900px 500px at 85% 10%, rgba(196,181,253,.18), transparent 60%),
        linear-gradient(180deg, #070711 0%, #141227 60%, rgba(243,232,255,.18) 140%)
        """
        card = "rgba(255,255,255,.06)"
        border = "rgba(226,232,240,.16)"
        txt = "#f8fafc"
        sub = "rgba(248,250,252,.75)"
        pill_bg = "rgba(167,139,250,.22)"
        pill_bd = "rgba(167,139,250,.35)"
        pill_txt = "#f8fafc"
    else:
        bg = """
        radial-gradient(1100px 600px at 15% 0%, rgba(167,139,250,.18), transparent 60%),
        radial-gradient(900px 500px at 85% 10%, rgba(196,181,253,.14), transparent 60%),
        linear-gradient(180deg, #f8fafc 0%, #ffffff 55%, rgba(243,232,255,.55) 140%)
        """
        card = "rgba(255,255,255,.88)"
        border = "rgba(148,163,184,.30)"
        txt = "#0b1220"
        sub = "rgba(15,23,42,.70)"
        pill_bg = "rgba(167,139,250,.14)"
        pill_bd = "rgba(167,139,250,.28)"
        pill_txt = "#0b1220"

    st.markdown(
        f"""
<style>
  .stApp {{
    background: {bg} !important;
    color: {txt} !important;
  }}
  [data-testid="stSidebar"] {{
    background: rgba(255,255,255,.06) !important;
    backdrop-filter: blur(8px);
  }}
  .block-container {{ padding-top: 1.2rem; max-width: 1100px; }} /* <-- memanjang ke bawah, tak melebar */
  .card {{
    border-radius: 18px;
    padding: 16px 16px;
    border: 1px solid {border};
    background: {card};
    backdrop-filter: blur(8px);
    margin-bottom: 14px;
  }}
  .title {{
    font-size: 34px;
    font-weight: 900;
    letter-spacing: .2px;
    margin: 0 0 6px 0;
  }}
  .subtitle {{
    color: {sub};
    margin: 0 0 10px 0;
  }}
  .topbar {{
    display:flex;
    justify-content:space-between;
    align-items:center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 10px;
  }}
  .pills {{
    display:flex;
    gap: 8px;
    flex-wrap: wrap;
    margin: 8px 0 0 0;
  }}
  .pill {{
    display:inline-flex;
    align-items:center;
    padding: 7px 12px;
    border-radius: 999px;
    background: {pill_bg};
    border: 1px solid {pill_bd};
    color: {pill_txt};
    font-weight: 800;
    font-size: 12px;
  }}
  .h3 {{
    font-size: 18px;
    font-weight: 900;
    margin: 0 0 10px 0;
  }}
  .ok {{ color: #22c55e; font-weight: 900; }}
  .bad {{ color: #ef4444; font-weight: 900; }}
</style>
""",
        unsafe_allow_html=True,
    )

# ---------------- Sidebar controls ----------------
with st.sidebar:
    st.markdown("### Settings")
    dark = st.toggle("Dark mode", value=True)
inject_css(dark)

# ---------------- Header ----------------
st.markdown(
    """
<div class="topbar">
  <div>
    <div class="title">AHP — Section 3 (GM + Consistency)</div>
    <div class="subtitle">Step-by-step tables (maintain Step 1A → Step 7). Upload CSV or Load Sample.</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------- Step 1 (controls) ----------------
colA, colB = st.columns([1, 1], gap="large")

with colA:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="h3">Step 1 — Upload CSV (Pairwise Matrix P)</div>', unsafe_allow_html=True)

    cbtn1, cbtn2 = st.columns([1, 1])
    with cbtn1:
        st.download_button(
            "⬇️ Sample CSV",
            data=SAMPLE.encode("utf-8"),
            file_name="sample_pairwise_matrix.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with cbtn2:
        if st.button("📄 Load Sample", use_container_width=True):
            st.session_state["use_sample"] = True

    uploaded = st.file_uploader("📤 Choose CSV", type=["csv", "txt"], label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

with colB:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="h3">Results (Step 2 — Step 7)</div>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="pills">
  <span class="pill">Step 2 Π</span>
  <span class="pill">Step 3 GM</span>
  <span class="pill">Step 4 ω</span>
  <span class="pill">Step 5 Pω</span>
  <span class="pill">Step 6 λ</span>
  <span class="pill">Step 7 SI & CR</span>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Load data (upload OR sample) ----------------
df_raw = None
source_label = None

try:
    if st.session_state.get("use_sample", False) and uploaded is None:
        df_raw = pd.read_csv(io.StringIO(SAMPLE), sep=",", header=0, index_col=0)
        source_label = "Sample"
    elif uploaded is not None:
        df_raw = read_pairwise_csv_bytes(uploaded.getvalue())
        source_label = "Upload"
except Exception as e:
    st.error(f"Error reading CSV: {e}")

# If no data, stop quietly (no annoying message)
if df_raw is None:
    st.stop()

# ---------------- Compute ----------------
try:
    df_num = numeric_matrix_from_df(df_raw)
    ok_lbl, _ = check_square_labels(df_num)
    P = df_num.values.astype(float)
    m = P.shape[0]

    recip_ok, recip_err = check_reciprocal(P, tol=1e-6)

    Pi, GM, w = ahp_geometric_mean(P)
    Pw, lam, lam_max, SI, CR = ahp_consistency(P, w)

except Exception as e:
    st.error(f"Error calculating AHP: {e}")
    st.stop()

# ---------------- Output layout (STACKED, not sideways) ----------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown(f'<div class="h3">Step 1A — Raw CSV (preview) <span class="subtitle">({source_label})</span></div>', unsafe_allow_html=True)
st.dataframe(df_style_for_theme(df_raw, dark), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown(
    f'<div class="h3">Step 1B — Numeric P</div>'
    f'<div class="subtitle">m = {m} • '
    + (f'<span class="ok">reciprocal OK</span>' if recip_ok else f'<span class="bad">reciprocal off</span> (max err {recip_err:.2e})')
    + "</div>",
    unsafe_allow_html=True,
)
st.dataframe(df_style_for_theme(df_num, dark).format("{:.6g}"), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# Step 2
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="h3">Step 2 — Πᵢ = ∏ⱼ pᵢⱼ</div>', unsafe_allow_html=True)
df_step2 = pd.DataFrame({"Criterion": df_num.index, "Πᵢ": Pi}).set_index("Criterion")
st.dataframe(df_style_for_theme(df_step2, dark).format({"Πᵢ": "{:.10f}"}), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# Step 3
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="h3">Step 3 — GMᵢ = (Πᵢ)^(1/m)</div>', unsafe_allow_html=True)
df_step3 = pd.DataFrame({"Criterion": df_num.index, "GMᵢ": GM}).set_index("Criterion")
st.dataframe(df_style_for_theme(df_step3, dark).format({"GMᵢ": "{:.10f}"}), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# Step 4
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="h3">Step 4 — ωᵢ = GMᵢ / ΣGM</div>', unsafe_allow_html=True)
df_step4 = pd.DataFrame({"Criterion": df_num.index, "ωᵢ": w}).set_index("Criterion")
st.dataframe(df_style_for_theme(df_step4, dark).format({"ωᵢ": "{:.10f}"}), use_container_width=True)
st.bar_chart(df_step4["ωᵢ"])  # simple pastel-ish default
st.markdown("</div>", unsafe_allow_html=True)

# Step 5
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="h3">Step 5 — Pω</div>', unsafe_allow_html=True)
df_step5 = pd.DataFrame({"Criterion": df_num.index, "(Pω)ᵢ": Pw}).set_index("Criterion")
st.dataframe(df_style_for_theme(df_step5, dark).format({"(Pω)ᵢ": "{:.10f}"}), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# Step 6
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="h3">Step 6 — λᵢ = (Pω)ᵢ / ωᵢ ;  λmax = avg(λᵢ)</div>', unsafe_allow_html=True)
df_step6 = pd.DataFrame({"Criterion": df_num.index, "ωᵢ": w, "(Pω)ᵢ": Pw, "λᵢ": lam}).set_index("Criterion")
st.dataframe(
    df_style_for_theme(df_step6, dark).format({"ωᵢ": "{:.10f}", "(Pω)ᵢ": "{:.10f}", "λᵢ": "{:.10f}"}),
    use_container_width=True
)
st.markdown(f"<div class='subtitle'><b>λmax</b> = {lam_max:.10f}</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Step 7
RI = approx_RI(m)
ok = CR <= 0.10
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="h3">Step 7 — SI & CR</div>', unsafe_allow_html=True)
st.markdown(
    f"""
<div class="subtitle">
  <b>RI</b> = {RI:.4f} <br/>
  <b>SI</b> = (λmax − m)/(m − 1) = <b>{SI:.10f}</b> <br/>
  <b>CR</b> = SI/RI = <b>{CR:.10f}</b>
  &nbsp;→&nbsp; {'<span class="ok">ACCEPTABLE (≤ 0.10)</span>' if ok else '<span class="bad">NOT OK (> 0.10)</span>'}
</div>
""",
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# Export (all step results)
out = pd.DataFrame(
    {"Πᵢ": Pi, "GMᵢ": GM, "ωᵢ": w, "(Pω)ᵢ": Pw, "λᵢ": lam},
    index=df_num.index
)
st.download_button(
    "⬇️ Download Results (CSV)",
    data=out.to_csv(index=True).encode("utf-8"),
    file_name="ahp_section3_step_by_step.csv",
    mime="text/csv",
    use_container_width=True,
)
