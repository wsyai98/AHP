# app.py
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AHP Step-by-Step (Pastel Purple)", layout="wide")
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
    # fallback
    return (
        "Alternative,Cost,Quality,Delivery\n"
        "A1,200,8,4\n"
        "A2,250,7,5\n"
        "A3,300,9,6\n"
        "A4,220,8,4\n"
        "A5,180,6,7\n"
    )

SAMPLE_CSV = load_sample_csv_text()

def escape_for_js_template_literal(s: str) -> str:
    # Avoid breaking JS template literal: backslashes, backticks, and ${ interpolation
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
<title>AHP Step-by-Step</title>

<style>
  :root{
    --bg1:#0b0b10;
    --bg2:#141227;
    --lav:#f3e8ff;
    --lav2:#e9d5ff;
    --vio:#c4b5fd;
    --vio2:#a78bfa;
    --vio3:#8b5cf6;
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
  .header{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;gap:12px;flex-wrap:wrap}
  .title{
    font-weight:900;
    font-size:28px;
    letter-spacing:.3px;
    color: var(--lav);
    text-shadow: 0 10px 28px rgba(167,139,250,.22);
    white-space:nowrap;
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

  .hint{font-size:12px;opacity:.85}
  .mini{font-size:12px;opacity:.92;line-height:1.55}

  .table-wrap{overflow:auto;max-height:440px}
  table{width:100%;border-collapse:collapse;font-size:14px;color:#111}
  th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #e5e7eb}
  th{background:rgba(243,232,255,.65); position:sticky; top:0}

  .pill{
    display:inline-flex;align-items:center;gap:8px;
    padding:6px 10px;border-radius:999px;
    border:1px solid #c4b5fd;
    background: rgba(237,233,254,.7);
    margin:0 6px 6px 0;font-size:12px;color:#111;
    font-weight:900;
  }

  .ok{color:#16a34a;font-weight:900}
  .bad{color:#dc2626;font-weight:900}

  select{
    width:100%;
    padding:10px 12px;border-radius:12px;
    border:1px solid #ddd;background:#fbfaff;color:#111;
  }
</style>
</head>

<body class="theme-dark">
<div class="container">
  <div class="header">
    <div class="title">AHP — Step-by-Step (Paper)</div>
    <div class="row">
      <a class="btn" id="downloadSample">⬇️ Download Sample</a>
      <button class="btn" id="loadSample">📄 Load Sample</button>
      <button class="toggle" id="themeToggle">🌙 Dark</button>
    </div>
  </div>

  <div class="grid">
    <div>
      <div class="card dark">
        <div class="section-title">Step 1: Upload CSV (auto-detect criteria)</div>
        <label for="csvAHP" class="btn">📤 Choose CSV</label>
        <input id="csvAHP" type="file" accept=".csv" style="display:none"/>
        <p class="hint">First column = <b>Alternative</b>. Other columns = criteria names for AHP.</p>
      </div>

      <div id="mCard" class="card light" style="display:none;margin-top:14px">
        <div class="section-title">Detected Decision Matrix (preview)</div>
        <div class="table-wrap"><table id="tblMatrix"></table></div>
      </div>

      <div id="critCard" class="card dark" style="display:none;margin-top:14px">
        <div class="section-title">Step 2: Criteria detected (R₁…Rₘ)</div>
        <div class="mini">Criteria list below is extracted automatically from your CSV header.</div>
        <div id="critList" style="margin-top:10px"></div>
      </div>

      <div id="pairCard" class="card dark" style="display:none;margin-top:14px">
        <div class="section-title">Step 3: Pairwise Comparison Matrix P (Saaty)</div>
        <div class="mini">
          Fill only <b>upper triangle</b>. Inverse-symmetry: <b>pᵢⱼ = 1 / pⱼᵢ</b>. Diagonal is 1.<br/>
          Saaty scale: 1,3,5,7,9 (and 2,4,6,8 as intermediate).
        </div>
        <div class="table-wrap" style="margin-top:10px"><table id="ahpMatrix"></table></div>
        <div style="margin-top:10px" class="row">
          <button class="btn" id="ahpSetOnes">↺ Set all to 1</button>
          <button class="btn" id="ahpCompute">✅ Step 4–5: Compute ω & Consistency</button>
        </div>
      </div>
    </div>

    <div>
      <div id="resultCard" class="card light" style="display:none">
        <div class="section-title">AHP Output</div>

        <div class="pill">Step 4: Weights ω (principal eigenvector)</div>
        <div class="mini">
          Paper step: solve <b>Pω = λω</b>, take the eigenvector of the largest eigenvalue <b>λmax</b>, then normalize ω so ∑ωᵢ = 1.
        </div>
        <div class="table-wrap" style="margin-top:10px"><table id="weightsTbl"></table></div>

        <div style="margin-top:14px" class="pill">Step 5: Consistency (Sᵢ, S)</div>
        <div id="consBox" class="mini" style="margin-top:6px"></div>

        <div style="margin-top:14px" class="pill">Formulas used (paper)</div>
        <div class="mini">
          (Eq.3–4) <b>Pω = λω</b><br/>
          (Eq.5) <b>Sᵢ = (λmax − m)/(m − 1)</b><br/>
          (Eq.6) <b>S = Sᵢ / RI</b> (acceptable if <b>S ≤ 0.10</b>)<br/>
          RI uses Table 1 values.
        </div>
      </div>

      <div class="card dark" style="margin-top:16px">
        <div class="section-title">Tip</div>
        <div class="mini">
          If <b>S (CR) &gt; 0.10</b>, revise the upper triangle pairwise values until <b>S ≤ 0.10</b>.
        </div>
      </div>
    </div>
  </div>
</div>

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
  $("loadSample").onclick = ()=> initAll(SAMPLE_TEXT);

  // ---------- CSV parser ----------
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

  function renderPreviewTable(cols, rows){
    const tb=$("tblMatrix"); tb.innerHTML="";
    const thead=document.createElement("thead");
    const trh=document.createElement("tr");
    cols.forEach(c=>{ const th=document.createElement("th"); th.textContent=c; trh.appendChild(th); });
    thead.appendChild(trh); tb.appendChild(thead);

    const tbody=document.createElement("tbody");
    rows.forEach(r=>{
      const tr=document.createElement("tr");
      cols.forEach((_,ci)=>{
        const td=document.createElement("td");
        td.textContent=String(r[ci] ?? "");
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    tb.appendChild(tbody);
  }

  // ---------- AHP state ----------
  let header = [];
  let crit = [];
  let P = [];

  // Random Consistency Index values (Table 1)
  const RI = {
    1:0.00, 2:0.00, 3:0.58, 4:0.90, 5:1.12, 6:1.24, 7:1.32, 8:1.41, 9:1.45, 10:1.49,
    11:1.51, 12:1.48, 13:1.56, 14:1.57, 15:1.59
  };

  function initAll(csvText){
    const arr=parseCSVText(csvText);
    if(!arr.length) return;

    header = arr[0].map(x=> String(x??"").trim());
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

    // preview (header + up to 10 rows)
    const previewRows = arr.slice(1, Math.min(arr.length, 11));
    renderPreviewTable(header, previewRows);
    show($("mCard"), true);

    // show criteria pills
    const cl = $("critList");
    cl.innerHTML = "";
    crit.forEach(c=>{
      const pill=document.createElement("span");
      pill.className="pill";
      pill.textContent=c;
      cl.appendChild(pill);
    });
    show($("critCard"), true);

    buildPairwiseMatrix();
    show($("pairCard"), true);
    show($("resultCard"), false);
  }

  $("csvAHP").onchange = (e)=>{
    const f=e.target.files[0]; if(!f) return;
    const r=new FileReader();
    r.onload = ()=> initAll(String(r.result));
    r.readAsText(f);
  };

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
      show($("resultCard"), false);
    };

    $("ahpCompute").onclick = ()=> computeAHP();
  }

  // matrix-vector multiply
  function matVec(A, x){
    const m=A.length;
    const y=new Array(m).fill(0);
    for(let i=0;i<m;i++){
      let s=0;
      for(let j=0;j<m;j++) s += A[i][j]*x[j];
      y[i]=s;
    }
    return y;
  }
  function normalizeToSum1(x){
    let s=0; for(const v of x) s += v;
    s = s || 1;
    return x.map(v=> v/s);
  }

  // principal eigenvector via power iteration
  function powerIteration(A, maxIter=2000, tol=1e-12){
    const m=A.length;
    let w=new Array(m).fill(1/m);
    for(let it=0; it<maxIter; it++){
      const y = matVec(A, w);
      const wNew = normalizeToSum1(y.map(v=> Math.max(v, 1e-18)));
      let diff=0;
      for(let i=0;i<m;i++) diff = Math.max(diff, Math.abs(wNew[i]-w[i]));
      w = wNew;
      if(diff < tol) break;
    }
    return w;
  }

  function computeAHP(){
    const m = crit.length;

    // Step 4: solve Pω = λω (principal eigenvector)
    const w = powerIteration(P);

    // Step 5: λmax, SI, S
    const Pw = matVec(P, w);
    const lam = Pw.map((v,i)=> v/(w[i] || 1e-18));
    const lamMax = lam.reduce((s,v)=> s+v, 0) / m;

    const SI = (lamMax - m) / (m - 1);                 // Eq (5)
    const SA = (RI[m] !== undefined) ? RI[m] : (1.98*(m-2)/m); // Eq (7) approx if needed
    const S  = (SA === 0) ? 0 : (SI / SA);             // Eq (6)

    renderWeightsTable(w, Pw, lam, lamMax);
    renderConsistency(m, lamMax, SI, SA, S);

    show($("resultCard"), true);
  }

  function renderWeightsTable(w, Pw, lam, lamMax){
    const tb = $("weightsTbl");
    tb.innerHTML = "";
    const thead = document.createElement("thead");
    thead.innerHTML =
      "<tr><th>Criterion</th><th>Weight ωᵢ</th><th>(Pω)ᵢ</th><th>λᵢ = (Pω)ᵢ/ωᵢ</th></tr>";
    tb.appendChild(thead);

    const tbody = document.createElement("tbody");
    crit.forEach((c,i)=>{
      const tr = document.createElement("tr");
      tr.innerHTML =
        `<td>${c}</td>
         <td><b>${w[i].toFixed(6)}</b></td>
         <td>${Pw[i].toFixed(6)}</td>
         <td>${lam[i].toFixed(6)}</td>`;
      tbody.appendChild(tr);
    });

    const trf = document.createElement("tr");
    trf.innerHTML =
      `<td colspan="3" style="text-align:right"><b>λ<sub>max</sub></b></td>
       <td><b>${lamMax.toFixed(6)}</b></td>`;
    tbody.appendChild(trf);

    tb.appendChild(tbody);
  }

  function renderConsistency(m, lamMax, SI, SA, S){
    const box = $("consBox");
    const ok = (S <= 0.10);
    box.innerHTML =
      `<div>m = <b>${m}</b></div>
       <div>λ<sub>max</sub> = <b>${lamMax.toFixed(6)}</b></div>
       <div>S<sub>I</sub> = (λ<sub>max</sub> − m)/(m − 1) = <b>${SI.toFixed(6)}</b></div>
       <div>RI = <b>${SA.toFixed(2)}</b></div>
       <div>S = S<sub>I</sub>/RI = <b>${S.toFixed(6)}</b> → ${ok ? "<span class='ok'>ACCEPTABLE (≤ 0.10)</span>" : "<span class='bad'>NOT OK (&gt; 0.10)</span>"}</div>
       <div class="hint" style="margin-top:8px">If NOT OK: revise upper triangle pairwise values until S ≤ 0.10.</div>`;
  }

  // preload sample
  initAll(SAMPLE_TEXT);

})();
</script>
</body>
</html>
"""

# Inject sample csv safely
html = html.replace("__INJECT_SAMPLE_CSV__", SAFE_SAMPLE_CSV)

# Render once (no duplicates)
components.html(html, height=2600, scrolling=True)
