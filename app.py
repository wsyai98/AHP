# app.py
from __future__ import annotations

import math
from dataclasses import dataclass
from io import StringIO
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import streamlit as st


# --------------------------- Page config ---------------------------
st.set_page_config(
    page_title="AHP Auto Calculator (CSV → Pairwise → Weights → Consistency)",
    layout="wide",
)

st.title("AHP Auto Calculator (CSV upload)")
st.caption(
    "CSV: first column = Alternative, other columns = criteria (numeric). "
    "App auto-builds pairwise for alternatives using ratios, and you fill pairwise for criteria."
)


# --------------------------- Helpers ---------------------------
RI: Dict[int, float] = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
    11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59
}

def parse_ratio(x) -> float:
    """
    Parse:
      - numbers (int/float)
      - strings: "3", "0.5", "1/3"
    Returns float or raises ValueError.
    """
    if pd.isna(x):
        raise ValueError("Empty cell")
    if isinstance(x, (int, float, np.integer, np.floating)):
        v = float(x)
        if not np.isfinite(v) or v <= 0:
            raise ValueError("Non-positive / invalid number")
        return v

    s = str(x).strip()
    if s == "":
        raise ValueError("Empty cell")

    if "/" in s:
        parts = s.split("/")
        if len(parts) != 2:
            raise ValueError(f"Bad fraction: {s}")
        num = float(parts[0].strip())
        den = float(parts[1].strip())
        if den == 0:
            raise ValueError("Denominator zero")
        v = num / den
    else:
        v = float(s)

    if not np.isfinite(v) or v <= 0:
        raise ValueError("Non-positive / invalid number")
    return v


def geometric_mean_weights(P: np.ndarray) -> np.ndarray:
    """
    Geometric Mean method:
      Π_i = ∏_j p_ij
      GM_i = (Π_i)^(1/m)
      w_i = GM_i / Σ GM
    Matches the standard approximate method in AHP literature. :contentReference[oaicite:2]{index=2}
    """
    m = P.shape[0]
    prod = np.prod(P, axis=1)
    gm = prod ** (1.0 / m)
    s = gm.sum()
    return gm / (s if s != 0 else 1.0)


def matvec(P: np.ndarray, w: np.ndarray) -> np.ndarray:
    return P @ w


def ahp_consistency(P: np.ndarray, w: np.ndarray) -> Tuple[float, float, float]:
    """
    Consistency:
      Pw
      λ_i = (Pw)_i / w_i
      λmax = average(λ_i)
      CI = (λmax - m)/(m - 1)
      CR = CI / RI
    """
    m = P.shape[0]
    Pw = matvec(P, w)
    lam = Pw / np.where(w == 0, 1e-18, w)
    lam_max = float(np.mean(lam))
    if m <= 2:
        return lam_max, 0.0, 0.0
    ci = (lam_max - m) / (m - 1)
    ri = RI.get(m, (1.98 * (m - 2) / m))  # fallback approx for m>15
    cr = 0.0 if ri == 0 else ci / ri
    return lam_max, float(ci), float(cr)


def build_pairwise_from_values(values: np.ndarray, criterion_type: str) -> np.ndarray:
    """
    Build pairwise matrix for alternatives from raw numeric values.
      Benefit: a_ij = x_i / x_j
      Cost:    a_ij = x_j / x_i
    This creates an inverse-symmetric consistent matrix if all x > 0.
    """
    x = values.astype(float)
    if np.any(~np.isfinite(x)) or np.any(x <= 0):
        raise ValueError("All criterion values must be positive numbers (>0) to build ratio-based pairwise matrices.")
    n = len(x)
    P = np.ones((n, n), dtype=float)
    for i in range(n):
        for j in range(n):
            if i == j:
                P[i, j] = 1.0
            else:
                if criterion_type.lower().startswith("benefit"):
                    P[i, j] = x[i] / x[j]
                else:  # cost
                    P[i, j] = x[j] / x[i]
    return P


def make_blank_criteria_pairwise(criteria: List[str]) -> pd.DataFrame:
    m = len(criteria)
    df = pd.DataFrame(np.ones((m, m), dtype=object), index=criteria, columns=criteria)
    # Use empty strings above diagonal to encourage user input (but keep diagonal = 1).
    for i in range(m):
        for j in range(m):
            if i == j:
                df.iat[i, j] = "1"
            elif i < j:
                df.iat[i, j] = ""  # user fills
            else:
                df.iat[i, j] = ""  # auto later
    return df


def df_to_numeric_pairwise(df: pd.DataFrame) -> np.ndarray:
    """
    Convert editable DF into numeric pairwise matrix.
    Rules:
      - diagonal forced to 1
      - for i<j: parse user cell
      - for i>j: reciprocal of (j,i)
    """
    crit = list(df.index)
    m = len(crit)
    P = np.ones((m, m), dtype=float)

    for i in range(m):
        for j in range(m):
            if i == j:
                P[i, j] = 1.0
            elif i < j:
                cell = df.iat[i, j]
                v = parse_ratio(cell)
                P[i, j] = v
                P[j, i] = 1.0 / v
    return P


# --------------------------- Sample CSV ---------------------------
sample_csv = (
    "Alternative,Cost,Quality,Delivery\n"
    "A1,200,8,4\n"
    "A2,250,7,5\n"
    "A3,300,9,6\n"
    "A4,220,8,4\n"
    "A5,180,6,7\n"
)

with st.sidebar:
    st.header("Step 1 — Upload CSV")
    st.download_button(
        "Download sample CSV",
        data=sample_csv,
        file_name="sample_ahp.csv",
        mime="text/csv",
        use_container_width=True,
    )
    up = st.file_uploader("Upload your CSV", type=["csv"])


# --------------------------- Step 1: Load CSV ---------------------------
if up is None:
    st.info("Upload a CSV (or download the sample) to start.")
    st.stop()

raw_text = up.getvalue().decode("utf-8", errors="replace")
df = pd.read_csv(StringIO(raw_text))

if df.shape[1] < 3:
    st.error("CSV needs at least: Alternative + 2 criteria columns.")
    st.stop()

# Ensure first column is Alternative
if df.columns[0].strip().lower() != "alternative":
    # try find
    cols_lower = [c.strip().lower() for c in df.columns]
    if "alternative" in cols_lower:
        idx = cols_lower.index("alternative")
        cols = list(df.columns)
        # move Alternative to first
        alt = cols.pop(idx)
        cols = [alt] + cols
        df = df[cols]
    else:
        df = df.rename(columns={df.columns[0]: "Alternative"})

alt_col = df.columns[0]
criteria_cols = list(df.columns[1:])
alts = df[alt_col].astype(str).tolist()

st.subheader("Detected decision matrix (from CSV)")
st.dataframe(df, use_container_width=True)

# Validate numeric criteria
bad_cols = []
for c in criteria_cols:
    if not pd.to_numeric(df[c], errors="coerce").notna().all():
        bad_cols.append(c)
if bad_cols:
    st.error(
        "These criteria columns contain non-numeric / missing values (please clean the CSV): "
        + ", ".join(bad_cols)
    )
    st.stop()

# Force numeric
for c in criteria_cols:
    df[c] = pd.to_numeric(df[c], errors="raise")


# --------------------------- Step 2: Criterion types ---------------------------
st.subheader("Step 2 — Set criterion type (Benefit / Cost)")
st.caption("This controls how the alternatives pairwise matrix is auto-generated from your CSV values.")

colA, colB = st.columns([2, 1])
with colA:
    types_df = pd.DataFrame(
        {
            "Criterion": criteria_cols,
            "Type": ["Cost" if "cost" in c.lower() else "Benefit" for c in criteria_cols],
        }
    )
    edited_types = st.data_editor(
        types_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Type": st.column_config.SelectboxColumn(
                "Type",
                options=["Benefit", "Cost"],
                required=True,
            )
        },
        key="types_editor",
    )
crit_types = dict(zip(edited_types["Criterion"], edited_types["Type"]))

with colB:
    st.write("Quick notes")
    st.markdown(
        "- **Benefit**: bigger value = better\n"
        "- **Cost**: smaller value = better\n"
        "- Values must be **> 0** for ratio-based pairwise."
    )


# --------------------------- Step 3: Criteria pairwise input ---------------------------
st.subheader("Step 3 — Pairwise comparison for CRITERIA (fill upper triangle only)")
st.caption("Enter values like 3, 0.5, 1/3. Diagonal is 1. Lower triangle is auto reciprocal.")

if "crit_pw_df" not in st.session_state or st.session_state.get("crit_pw_cols") != criteria_cols:
    st.session_state["crit_pw_df"] = make_blank_criteria_pairwise(criteria_cols)
    st.session_state["crit_pw_cols"] = criteria_cols

crit_pw_df = st.session_state["crit_pw_df"]

edited_pw = st.data_editor(
    crit_pw_df,
    use_container_width=True,
    key="crit_pw_editor",
)

# Update session state
st.session_state["crit_pw_df"] = edited_pw

compute_btn = st.button("✅ Compute AHP (criteria weights + alternative ranking)", type="primary")


# --------------------------- Compute ---------------------------
if not compute_btn:
    st.stop()

# Convert criteria pairwise to numeric
try:
    P_criteria = df_to_numeric_pairwise(edited_pw)
except Exception as e:
    st.error(f"Criteria pairwise matrix has invalid entry: {e}")
    st.stop()

m = len(criteria_cols)

# Step 4: Criteria weights (GM)
w_criteria = geometric_mean_weights(P_criteria)
lam_max_c, ci_c, cr_c = ahp_consistency(P_criteria, w_criteria)

st.divider()
st.subheader("Step 4 — Criteria weights ω (Geometric Mean method)")
wcrit_table = pd.DataFrame(
    {"Criterion": criteria_cols, "Weight ω": w_criteria}
).sort_values("Weight ω", ascending=False)
st.dataframe(wcrit_table, use_container_width=True)

st.subheader("Step 5 — Consistency (Criteria matrix)")
ok = cr_c <= 0.10
st.write(f"m = {m}")
st.write(f"λmax = {lam_max_c:.6f}")
st.write(f"CI = {ci_c:.6f}")
st.write(f"CR = {cr_c:.6f}  →  {'✅ ACCEPTABLE (≤ 0.10)' if ok else '❌ NOT OK (> 0.10)'}")

if not ok:
    st.warning("CR > 0.10. Revise the upper triangle values of the criteria pairwise matrix and recompute.")

# --------------------------- Alternatives: auto pairwise per criterion ---------------------------
st.divider()
st.subheader("Step 6 — Auto pairwise for ALTERNATIVES (from CSV ratios) + local weights")

local_weights = {}
local_cr = {}

for c in criteria_cols:
    P_alt = build_pairwise_from_values(df[c].to_numpy(), crit_types[c])
    w_alt = geometric_mean_weights(P_alt)
    lam, ci, cr = ahp_consistency(P_alt, w_alt)  # should be ~0 for ratio-constructed matrices
    local_weights[c] = w_alt
    local_cr[c] = cr

# Show local weights table
local_df = pd.DataFrame(local_weights, index=alts)
local_df.insert(0, "Alternative", alts)
st.dataframe(local_df.set_index("Alternative"), use_container_width=True)

with st.expander("Show consistency (CR) for each alternative-pairwise matrix"):
    cr_rows = [{"Criterion": c, "Type": crit_types[c], "CR": float(local_cr[c])} for c in criteria_cols]
    st.dataframe(pd.DataFrame(cr_rows).sort_values("CR", ascending=False), use_container_width=True)
    st.caption("Because we build pairwise by exact ratios from data, CR is usually ~ 0.")

# --------------------------- Step 7: Synthesis (overall score) ---------------------------
st.divider()
st.subheader("Step 7 — Synthesis: overall ranking")
# overall score = Σ (criteria_weight * local_weight_alt_under_criterion)
Wc = np.array([w_criteria[criteria_cols.index(c)] for c in criteria_cols], dtype=float)
scores = np.zeros(len(alts), dtype=float)

for j, c in enumerate(criteria_cols):
    scores += Wc[j] * np.array(local_weights[c], dtype=float)

result = pd.DataFrame({"Alternative": alts, "Overall score": scores})
result["Rank"] = result["Overall score"].rank(ascending=False, method="dense").astype(int)
result = result.sort_values(["Rank", "Overall score"], ascending=[True, False])

st.dataframe(result, use_container_width=True)

# --------------------------- Downloads ---------------------------
st.divider()
st.subheader("Download outputs")
out1 = wcrit_table.reset_index(drop=True)
out2 = result.reset_index(drop=True)
out3 = local_df.reset_index(drop=True)

st.download_button(
    "Download criteria weights (CSV)",
    data=out1.to_csv(index=False),
    file_name="criteria_weights.csv",
    mime="text/csv",
    use_container_width=True,
)
st.download_button(
    "Download local weights (alternatives x criteria) (CSV)",
    data=out3.to_csv(index=False),
    file_name="local_weights.csv",
    mime="text/csv",
    use_container_width=True,
)
st.download_button(
    "Download final ranking (CSV)",
    data=out2.to_csv(index=False),
    file_name="final_ranking.csv",
    mime="text/csv",
    use_container_width=True,
)

st.caption(
    "Method references: Geometric-mean weights + consistency steps follow the standard AHP workflow "
    "(see the stepwise GM + λmax/CI/CR example). :contentReference[oaicite:3]{index=3} "
    "Consistency checking concept (CI/CR threshold 0.10) matches AHP procedure descriptions. :contentReference[oaicite:4]{index=4}"
)
