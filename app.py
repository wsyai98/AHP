# app.py
import base64
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="SYAI-Rank • AHP", layout="wide")
APP_DIR = Path(__file__).resolve().parent

# ---------- Single source of truth for the sample CSV ----------
def load_sample_csv_text() -> str:
    p = Path("/mnt/data/sample (1).csv")
    if p.exists():
        for enc in ("utf-8", "latin-1"):
            try:
                return p.read_text(encoding=enc)
            except Exception:
                pass
    # Fallback tiny demo
    return (
        "Alternative,Cost,Quality,Delivery\n"
        "A1,200,8,4\n"
        "A2,250,7,5\n"
        "A3,300,9,6\n"
        "A4,220,8,4\n"
        "A5,180,6,7\n"
    )

SAMPLE_CSV = load_sample_csv_text()

# ---------- IMPORTANT: escape CSV for JS template literal safely ----------
def escape_for_js_template_literal(s: str) -> str:
    # Avoid breaking: backslashes, backticks, and ${ interpolation
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

SAFE_SAMPLE_CSV = escape_for_js_template_literal(SAMPLE_CSV)

# ---------- base page background (purple pastel) ----------
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
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------- HTML APP -------------------------------
html = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>SYAI-Rank • AHP</title>

<style>
  :root{
    /* PURPLE PASTEL THEME */
    --bg1:#0b0b10;
    --bg2:#141227;
    --lav:#f3e8ff;
    --lav2:#e9d5ff;
    --vio:#c4b5fd;
    --vio2:#a78bfa;
    --vio3:#8b5cf6;
    --ink:#0f172a;
    --text:#f8fafc;

    --cardDark: rgba(18,16,35,.78);
    --cardLight: rgba(255,255,255,.78);

    --bdDark:#2c2a45;
    --bdLight:#e5e7eb;

    --btn:#a78bfa;
    --btnBd:#8b5cf6;
  }

  *{box-sizing:border-box}
  html,body{height:100%;margin:0}
  body{font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial}

  body.theme-dark{
    color:var(--text);
    background: radial-gradient(1200px 600px at 20% 0%, rgba(167,139,250,.25), transparent 55%),
                radial-gradient(900px 500px at 85% 10%, rgba(196,181,253,.22), transparent 60%),
                linear-gradient(180deg, var(--bg1) 0%, var(--bg2) 55%, rgba(243,232,255,.28) 140%);
  }
  body.theme-light{
    color:#111;
    background: radial-gradient(1100px 520px at 15% 0%, rgba(167,139,250,.25), transparent 55%),
                radial-gradient(900px 460px at 85% 10%, rgba(196,181,253,.20), transparent 60%),
                linear-gradient(180deg, #fbfaff 0%, #f8fafc 55%, var(--lav) 140%);
  }

  .container{max-width:1200px;margin:24px auto;padding:0 16px}
  .header{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
  .title{
    font-weight:900;
    font-size:28px;
    letter-spacing:.3px;
    color: var(--lav);
    text-shadow: 0 10px 28px rgba(167,139,250,.22);
  }
  body.theme-light .title{color:#111;text-shadow:none}

  .row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
  .btn{
    display:inline-flex;align-items:center;gap:8px;
    padding:10px 14px;border-radius:14px;
    border:1px solid var(--btnBd);
    background: linear-gradient(180deg, var(--btn) 0%, var(--vio2) 100%);
    color:#fff;cursor:pointer;
    box-shadow: 0 12px 24px rgba(139,92,246,.18);
    text-decoration:none;
    font-weight:800;
  }
  .btn:hover{filter:brightness(0.98); transform: translateY(-.5px)}
  .toggle{
    padding:8px 12px;border-radius:14px;
    border:1px solid var(--bdDark);
    background: rgba(255,255,255,.06);
    color:#eee;cursor:pointer;
    font-weight:800;
  }
  body.theme-light .toggle{background:#fff;color:#111;border-color:#cbd5e1}

  .tabs{display:flex;gap:8px;margin:12px 0;position:relative;z-index:10;flex-wrap:wrap}
  .tab{
    padding:10px 14px;border-radius:14px;
    border:1px solid rgba(196,181,253,.35);
    background: rgba(255,255,255,.06);
    color:#e5e7eb;cursor:pointer;
    font-weight:900;
  }
  .tab.active{
    background: linear-gradient(180deg, rgba(167,139,250,.95), rgba(139,92,246,.95));
    border-color: rgba(196,181,253,.9);
    color:#fff;
  }
  body.theme-light .tab{background:#ede9fe;color:#111;border-color:#c4b5fd}

  .grid{display:grid;gap:16px;grid-template-columns:1fr}
  @media (min-width:1024px){.grid{grid-template-columns:1fr 2fr}}

  .card{
    border-radius:18px;padding:18px;
    border:1px solid var(--bdLight);
    backdrop-filter: blur(8px);
  }
  .card.dark{background:var(--cardDark);color:#e5e7eb;border-color:var(--bdDark)}
  .card.light{background:var(--cardLight);color:#111;border-color:var(--bdLight)}
  body.theme-light .card.dark{background:#fff;color:#111;border-color:#e5e7eb}

  .section-title{
    font-weight:900;font-size:18px;margin-bottom:12px;
    color: var(--lav2);
  }
  body.theme-light .section-title{color:#4c1d95}

  .label{display:block;font-size:12px;opacity:.9;margin-bottom:4px;font-weight:800}
  input[type="number"], select{
    width:100%;
    padding:10px 12px;border-radius:12px;
    border:1px solid #ddd;background:#fbfaff;color:#111;
  }
  .hint{font-size:12px;opacity:.85}
  .mini{font-size:12px;opacity:.92;line-height:1.45}

  .table-wrap{overflow:auto;max-height:460px}
  table{width:100%;border-collapse:collapse;font-size:14px;color:#111}
  th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #e5e7eb}
  th{background:rgba(243,232,255,.65); position:sticky; top:0}

  .grid2{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(220px,1fr))}

  /* Tooltip */
  #tt{
    position:fixed;display:none;pointer-events:none;background:#fff;color:#111;
    padding:6px 8px;border-radius:10px;font-size:12px;
    box-shadow:0 12px 24px rgba(0,0,0,.18);
    border:1px solid #e5e7eb;z-index:9999
  }

  .pill{
    display:inline-flex;align-items:center;gap:8px;
    padding:6px 10px;border-radius:999px;
    border:1px solid #c4b5fd;
    background: rgba(237,233,254,.7);
    margin:0 6px 6px 0;font-size:12px;color:#111;
    font-weight:900;
  }
</style>
</head>

<body class="theme-dark">
<div class="container">
  <div class="header">
    <div class="title">SYAI-Rank • AHP (Pastel Purple)</div>
    <div class="row">
      <a class="btn" id="downloadSample">⬇️ Download Sample</a>
      <button class="btn" id="loadSample">📄 Load Sample</button>
      <button class="toggle" id="themeToggle">🌙 Dark</button>
    </div>
  </div>

  <div class="tabs">
    <button type="button" class="tab active" id="tabAHP">AHP (Step-by-Step)</button>
    <button type="button" class="tab" id="tabSYAI">SYAI (use AHP weights later)</button>
  </div>

  <!-- ================= TAB: AHP ================= -->
  <div id="viewAHP">
    <div class="grid">
      <div>
        <div class="card dark">
          <div class="section-title">Step 1: Upload CSV (detect criteria)</div>
          <label for="csvAHP" class="btn">📤 Choose CSV</label>
          <input id="csvAHP" type="file" accept=".csv" style="display:none"/>
          <p class="hint">First column = <b>Alternative</b>. Other columns = criteria for AHP.</p>
        </div>

        <div id="ahpCritCard" class="card dark" style="display:none">
          <div class="section-title">Step 2: Criteria detected</div>
          <div class="mini">These criteria will be used to build the AHP pairwise matrix.</div>
          <div id="ahpCritList" style="margin-top:10px"></div>
        </div>

        <div id="ahpPairCard" class="card dark" style="display:none">
          <div class="section-title">Step 3: Pairwise Comparison Matrix (Saaty scale)</div>
          <div class="mini">
            Fill only the <b>upper triangle</b>. The lower triangle becomes reciprocal automatically.<br/>
            Scale: 1 (equal), 3, 5, 7, 9. Use 2,4,6,8 for intermediate.
          </div>
          <div class="table-wrap" style="margin-top:10px"><table id="ahpMatrix"></table></div>
          <div style="margin-top:10px" class="row">
            <button class="btn" id="ahpSetOnes">↺ Set all to 1</button>
            <button class="btn" id="ahpCompute">✅ Step 4–5: Compute Weights & Consistency</button>
          </div>
        </div>
      </div>

      <div>
        <div id="ahpResultCard" class="card light" style="display:none">
          <div class="section-title">AHP Output</div>

          <div class="pill">Step 4: Weights via Geometric Mean</div>
          <div class="table-wrap"><table id="ahpWeightsTbl"></table></div>

          <div style="margin-top:14px" class="pill">Step 5: Consistency</div>
          <div id="ahpConsistency" class="mini"></div>

          <div style="margin-top:14px" class="pill">Formulas used</div>
          <div class="mini">
            Π<sub>i</sub> = ∏<sub>j</sub> p<sub>ij</sub><br/>
            g<sub>i</sub> = (Π<sub>i</sub>)<sup>1/m</sup><br/>
            ω<sub>i</sub> = g<sub>i</sub> / ∑ g<sub>k</sub><br/><br/>
            y = Pω,  λ<sub>i</sub> = y<sub>i</sub>/ω<sub>i</sub>,  λ<sub>max</sub> = (1/m)∑λ<sub>i</sub><br/>
            CI = (λ<sub>max</sub> − m)/(m − 1),  CR = CI/RI
          </div>
        </div>

        <div class="card dark" style="margin-top:16px">
          <div class="section-title">Tip</div>
          <div class="mini">
            If your <b>CR &gt; 0.10</b>, revise the pairwise values (upper triangle) until CR ≤ 0.10.
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ================= TAB: SYAI (placeholder) ================= -->
  <div id="viewSYAI" style="display:none">
    <div class="card dark">
      <div class="section-title">SYAI tab</div>
      <div class="mini">
        This file focuses on making AHP step-by-step working + purple pastel UI.
        If you want, I can merge your full SYAI code back here and auto-fill SYAI weights using the AHP weights you computed.
      </div>
    </div>
  </div>

</div>

<div id="tt"></div>

<script>
(function(){
  const $  = (id)=> document.getElementById(id);
  const show = (el,on=true)=> el.style.display = on ? "" : "none";

  // ---------- theme ----------
  let dark=true;
  function applyTheme(){
    document.body.classList.toggle('theme-dark', dark);
    document.body.classList.toggle('theme-light', !dark);
    $("themeToggle").textContent = dark ? "🌙 Dark" : "☀️ Light";
  }
  $("themeToggle").onclick = ()=>{ dark=!dark; applyTheme(); };
  applyTheme();

  // ---------- injected by Python ----------
  const SAMPLE_TEXT = `__INJECT_SAMPLE_CSV__`;

  $("downloadSample").href = "data:text/csv;charset=utf-8," + encodeURIComponent(SAMPLE_TEXT);
  $("downloadSample").download = "sample.csv";
  $("loadSample").onclick = ()=> initAHP(SAMPLE_TEXT);

  // ---------- tabs ----------
  function activateAHP(){
    $("tabAHP").classList.add("active"); $("tabSYAI").classList.remove("active");
    show($("viewAHP"), true); show($("viewSYAI"), false);
  }
  function activateSYAI(){
    $("tabSYAI").classList.add("active"); $("tabAHP").classList.remove("active");
    show($("viewAHP"), false); show($("viewSYAI"), true);
  }
  $("tabAHP").addEventListener("click", activateAHP);
  $("tabSYAI").addEventListener("click", activateSYAI);
  activateAHP();

  // ---------- CSV helpers ----------
  function parseCSVText(text){
    const rows=[]; let i=0, cur="", inQ=false, row=[];
    const pushCell=()=>{ row.push(cur); cur=""; };
    const pushRow =()=>{ rows.push(row); row=[]; };
    while(i<text.length){
      const ch=text[i];
      if(inQ){
        if(ch==='\"'){ if(text[i+1]==='\"'){ cur+='\"'; i++; } else { inQ=false; } }
        else cur+=ch;
      }else{
        if(ch==='\"') inQ=true;
        else if(ch===',') pushCell();
        else if(ch==='\n'){ pushCell(); pushRow(); }
        else if(ch==='\r'){}
        else cur+=ch;
      }
      i++;
    }
    pushCell(); if(row.length>1 || row[0] !== "") pushRow();
    return rows;
  }

  // ---------- AHP state ----------
  let crit = [];
  let P = [];
  const RI = { 1:0.00, 2:0.00, 3:0.58, 4:0.90, 5:1.12, 6:1.24, 7:1.32, 8:1.41, 9:1.45, 10:1.49 };

  function initAHP(csvText){
    const arr = parseCSVText(csvText);
    if(!arr.length) return;

    let header = arr[0].map(x=> String(x??"").trim());
    if(header[0] !== "Alternative"){
      const idx = header.indexOf("Alternative");
      if(idx>0){ const nm=header.splice(idx,1)[0]; header.unshift(nm); }
      else header[0] = "Alternative";
    }

    crit = header.slice(1);
    if(crit.length < 2){
      alert("Need at least 2 criteria columns for AHP.");
      return;
    }

    buildCriteriaCard();
    buildPairwiseMatrix();

    show($("ahpCritCard"), true);
    show($("ahpPairCard"), true);
    show($("ahpResultCard"), false);
  }

  $("csvAHP").onchange = (e)=>{
    const f=e.target.files[0]; if(!f) return;
    const r=new FileReader();
    r.onload = ()=> initAHP(String(r.result));
    r.readAsText(f);
  };

  function buildCriteriaCard(){
    const box = $("ahpCritList");
    box.innerHTML = "";
    crit.forEach((c)=> {
      const pill = document.createElement("span");
      pill.className = "pill";
      pill.textContent = c;
      box.appendChild(pill);
    });
  }

  function buildPairwiseMatrix(){
    const m = crit.length;
    P = Array.from({length:m}, (_,i)=> Array.from({length:m}, (_,j)=> (i===j?1:1)));

    const tbl = $("ahpMatrix");
    tbl.innerHTML = "";

    const thead = document.createElement("thead");
    const trh = document.createElement("tr");
    trh.innerHTML = "<th>Criteria</th>" + crit.map(c=> `<th>${c}</th>`).join("");
    thead.appendChild(trh);
    tbl.appendChild(thead);

    const tbody = document.createElement("tbody");
    for(let i=0;i<m;i++){
      const tr = document.createElement("tr");

      const th = document.createElement("th");
      th.textContent = crit[i];
      tr.appendChild(th);

      for(let j=0;j<m;j++){
        const td = document.createElement("td");

        if(i===j){
          td.textContent = "1";
        } else if(i < j){
          const sel = document.createElement("select");
          [1,2,3,4,5,6,7,8,9].forEach(v=>{
            const o=document.createElement("option");
            o.value = String(v);
            o.textContent = String(v);
            sel.appendChild(o);
          });
          sel.value = "1";
          sel.onchange = ()=>{
            const v = parseFloat(sel.value);
            P[i][j] = v;
            P[j][i] = 1/v;

            // mirrored cell is in row j, column i (+1 for row header)
            const mirror = tbody.children[j].children[i+1];
            mirror.textContent = (1/v).toFixed(6);
          };
          td.appendChild(sel);
        } else {
          td.textContent = (P[i][j]).toFixed(6);
        }

        tr.appendChild(td);
      }

      tbody.appendChild(tr);
    }
    tbl.appendChild(tbody);

    $("ahpSetOnes").onclick = ()=>{
      for(let i=0;i<m;i++){
        for(let j=0;j<m;j++){
          P[i][j] = (i===j?1:1);
        }
      }
      buildPairwiseMatrix();
      show($("ahpResultCard"), false);
    };

    $("ahpCompute").onclick = ()=> computeAHP();
  }

  function computeAHP(){
    const m = crit.length;

    // Step 4: geometric mean weights
    const prod = new Array(m).fill(1);
    for(let i=0;i<m;i++){
      let p=1;
      for(let j=0;j<m;j++) p *= P[i][j];
      prod[i]=p;
    }

    const g = prod.map(v=> Math.pow(v, 1/m));
    const sumg = g.reduce((s,v)=> s+v, 0) || 1;
    const w = g.map(v=> v/sumg);

    // Step 5: consistency
    const y = new Array(m).fill(0);
    for(let i=0;i<m;i++){
      let s=0;
      for(let j=0;j<m;j++) s += P[i][j]*w[j];
      y[i]=s;
    }

    const lam = y.map((yi,i)=> yi/(w[i] || 1e-12));
    const lamMax = lam.reduce((s,v)=> s+v, 0) / m;

    const CI = (lamMax - m) / (m - 1);
    const ri = RI[m] ?? 1.49;
    const CR = (ri === 0) ? 0 : (CI / ri);

    renderWeightsTable(w, g, prod);
    renderConsistency(lamMax, CI, CR, ri);

    show($("ahpResultCard"), true);
  }

  function renderWeightsTable(w, g, prod){
    const tb = $("ahpWeightsTbl");
    tb.innerHTML = "";
    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>Criterion</th><th>Πᵢ (row product)</th><th>gᵢ (geom. mean)</th><th>Weight ωᵢ</th></tr>";
    tb.appendChild(thead);

    const tbody = document.createElement("tbody");
    crit.forEach((c,i)=>{
      const tr = document.createElement("tr");
      tr.innerHTML =
        `<td>${c}</td>
         <td>${prod[i].toExponential(6)}</td>
         <td>${g[i].toFixed(6)}</td>
         <td><b>${w[i].toFixed(6)}</b></td>`;
      tbody.appendChild(tr);
    });
    tb.appendChild(tbody);
  }

  function renderConsistency(lamMax, CI, CR, ri){
    const box = $("ahpConsistency");
    const ok = (CR <= 0.10);
    box.innerHTML =
      `<div>m = <b>${crit.length}</b></div>
       <div>λ<sub>max</sub> = <b>${lamMax.toFixed(6)}</b></div>
       <div>CI = <b>${CI.toFixed(6)}</b></div>
       <div>RI = <b>${ri.toFixed(2)}</b></div>
       <div>CR = <b>${CR.toFixed(6)}</b> → ${ok ? "<b style='color:#16a34a'>ACCEPTABLE (≤ 0.10)</b>" : "<b style='color:#dc2626'>NOT OK (&gt; 0.10)</b>"}</div>
       <div class="hint" style="margin-top:6px">If CR not OK, revise pairwise values until CR ≤ 0.10.</div>`;
  }

  // preload sample
  initAHP(SAMPLE_TEXT);

})();
</script>
</body>
</html>
"""

# Inject sample csv (SAFE)
html = html.replace("__INJECT_SAMPLE_CSV__", SAFE_SAMPLE_CSV)

components.html(html, height=2200, scrolling=True)
