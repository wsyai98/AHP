# app.py
from __future__ import annotations

from io import StringIO
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
import streamlit as st


# ------------------------- Config -------------------------
st.set_page_config(page_title="AHP (Saaty) — CSV Labels + Auto Calculation", layout="wide")

st.title("AHP (Saaty Scale) — Auto Calculation from Your Pairwise Judgements")
st.caption(
    "Upload CSV to detect Alternatives & Criteria (labels). "
    "Then fill pairwise comparisons using Saaty left/equal/right. "
    "App computes weights, consistency (CR), and final ranking."
)

# Random Index (RI) table
RI = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
    11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59
}

SAATY_VALUES = [1, 2, 3, 4, 5, 6, 7, 8, 9]


# ------------------------- Core AHP math -------------------------
def geometric_mean_weights(P: np.ndarray) -> np.ndarray:
    """
    Geometric Mean method:
      GM_i = (∏_j p_ij)^(1/m)
      w_i  = GM_i / Σ GM
    """
    m = P.shape[0]
    prod = np.prod(P, axis=1)
    gm = prod ** (1.0 / m)
    s = gm.sum()
    return gm / (s if s != 0 else 1.0)


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
    Pw = P @ w
    lam = Pw / np.where(w == 0, 1e-18, w)
    lam_max = float(np.mean(lam))
    if m <= 2:
        return lam_max, 0.0, 0.0
    ci = (lam_max - m) / (m - 1)
    ri = RI.get(m, (1.98 * (m - 2) / m))  # approx if m>15
    cr = 0.0 if ri == 0 else ci / ri
    return lam_max, float(ci), float(cr)


def empty_pairwise(names: List[str]) -> np.ndarray:
    n = len(names)
    P = np.ones((n, n), dtype=float)
    return P


def apply_saaty_choice(P: np.ndarray, i: int, j: int, direction: str, value: int) -> None:
    """
    direction:
      - "Left (i more important)"  -> a_ij = value
      - "Equal"                    -> a_ij = 1
      - "Right (j more important)" -> a_ij = 1/value
    Always enforce reciprocity and diagonal=1.
    """
    if i == j:
        P[i, j] = 1.0
        return

    if direction == "Equal":
        a = 1.0
    elif direction.startswith("Left"):
        a = float(value)
    else:  # Right
        a = 1.0 / float(value)

    P[i, j] = a
    P[j, i] = 1.0 / a
    P[i, i] = 1.0
    P[j, j] = 1.0


def matrix_to_df(P: np.ndarray, names: List[str], decimals: int = 4) -> pd.DataFrame:
    df = pd.DataFrame(P, index=names, columns=names)
    return df.round(decimals)


# ------------------------- UI helpers -------------------------
def init_state_pairwise(key: str, names: List[str]) -> None:
    if key not in st.session_state or st.session_state.get(key + "_names") != names:
        st.session_state[key] = empty_pairwise(names)
        st.session_state[key + "_names"] = names


def render_pairwise_form(
    key_prefix: str,
    names: List[str],
    title: str,
    help_text: str,
) -> np.ndarray:
    """
    Renders pairwise comparisons for items in `names`.
    Stores/reads matrix in st.session_state[key_prefix].
    Returns numeric pairwise matrix.
    """
    init_state_pairwise(key_prefix, names)
    P = st.session_state[key_prefix]

    st.subheader(title)
    st.caption(help_text)

    n = len(names)
    if n < 2:
        st.info("Need at least 2 items to compare.")
        return P

    # For each pair (i<j) provide: direction + value
    for i in range(n):
        for j in range(i + 1, n):
            pair_key = f"{key_prefix}_pair_{i}_{j}"

            # Defaults: if existing P has a_ij not 1, infer direction/value
            aij = float(P[i, j])
            if np.isclose(aij, 1.0):
                default_dir = "Equal"
                default_val = 1
            elif aij > 1:
                default_dir = "Left (i more important)"
                # clamp to Saaty 1..9 if user previously used non-Saaty (shouldn't)
                default_val = int(min(9, max(1, round(aij))))
            else:
                default_dir = "Right (j more important)"
                inv = 1.0 / aij
                default_val = int(min(9, max(1, round(inv))))

            c1, c2, c3 = st.columns([2.3, 1.2, 2.3])
            with c1:
                st.markdown(f"**{names[i]}**  vs  **{names[j]}**")
                direction = st.radio(
                    "Direction",
                    options=["Left (i more important)", "Equal", "Right (j more important)"],
                    index=["Left (i more important)", "Equal", "Right (j more important)"].index(default_dir),
                    horizontal=True,
                    key=f"{pair_key}_dir",
                    label_visibility="collapsed",
                )
            with c2:
                value = st.selectbox(
                    "Saaty",
                    options=SAATY_VALUES,
                    index=SAATY_VALUES.index(default_val),
                    key=f"{pair_key}_val",
                    label_visibility="collapsed",
                )
            with c3:
                # Show what will be placed into matrix
                if direction == "Equal":
                    shown = "aᵢⱼ = 1  and  aⱼᵢ = 1"
                elif direction.startswith("Left"):
                    shown = f"aᵢⱼ = {value}  and  aⱼᵢ = 1/{value}"
                else:
                    shown = f"aᵢⱼ = 1/{value}  and  aⱼᵢ = {value}"
                st.write(shown)

            apply_saaty_choice(P, i, j, direction, int(value))

    st.session_state[key_prefix] = P

    st.markdown("**Current pairwise matrix (auto reciprocal):**")
    st.dataframe(matrix_to_df(P, names, decimals=4), use_container_width=True)

    return P


# ------------------------- Sidebar: CSV Upload -------------------------
sample_csv = (
    "Alternative,B1,B2,B3,B4,B5,B6,B7\n"
    "A1,0,0,0,0,0,0,0\n"
    "A2,0,0,0,0,0,0,0\n"
    "A3,0,0,0,0,0,0,0\n"
    "A4,0,0,0,0,0,0,0\n"
    "A5,0,0,0,0,0,0,0\n"
)

with st.sidebar:
    st.header("Step 1 — Upload CSV")
    st.download_button(
        "Download sample CSV (labels only)",
        data=sample_csv,
        file_name="sample_labels.csv",
        mime="text/csv",
        use_container_width=True,
    )
    up = st.file_uploader("Upload your CSV", type=["csv"])
    st.markdown("---")
    st.write("CSV rules:")
    st.markdown(
        "- First column = `Alternative`\n"
        "- Other columns = criteria names (B1..B7 etc.)\n"
        "- Values are **ignored** (labels only) because you use Saaty judgements."
    )

if up is None:
    st.info("Upload a CSV to begin.")
    st.stop()

raw = up.getvalue().decode("utf-8", errors="replace")
df = pd.read_csv(StringIO(raw))

if df.shape[1] < 3:
    st.error("CSV needs at least: Alternative + 2 criteria columns.")
    st.stop()

# Ensure Alternative column exists in col0
cols_lower = [c.strip().lower() for c in df.columns]
if cols_lower[0] != "alternative":
    if "alternative" in cols_lower:
        idx = cols_lower.index("alternative")
        cols = list(df.columns)
        alt_col = cols.pop(idx)
        cols = [alt_col] + cols
        df = df[cols]
    else:
        df = df.rename(columns={df.columns[0]: "Alternative"})

alt_col = df.columns[0]
criteria = list(df.columns[1:])
alternatives = df[alt_col].astype(str).tolist()

st.subheader("Detected labels from CSV")
cL, cR = st.columns([2, 1])
with cL:
    st.write("**Alternatives**")
    st.write(alternatives)
with cR:
    st.write("**Criteria**")
    st.write(criteria)


# ------------------------- Step 2: Criteria pairwise -------------------------
P_crit = render_pairwise_form(
    key_prefix="P_CRITERIA",
    names=criteria,
    title="Step 2 — Pairwise comparison for CRITERIA (Saaty)",
    help_text=(
        "Fill all pairs using Saaty scale (1–9) with Left / Equal / Right. "
        "Diagonal is 1, lower triangle auto reciprocal."
    ),
)

# Compute criteria weights + CR
w_crit = geometric_mean_weights(P_crit)
lam_max_c, ci_c, cr_c = ahp_consistency(P_crit, w_crit)

st.markdown("---")
st.subheader("Step 3 — Criteria weights ω and consistency")
wcrit_df = pd.DataFrame({"Criterion": criteria, "Weight ω": w_crit})
wcrit_df["Rank"] = wcrit_df["Weight ω"].rank(ascending=False, method="dense").astype(int)
wcrit_df = wcrit_df.sort_values(["Rank", "Weight ω"], ascending=[True, False])
st.dataframe(wcrit_df, use_container_width=True)

ok_c = cr_c <= 0.10
st.write(f"λmax = **{lam_max_c:.6f}**, CI = **{ci_c:.6f}**, CR = **{cr_c:.6f}** → "
         f"{'✅ OK (≤ 0.10)' if ok_c else '❌ NOT OK (> 0.10)'}")
if not ok_c:
    st.warning("CR criteria > 0.10. Adjust your judgements (upper pairs) until CR ≤ 0.10.")


# ------------------------- Step 4: Alternatives pairwise per criterion -------------------------
st.markdown("---")
st.subheader("Step 4 — Pairwise comparison for ALTERNATIVES under each criterion (Saaty)")
st.caption(
    "For each criterion, compare Alternatives using the same Saaty left/equal/right. "
    "App will compute local weights and local CR per criterion."
)

local_weights: Dict[str, np.ndarray] = {}
local_cr: Dict[str, float] = {}

for k, crit_name in enumerate(criteria):
    with st.expander(f"Fill pairwise for alternatives under: {crit_name}", expanded=(k == 0)):
        P_alt = render_pairwise_form(
            key_prefix=f"P_ALT_{crit_name}",
            names=alternatives,
            title=f"{crit_name}: Alternatives pairwise matrix",
            help_text="Compare alternatives (A1 vs A2, etc.) using Saaty scale. Auto reciprocal is enforced.",
        )
        w_alt = geometric_mean_weights(P_alt)
        lam_max_a, ci_a, cr_a = ahp_consistency(P_alt, w_alt)

        local_weights[crit_name] = w_alt
        local_cr[crit_name] = cr_a

        show = pd.DataFrame({"Alternative": alternatives, f"Local weight under {crit_name}": w_alt})
        show["Rank"] = show[f"Local weight under {crit_name}"].rank(ascending=False, method="dense").astype(int)
        show = show.sort_values(["Rank", f"Local weight under {crit_name}"], ascending=[True, False])
        st.dataframe(show, use_container_width=True)

        ok_a = cr_a <= 0.10
        st.write(f"Local CR for **{crit_name}**: **{cr_a:.6f}** → "
                 f"{'✅ OK (≤ 0.10)' if ok_a else '❌ NOT OK (> 0.10)'}")
        if not ok_a:
            st.warning(f"CR for {crit_name} > 0.10. Revise judgements for this criterion.")


# ------------------------- Step 5: Final synthesis -------------------------
st.markdown("---")
st.subheader("Step 5 — Final ranking (AHP synthesis)")

# Build local weight matrix (alternatives x criteria)
LW = np.column_stack([local_weights[c] for c in criteria])  # shape: n_alt x n_crit
wc = w_crit.reshape(-1)  # n_crit

scores = LW @ wc  # n_alt
final = pd.DataFrame({"Alternative": alternatives, "Score": scores})
final["Rank"] = final["Score"].rank(ascending=False, method="dense").astype(int)
final = final.sort_values(["Rank", "Score"], ascending=[True, False])

st.dataframe(final, use_container_width=True)

st.caption("Score(Aᵢ) = Σ_k  (criteria_weight_k × local_weight_of_Aᵢ_under_criterion_k)")

# Show local CR summary
with st.expander("Consistency summary (CR)"):
    rows = [{"Matrix": "CRITERIA", "CR": cr_c, "OK (≤0.10)": cr_c <= 0.10}]
    for c in criteria:
        rows.append({"Matrix": f"ALT under {c}", "CR": float(local_cr[c]), "OK (≤0.10)": float(local_cr[c]) <= 0.10})
    st.dataframe(pd.DataFrame(rows), use_container_width=True)


# ------------------------- Downloads -------------------------
st.markdown("---")
st.subheader("Download outputs")

# Criteria weights
st.download_button(
    "Download criteria weights CSV",
    data=wcrit_df.to_csv(index=False),
    file_name="criteria_weights.csv",
    mime="text/csv",
    use_container_width=True,
)

# Local weights (alts x criteria)
local_df = pd.DataFrame(LW, columns=criteria)
local_df.insert(0, "Alternative", alternatives)
st.download_button(
    "Download local weights CSV",
    data=local_df.to_csv(index=False),
    file_name="local_weights.csv",
    mime="text/csv",
    use_container_width=True,
)

# Final ranking
st.download_button(
    "Download final ranking CSV",
    data=final.to_csv(index=False),
    file_name="final_ranking.csv",
    mime="text/csv",
    use_container_width=True,
)
