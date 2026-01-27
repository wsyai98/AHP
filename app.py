# app.py
from __future__ import annotations

import io
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# =========================================================
# Page config
# =========================================================
st.set_page_config(
    page_title="AHP (Saaty) — Section 3 (GM + Consistency)",
    layout="wide",
)

# =========================================================
# Theme (Dark/Light) + Styling (SYAI-Rank vibe)
# =========================================================
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "Dark"

THEME = st.session_state["theme_mode"]

st.markdown(
    f"""
<style>
  :root {{
    --bg-dark:#0b0b0f;
    --bg-light:#f8fafc;
    --grad-light:#ffe4e6;

    --card-dark: rgba(15,17,21,.80);
    --card-light: rgba(255,255,255,.85);

    --border-dark:#262b35;
    --border-light:#e5e7eb;

    --text-dark:#111;
    --text-light:#f5f5f5;

    --pink:#ec4899;
    --pink-700:#db2777;

    --muted-dark: rgba(255,255,255,.72);
    --muted-light: rgba(0,0,0,.65);
  }}

  .stApp {{
    background: linear-gradient(180deg,
      {"#0b0b0f 0%, #0b0b0f 35%, #ffe4e6 120%" if THEME=="Dark"
        else "#f8fafc 0%, #f8fafc 40%, #ffe4e6 120%"}
    ) !important;
  }}

  [data-testid="stSidebar"] {{
    background: rgba(255, 228, 230, 0.08) !important;
    backdrop-filter: blur(6px);
  }}

  .app-title {{
    font-weight: 900;
    font-size: 30px;
    letter-spacing: .2px;
    margin: 6px 0 10px 0;
    color: {"#fce7f3" if THEME=="Dark" else "#111"};
  }}

  .pill {{
    display:inline-flex;
    align-items:center;
    gap:8px;
    padding:6px 10px;
    border-radius:999px;
    border:1px solid rgba(219,39,119,.85);
    background: rgba(236,72,153,.18);
    color: {"#fff" if THEME=="Dark" else "#111"};
    font-weight: 800;
    font-size: 12px;
    margin-right: 8px;
    margin-bottom: 8px;
  }}

  .card-dark {{
    border-radius: 16px;
    padding: 16px;
    border: 1px solid var(--border-dark);
    background: var(--card-dark);
    color: var(--text-light);
    backdrop-filter: blur(6px);
  }}

  .card-light {{
    border-radius: 16px;
    padding: 16px;
    border: 1px solid var(--border-light);
    background: var(--card-light);
    color: var(--text-dark);
    backdrop-filter: blur(6px);
  }}

  .section-title {{
    font-weight: 800;
    font-size: 18px;
    margin: 0 0 10px 0;
    color: {"#f9a8d4" if THEME=="Dark" else "#be185d"};
  }}

  .hint {{
    font-size: 12px;
    opacity: .85;
    color: {"var(--muted-dark)" if THEME=="Dark" else "var(--muted-light)"};
  }}

  .ok {{ color:#16a34a; font-weight: 900; }}
  .bad {{ color:#dc2626; font-weight: 900; }}

  div[data-testid="stDataFrame"] {{
    border-radius: 12px;
    overflow: hidden;
  }}

  button[data-baseweb="tab"] {{
    border-radius: 12px !important;
    padding-top: 10px !important;
    padding-bottom: 10px !important;
  }}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# Saaty RI table
# =========================================================
RI_TABLE = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
    11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59
}

def RI(m: int) -> float:
    if m in RI_TABLE:
        return RI_TABLE[m]
    if m <= 2:
        return 0.0
    return 1.98 * (m - 2) / m

# =========================================================
# Sample CSV (pairwise matrix)
# =========================================================
SAMPLE = """B,B1,B2,B3,B4,B5,B6,B7
B1,1,1/2,1/3,1/3,1/3,1/5,1
B2,2,1,1/3,1,1/3,1/5,1
B3,3,3,1,3,1,1,1
B4,3,1,1/3,1,1/3,1/3,1/3
B5,3,3,1,3,1,1,1
B6,5,5,1,3,1,1,1
B7,1,1,1,3,1,1,1
"""

# =========================================================
# Helpers (UNCHANGED)
# =========================================================
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
            raise ValueError(f"Division by zero: {s}")
        v = num / den
    else:
        v = float(s)

    if not np.isfinite(v) or v <= 0:
        raise ValueError(f"Value must be positive: {s}")
    return float(v)

def read_pairwise_csv(uploaded_bytes: bytes) -> pd.DataFrame:
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

def check_reciprocal(P: np.ndarray) -> tuple[bool, float]:
    m = P.shape[0]
    errs = []
    for i in range(m):
        errs.append(abs(P[i, i] - 1.0))
        for j in range(i + 1, m):
            errs.append(abs(P[i, j] * P[j, i] - 1.0))
    mx = float(max(errs)) if errs else 0.0
    return (mx <= 1e-6), mx

# ---------------- Paper Section 3 steps (UNCHANGED) ----------------
def step2_row_product(P: np.ndarray) -> np.ndarray:
    return np.prod(P, axis=1)

def step3_gm(Pi: np.ndarray, m: int) -> np.ndarray:
    return Pi ** (1.0 / m)

def step4_weights(GM: np.ndarray) -> np.ndarray:
    s = float(np.sum(GM))
    if s == 0:
        raise ValueError("Sum(GM) is zero.")
    return GM / s

def step5_full_multiply(P: np.ndarray, w: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    M = P * w.reshape(1, -1)
    Pw = np.sum(M, axis=1)
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

# =========================================================
# SVG Pastel Bar Chart (NO matplotlib)
# =========================================================
PASTELS = [
    "#a5b4fc", "#f9a8d4", "#bae6fd", "#bbf7d0", "#fde68a",
    "#c7d2fe", "#fecdd3", "#fbcfe8", "#bfdbfe", "#d1fae5"
]

def render_pastel_bar_svg(labels: list[str], values: np.ndarray, height: int = 320) -> None:
    vals = [float(v) for v in values.tolist()]
    n = len(vals)
    if n == 0:
        st.info("No weights to plot.")
        return

    vmax = max(vals) if max(vals) > 0 else 1.0

    # SVG dimensions (responsive)
    svg_w = 900
    svg_h = 360
    padL, padR, padT, padB = 60, 20, 20, 70
    plotW = svg_w - padL - padR
    plotH = svg_h - padT - padB
    cell = plotW / n
    barW = cell * 0.75

    # build bars + labels
    bars = []
    ticks = []
    # y grid + ticks (0..5)
    for t in range(6):
        yv = vmax * t / 5.0
        y = padT + plotH - (plotH * (yv / vmax))
        ticks.append(
            f"""
            <line x1="{padL}" y1="{y:.2f}" x2="{svg_w-padR}" y2="{y:.2f}"
                  stroke="#000" stroke-dasharray="3 3" opacity="0.25"/>
            <text x="{padL-10}" y="{y+4:.2f}" font-size="12" text-anchor="end" fill="#000">{yv:.3f}</text>
            """
        )

    for i, (lab, v) in enumerate(zip(labels, vals)):
        h = plotH * (v / vmax)
        x = padL + i * cell + (cell - barW) / 2
        y = padT + (plotH - h)
        color = PASTELS[i % len(PASTELS)]
        bars.append(
            f"""
            <g>
              <rect x="{x:.2f}" y="{y:.2f}" width="{barW:.2f}" height="{h:.2f}"
                    rx="8" ry="8"
                    fill="{color}">
                <title>{lab}: {v:.9f}</title>
              </rect>
              <text x="{x + barW/2:.2f}" y="{svg_h-18}" font-size="12" text-anchor="middle" fill="#000">
                {lab}
              </text>
            </g>
            """
        )

    # axes
    axes = f"""
      <line x1="{padL}" y1="{padT}" x2="{padL}" y2="{svg_h-padB}" stroke="#000"/>
      <line x1="{padL}" y1="{svg_h-padB}" x2="{svg_w-padR}" y2="{svg_h-padB}" stroke="#000"/>
      <text x="{padL}" y="{padT-4}" font-size="12" fill="#000">ω (weights)</text>
    """

    html = f"""
    <div style="width:100%; border:1px dashed #9ca3af; border-radius:12px; padding:10px; background:transparent;">
      <svg width="100%" height="{height}" viewBox="0 0 {svg_w} {svg_h}" preserveAspectRatio="xMidYMid meet">
        {axes}
        {''.join(ticks)}
        {''.join(bars)}
      </svg>
      <div style="font-size:12px; opacity:.75; margin-top:6px;">Hover bar untuk nilai ω.</div>
    </div>
    """
    components.html(html, height=height + 60, scrolling=False)

# =========================================================
# Sidebar controls
# =========================================================
with st.sidebar:
    st.markdown("### Theme")
    light_mode = st.toggle("Light mode", value=(st.session_state["theme_mode"] == "Light"))
    st.session_state["theme_mode"] = "Light" if light_mode else "Dark"

    st.markdown("---")
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

# =========================================================
# Header
# =========================================================
st.markdown("<div class='app-title'>AHP (Saaty) — Section 3 (GM + Consistency)</div>", unsafe_allow_html=True)
st.markdown(
    """
<span class='pill'>Step 1 Upload P</span>
<span class='pill'>Step 2 Π</span>
<span class='pill'>Step 3 GM</span>
<span class='pill'>Step 4 ω</span>
<span class='pill'>Step 5 P×ω</span>
<span class='pill'>Step 6 λmax</span>
<span class='pill'>Step 7 SI & CR</span>
""",
    unsafe_allow_html=True,
)

# =========================================================
# Stop if no upload
# =========================================================
if uploaded is None:
    st.info("Upload CSV dulu (guna sidebar).")
    st.stop()

# =========================================================
# Read + compute
# =========================================================
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

# =========================================================
# Layout: Tabs (AHP / Export)
# =========================================================
tab1, tab2 = st.tabs(["AHP (Section 3)", "Export"])

with tab1:
    left, right = st.columns([1, 2], gap="large")

    # ---------------- LEFT: summary cards + pastel bar ----------------
    with left:
        st.markdown("<div class='card-dark'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Step 1: Pairwise Matrix</div>", unsafe_allow_html=True)
        st.markdown("<div class='hint'>Raw + numeric display. Reciprocal check included.</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='hint'>m = <b>{m}</b></div>", unsafe_allow_html=True)

        if list(df_num.index) != list(df_num.columns):
            st.warning("Row labels != Column labels (recommended to match, but calculation continues).")

        if recip_ok:
            st.success("Reciprocal OK (pij*pji≈1, diag≈1)")
        else:
            st.warning(f"Reciprocal not perfect (max error={recip_err:.2e})")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card-dark'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Step 4: Weights (ω) — Pastel Bar</div>", unsafe_allow_html=True)
        st.markdown("<div class='hint'>Graph dibuat guna SVG (tak perlukan matplotlib).</div>", unsafe_allow_html=True)
        render_pastel_bar_svg(names, w, height=320)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card-dark'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Step 7: Consistency</div>", unsafe_allow_html=True)
        ok = CR <= 0.10
        st.markdown(
            f"""
<div class="hint">
<b>SI</b> = (λmax − m)/(m − 1) = <b>{SI:.9f}</b><br/>
<b>RI</b> = <b>{ri:.4f}</b><br/>
<b>CR</b> = SI/RI = <b>{CR:.9f}</b>
&nbsp;→&nbsp; {"<span class='ok'>ACCEPTABLE (≤ 0.10)</span>" if ok else "<span class='bad'>NOT OK (> 0.10)</span>"}
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- RIGHT: full step-by-step (UNCHANGED) ----------------
    with right:
        st.markdown("<div class='card-light'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Step 1 — Pairwise comparison matrix P (raw & numeric)</div>", unsafe_allow_html=True)

        c1, c2 = st.columns([1, 1], gap="large")
        with c1:
            st.markdown("**Step 1A: Raw CSV values**")
            st.dataframe(df_raw, use_container_width=True)

        with c2:
            st.markdown("**Step 1B: Numeric P (float)**")
            st.dataframe(df_num.style.format("{:.6g}"), use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card-light'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Step 2 — Row products  Πᵢ = ∏ⱼ pᵢⱼ</div>", unsafe_allow_html=True)
        df_step2 = pd.DataFrame({"Π_i": Pi}, index=names)
        st.dataframe(df_step2.style.format("{:.9f}"), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card-light'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Step 3 — Geometric mean  GMᵢ = (Πᵢ)^(1/m)</div>", unsafe_allow_html=True)
        df_step3 = pd.DataFrame({"GM_i": GM}, index=names)
        st.dataframe(df_step3.style.format("{:.9f}"), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card-light'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Step 4 — Weights  ωᵢ = GMᵢ / ΣGM</div>", unsafe_allow_html=True)
        sumGM = float(np.sum(GM))
        df_step4 = pd.DataFrame({"GM_i": GM, "ΣGM": [sumGM]*m, "ω_i": w}, index=names)
        st.dataframe(
            df_step4.style.format({"GM_i": "{:.9f}", "ΣGM": "{:.9f}", "ω_i": "{:.9f}"}),
            use_container_width=True
        )
        st.write(f"Check: Σω = **{float(np.sum(w)):.9f}** (must be 1.000000000)")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card-light'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Step 5 — Matrix multiplication: (pᵢⱼ × ωⱼ) then row-sum ⇒ (Pω)ᵢ</div>", unsafe_allow_html=True)
        st.caption("Table below shows each cell: pᵢⱼ × ωⱼ (column j scaled by ωⱼ). Then sum across row i gives (Pω)ᵢ.")
        df_mult = pd.DataFrame(mult_table, index=names, columns=names)
        st.dataframe(df_mult.style.format("{:.9f}"), use_container_width=True)
        df_Pw = pd.DataFrame({"(Pω)_i (row-sum)": Pw}, index=names)
        st.dataframe(df_Pw.style.format("{:.9f}"), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card-light'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Step 6 — λᵢ = (Pω)ᵢ / ωᵢ ,  λmax = average(λᵢ)</div>", unsafe_allow_html=True)
        df_step6 = pd.DataFrame({"ω_i": w, "(Pω)_i": Pw, "λ_i": lam}, index=names)
        st.dataframe(
            df_step6.style.format({"ω_i": "{:.9f}", "(Pω)_i": "{:.9f}", "λ_i": "{:.9f}"}),
            use_container_width=True
        )
        st.write(f"**λmax = {lam_max:.9f}**")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card-light'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Step 7 — Consistency: SI and CR</div>", unsafe_allow_html=True)
        ok = CR <= 0.10
        st.markdown(
            f"""
<div>
  <div><b>SI</b> = (λmax − m)/(m − 1) = <b>{SI:.9f}</b></div>
  <div><b>RI</b> = <b>{ri:.4f}</b></div>
  <div><b>CR</b> = SI/RI = <b>{CR:.9f}</b>
    &nbsp;→&nbsp; {"<span class='ok'>ACCEPTABLE (≤ 0.10)</span>" if ok else "<span class='bad'>NOT OK (> 0.10)</span>"}
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown("<div class='card-dark'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Download</div>", unsafe_allow_html=True)
    st.markdown("<div class='hint'>Summary results CSV (Π, GM, ω, Pω, λ).</div>", unsafe_allow_html=True)

    export = pd.DataFrame(
        {"Π_i": Pi, "GM_i": GM, "ω_i": w, "(Pω)_i": Pw, "λ_i": lam},
        index=names
    )
    st.download_button(
        "⬇️ Download summary results CSV",
        data=export.to_csv(index=True).encode("utf-8"),
        file_name="ahp_section3_results.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
