# app.py
import numpy as np
import pandas as pd
import streamlit as st

# ---------------- Page config ----------------
st.set_page_config(page_title="AHP Step-by-Step (Pastel Purple)", layout="wide")

# ---------------- Pastel purple theme ----------------
st.markdown(
    """
<style>
  .stApp {
    background: linear-gradient(180deg, #0b0b12 0%, #120a2a 40%, #f3e8ff 130%) !important;
  }
  [data-testid="stSidebar"] {
    background: rgba(243, 232, 255, 0.10) !important;
    backdrop-filter: blur(8px);
    border-right: 1px solid rgba(216, 180, 254, 0.25);
  }
  .block-container { padding-top: 1.2rem; }
  h1, h2, h3, h4 { color: #f5f3ff; }
  p, li, label, div { color: #e9d5ff; }
  .card {
    background: rgba(17, 24, 39, 0.55);
    border: 1px solid rgba(216, 180, 254, 0.25);
    border-radius: 16px;
    padding: 16px;
  }
  .card-light {
    background: rgba(255, 255, 255, 0.78);
    border: 1px solid rgba(216, 180, 254, 0.45);
    border-radius: 16px;
    padding: 16px;
    color: #111827 !important;
  }
  .card-light * { color: #111827 !important; }
  .pill {
    display:inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(168, 85, 247, 0.16);
    border: 1px solid rgba(216, 180, 254, 0.35);
    color: #f5f3ff;
    font-size: 12px;
    margin-right: 6px;
  }
  .stButton button {
    background: #a855f7 !important;
    border: 1px solid #7c3aed !important;
    color: white !important;
    border-radius: 12px !important;
    padding: 0.6rem 0.9rem !important;
  }
  .stButton button:hover { filter: brightness(0.96); }
  .stDataFrame { border-radius: 12px; overflow: hidden; }
  code { color: #111827 !important; background: rgba(255,255,255,0.75); padding: 2px 6px; border-radius: 8px; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("AHP Step-by-Step (Pastel Purple) — ikut paper")

# ---------------- Helpers (AHP by paper) ----------------
# Random Index (Saaty) typical table for m=1..15
RI_TABLE = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41,
    9: 1.45, 10: 1.49, 11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59
}

def safe_float(x, default=np.nan):
    try:
        v = float(x)
        return v
    except Exception:
        return default

def build_pairwise_matrix(criteria, pair_inputs):
    """
    criteria: list[str]
    pair_inputs: dict[(i,j)] = p_ij for i<j
    return P (m x m) reciprocal matrix with diag=1
    """
    m = len(criteria)
    P = np.ones((m, m), dtype=float)
    for i in range(m):
        for j in range(i + 1, m):
            pij = float(pair_inputs[(i, j)])
            P[i, j] = pij
            P[j, i] = 1.0 / pij
    return P

def ahp_weights_geometric_mean(P):
    """
    Paper scheme:
      Π_i = ∏_j p_ij
      g_i = (Π_i)^(1/m)
      ω_i = g_i / ∑ g_i
    """
    m = P.shape[0]
    # product of each row
    Pi = np.prod(P, axis=1)
    gi = Pi ** (1.0 / m)
    w = gi / np.sum(gi)
    return Pi, gi, w

def ahp_lambda_max_approx(P, w):
    """
    Approx λmax from paper:
      compute y = P w
      λ_i = y_i / w_i
      λmax = average(λ_i)
    """
    y = P @ w
    lam_i = y / np.maximum(w, 1e-16)
    lam_max = float(np.mean(lam_i))
    return y, lam_i, lam_max

def consistency_metrics(lam_max, m):
    """
    SI = (λmax - m)/(m-1)
    S  = SI/SA  (SA = random index)
    Accept if S <= 0.1
    """
    if m <= 2:
        return 0.0, 0.0, RI_TABLE.get(m, 0.0), True

    SI = (lam_max - m) / (m - 1)

    # SA / RI
    SA = RI_TABLE.get(m, None)
    if SA is None:
        # Paper mentions rough approximation for m>15:
        # SA = 1.98*(m-2)/m  (they note it's slightly larger than table)
        SA = 1.98 * (m - 2) / m

    S = SI / (SA if SA != 0 else 1e-16)
    ok = (S <= 0.10)
    return float(SI), float(S), float(SA), ok

def normalize_for_weighted_sum(df_vals, crit_types):
    """
    Simple ranking after AHP weights (optional):
      Benefit: x / max
      Cost:    min / x
    """
    norm = df_vals.copy().astype(float)
    for c in norm.columns:
        col = norm[c].values.astype(float)
        if crit_types[c] == "Cost":
            mn = np.nanmin(col)
            norm[c] = mn / np.maximum(col, 1e-16)
        else:
            mx = np.nanmax(col)
            norm[c] = col / (mx if mx != 0 else 1.0)
    return norm

# ---------------- Sidebar: Upload ----------------
with st.sidebar:
    st.markdown("### Upload CSV")
    up = st.file_uploader("CSV (first column = Alternative)", type=["csv"])
    st.markdown("---")
    st.markdown("### Nota ringkas")
    st.write("AHP perlukan **pairwise comparison** untuk criteria (skala Saaty).")

# ---------------- Main: Load data ----------------
if up is None:
    st.markdown('<div class="card">Upload CSV dulu. Lepas tu sistem auto keluar nama criteria dan form pairwise AHP.</div>', unsafe_allow_html=True)
    st.stop()

df = pd.read_csv(up)

# Fix column name for first column
cols = list(df.columns)
if len(cols) < 2:
    st.error("CSV mesti ada sekurang-kurangnya 2 kolum: Alternative + at least 1 criterion.")
    st.stop()

if cols[0].strip().lower() != "alternative":
    # rename first column to Alternative
    df = df.rename(columns={cols[0]: "Alternative"})
criteria = [c for c in df.columns if c != "Alternative"]

# ensure numeric for criteria
df_crit = df[criteria].apply(pd.to_numeric, errors="coerce")

st.markdown('<div class="card-light"><b>Detected criteria:</b> ' +
            " ".join([f'<span class="pill">{c}</span>' for c in criteria]) +
            "</div>", unsafe_allow_html=True)

colL, colR = st.columns([1, 1], gap="large")

with colL:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Step 0: Decision Matrix (input)")
    st.dataframe(df, use_container_width=True, height=260)

    st.subheader("Step 1: Set criteria type (optional for final ranking)")
    crit_types = {}
    for c in criteria:
        crit_types[c] = st.selectbox(f"{c} type", ["Benefit", "Cost"], index=0, key=f"type_{c}")
    st.markdown("</div>", unsafe_allow_html=True)

with colR:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Step 2: Pairwise comparison (Saaty scale)")

    st.caption("Untuk setiap pasangan (Ci, Cj): pilih siapa lebih penting + tahap kepentingan. "
               "Matrix akan auto jadi reciprocal (p_ji = 1/p_ij) dan diagonal = 1.")

    intensity_opts = {
        1: "1 (Equal)",
        2: "2 (Between)",
        3: "3 (Moderate)",
        4: "4 (Between)",
        5: "5 (Strong)",
        6: "6 (Between)",
        7: "7 (Very strong)",
        8: "8 (Between)",
        9: "9 (Extreme)",
    }

    pair_inputs = {}
    m = len(criteria)

    if m == 1:
        st.info("Hanya 1 criteria → weight = 1.")
    else:
        for i in range(m):
            for j in range(i + 1, m):
                c_i, c_j = criteria[i], criteria[j]
                with st.container(border=True):
                    st.markdown(f"**{c_i} vs {c_j}**")
                    who = st.radio(
                        "Which is more important?",
                        options=[c_i, c_j],
                        horizontal=True,
                        key=f"who_{i}_{j}",
                    )
                    inten = st.select_slider(
                        "Intensity",
                        options=list(intensity_opts.keys()),
                        value=3,
                        format_func=lambda k: intensity_opts[k],
                        key=f"inten_{i}_{j}",
                    )
                    # set p_ij
                    if who == c_i:
                        pij = float(inten)
                    else:
                        pij = 1.0 / float(inten)
                    pair_inputs[(i, j)] = pij

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Compute AHP ----------------
st.markdown("---")
st.subheader("AHP Results (Step-by-Step)")

if len(criteria) == 1:
    P = np.array([[1.0]])
    Pi = np.array([1.0])
    gi = np.array([1.0])
    w = np.array([1.0])
    y = np.array([1.0])
    lam_i = np.array([1.0])
    lam_max = 1.0
    SI, S, SA, ok = 0.0, 0.0, 0.0, True
else:
    P = build_pairwise_matrix(criteria, pair_inputs)
    Pi, gi, w = ahp_weights_geometric_mean(P)
    y, lam_i, lam_max = ahp_lambda_max_approx(P, w)
    SI, S, SA, ok = consistency_metrics(lam_max, len(criteria))

tab1, tab2, tab3, tab4 = st.tabs(["Step 3: Matrix P", "Step 4: Weights ω", "Step 5: Consistency", "Step 6: Optional Ranking"])

with tab1:
    st.markdown('<div class="card-light">', unsafe_allow_html=True)
    st.markdown("**Pairwise comparison matrix**  \(P=[p_{ij}]\)  (reciprocal, diagonal = 1).")
    dfP = pd.DataFrame(P, index=criteria, columns=criteria)
    st.dataframe(dfP.style.format("{:.4f}"), use_container_width=True, height=320)
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="card-light">', unsafe_allow_html=True)
    st.markdown("Mengikut paper (geometric mean):")
    st.latex(r"\Pi_i=\prod_{j=1}^{m} p_{ij},\quad g_i=\sqrt[m]{\Pi_i},\quad \omega_i=\frac{g_i}{\sum_{k=1}^{m} g_k}")
    out = pd.DataFrame({
        "Criterion": criteria,
        "Pi (row product)": Pi,
        "gi (m-th root)": gi,
        "weight ωi": w,
    })
    st.dataframe(out.style.format({"Pi (row product)": "{:.6f}", "gi (m-th root)": "{:.6f}", "weight ωi": "{:.6f}"}),
                 use_container_width=True, height=280)
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="card-light">', unsafe_allow_html=True)
    st.markdown("Anggaran \(\\lambda_{max}\) ikut paper:")
    st.latex(r"y=P\omega,\quad \lambda_i=\frac{y_i}{\omega_i},\quad \lambda_{max}=\frac{1}{m}\sum_{i=1}^{m}\lambda_i")
    cons = pd.DataFrame({
        "Criterion": criteria,
        "(Pω)i": y,
        "ωi": w,
        "λi=(Pω)i/ωi": lam_i,
    })
    st.dataframe(cons.style.format({"(Pω)i": "{:.6f}", "ωi": "{:.6f}", "λi=(Pω)i/ωi": "{:.6f}"}),
                 use_container_width=True, height=260)

    st.markdown("Consistency index & ratio:")
    st.latex(r"SI=\frac{\lambda_{max}-m}{m-1},\quad S=\frac{SI}{SA}")
    st.write(f"m = **{len(criteria)}**")
    st.write(f"λmax = **{lam_max:.6f}**")
    st.write(f"SI = **{SI:.6f}**")
    st.write(f"SA (Random Index) = **{SA:.6f}**")
    st.write(f"S (Consistency Ratio) = **{S:.6f}**")

    if ok:
        st.success("✅ Consistent (S ≤ 0.10)")
    else:
        st.warning("⚠️ Not consistent (S > 0.10). Cuba adjust pairwise values sampai S ≤ 0.10.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="card-light">', unsafe_allow_html=True)
    st.markdown("Ini **optional**: guna weight AHP untuk ranking alternatif secara Weighted Sum (simple).")
    st.caption("Normalization: Benefit = x/max, Cost = min/x. Lepas tu Score = Σ ωj * normalized_ij.")

    norm = normalize_for_weighted_sum(df_crit, crit_types)
    score = (norm.values @ w.reshape(-1, 1)).flatten()

    res = pd.DataFrame({
        "Alternative": df["Alternative"].astype(str),
        "Score": score
    }).sort_values("Score", ascending=False).reset_index(drop=True)
    res["Rank"] = np.arange(1, len(res) + 1)

    st.subheader("Ranking")
    st.dataframe(res.style.format({"Score": "{:.6f}"}), use_container_width=True, height=280)

    st.subheader("Normalized matrix (preview)")
    preview = norm.copy()
    preview.insert(0, "Alternative", df["Alternative"].astype(str))
    st.dataframe(preview.style.format("{:.6f}"), use_container_width=True, height=260)
    st.markdown("</div>", unsafe_allow_html=True)
