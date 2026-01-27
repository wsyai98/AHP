# app.py
import base64
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
<title>AHP Step-by-Step</title>

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

  .table-wrap{overflow:auto;max-height:420px}
  table{width:100%;border-collapse:collapse;font-size:14px;color:#111}
  th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #e5e7eb}
  th{background:rgba(243,232,255,.65); position:sticky; top:0}

  .grid2{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(240px,1fr))}

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
</style>
</head>

<body class="theme-dark">
<div class="container">
  <div class="header">
    <div class="title">AHP (Pastel Purple) — Step-by-Step</div>
    <div class="row">
      <a class="btn" id="downloadSample">⬇️ Download Sample</a>
      <button class="btn" id="loadSample">📄 Load Sample</button>
      <button class="toggle" id="themeToggle">🌙 Dark</button>
    </div>
  </div>

  <div class="grid">
    <div>
      <!-- Step 1 -->
      <div class="card dark">
        <div class="section-title">Step 1: Upload CSV (auto detect criteria)</div>
        <label for="csvAHP" class="btn">📤 Choose CSV</label>
        <input id="csvAHP" type="file" accept=".csv" style="display:none"/>
        <p class="hint">First column = <b>Alternative</b>. Others = criteria.</p>
      </div>

      <!-- Show matrix -->
      <div id="mCard" class="card light" style="display:none;margin-top:14px">
        <div class="section-title">Decision Matrix (preview)</div>
        <div class="table-wrap"><table id="tblMatrix"></table></div>
      </div>

      <!-- Step 2 -->
      <div id="typeCard" class="card dark" style="display:none;margin-top:14px">
        <div class="section-title">Step 2: Criteria Type (Benefit / Cost)</div>
        <div class="mini">Ini penting untuk explain criteria (contoh: <b>Cost</b> = lebih kecil lebih baik, <b>Benefit</b> = lebih besar lebih baik).</div>
        <div id="typesWrap" class="grid2" style="margin-top:12px"></div>
      </div>

      <!-- Step 3 -->
      <div id="pairCard" class="card dark" style="display:none;margin-top:14px">
        <div class="section-title">Step 3: Pairwise Comparison Matrix (Saaty)</div>
        <div class="mini">
          Isi <b>upper triangle</b> sahaja. Bawah akan auto jadi reciprocal (p<sub>ji</sub> = 1/p<sub>ij</sub>).<br/>
          Skala: 1,3,5,7,9 (2,4,6,8 untuk intermediate).
        </div>
        <div class="table-wrap" style="margin-top:10px"><table id="ahpMatrix"></table></div>
        <div style="margin-top:10px" class="row">
          <button class="btn" id="ahpSetOnes">↺ Set all to 1</button>
          <button class="btn" id="ahpCompute">✅ Step 4–5: Compute Weights & Consistency</button>
        </div>
      </div>
    </div>

    <div>
      <!-- Result -->
      <div id="resultCard" class="card light" style="display:none">
        <div class="section-title">AHP Output</div>

        <div class="pill">Step 4: Weights (Geometric Mean)</div>
        <div class="table-wrap"><table id="weightsTbl"></table></div>

        <div style="margin-top:14px" class="pill">Step 5: Consistency</div>
        <div id="consBox" class="mini"></div>

        <div style="margin-top:14px" class="pill">Formulas (paper)</div>
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
          Kalau <b>CR &gt; 0.10</b> → pairwise kau tak konsisten. Adjust upper triangle sampai <b>CR ≤ 0.10</b>.
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

  function renderTable(tid, cols, rows){
    const tb=$(tid); tb.innerHTML="";
    const thead=document.createElement("thead");
    const trh=document.createElement("tr");
    cols.forEach(c=>{ const th=document.createElement("th"); th.textContent=c; trh.appendChild(th); });
    thead.appendChild(trh); tb.appendChild(thead);

    const tbody=document.createElement("tbody");
    rows.forEach(r=>{
      const tr=document.createElement("tr");
      cols.forEach((c,ci)=>{ const td=document.createElement("td"); td.textContent=String(r[ci] ?? ""); tr.appendChild(td); });
      tbody.appendChild(tr);
    });
    tb.appendChild(tbody);
  }

  // ---------- AHP state ----------
  let header = [];
  let crit = [];
  let P = [];
  let critType = {}; // Benefit/Cost

  // Random Index
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

    // matrix preview
    const preview = arr.slice(0, Math.min(arr.length, 11)); // header + 10 rows
    renderTable("tblMatrix", header, preview.slice(1));
    show($("mCard"), true);

    // default type: Benefit
    critType = Object.fromEntries(crit.map(c=> [c, "Benefit"]));
    renderTypes();

    buildPairwiseMatrix();

    show($("typeCard"), true);
    show($("pairCard"), true);
    show($("resultCard"), false);
  }

  $("csvAHP").onchange = (e)=>{
    const f=e.target.files[0]; if(!f) return;
    const r=new FileReader();
    r.onload = ()=> initAll(String(r.result));
    r.readAsText(f);
  };

  function renderTypes(){
    const wrap = $("typesWrap");
    wrap.innerHTML = "";
    crit.forEach(c=>{
      const box=document.createElement("div");

      const lab=document.createElement("div");
      lab.className="label";
      lab.textContent = c;
      box.appendChild(lab);

      const sel=document.createElement("select");
      ["Benefit","Cost"].forEach(v=>{
        const o=document.createElement("option");
        o.value=v; o.textContent=v;
        sel.appendChild(o);
      });
      sel.value = critType[c] || "Benefit";
      sel.onchange = ()=>{ critType[c]=sel.value; };
      box.appendChild(sel);

      const small=document.createElement("div");
      small.className="hint";
      small.style.marginTop="6px";
      small.innerHTML = (sel.value==="Cost")
        ? "Cost: kecil lebih baik (min)."
        : "Benefit: besar lebih baik (max).";
      sel.onchange = ()=>{
        critType[c]=sel.value;
        small.innerHTML = (sel.value==="Cost")
          ? "Cost: kecil lebih baik (min)."
          : "Benefit: besar lebih baik (max).";
      };
      box.appendChild(small);

      wrap.appendChild(box);
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
      show($("resultCard"), false);
    };

    $("ahpCompute").onclick = ()=> computeAHP();
  }

  function computeAHP(){
    const m = crit.length;

    // Step 4 (paper): Π_i, g_i, ω_i (Geometric Mean)
    const prod = new Array(m).fill(1);
    for(let i=0;i<m;i++){
      let p=1;
      for(let j=0;j<m;j++) p *= P[i][j];
      prod[i]=p;
    }
    const g = prod.map(v=> Math.pow(v, 1/m));
    const sumg = g.reduce((s,v)=> s+v, 0) || 1;
    const w = g.map(v=> v/sumg);

    // Step 5 (paper): λmax, CI, CR
    const y = new Array(m).fill(0);
    for(let i=0;i<m;i++){
      let s=0;
      for(let j=0;j<m;j++) s += P[i][j]*w[j];
      y[i]=s;
    }
    const lam = y.map((yi,i)=> yi/(w[i] || 1e-12));
    const lamMax = lam.reduce((s,v)=> s+v, 0) / m;

    const CI = (lamMax - m) / (m - 1);
    const ri = RI[m] ?? (1.98*(m-2)/m); // fallback approximation
    const CR = (ri === 0) ? 0 : (CI / ri);

    renderWeightsTable(w, g, prod);
    renderConsistency(lamMax, CI, CR, ri);

    show($("resultCard"), true);
  }

  function renderWeightsTable(w, g, prod){
    const tb = $("weightsTbl");
    tb.innerHTML = "";
    const thead = document.createElement("thead");
    thead.innerHTML = "<tr><th>Criterion</th><th>Type</th><th>Πᵢ</th><th>gᵢ</th><th>Weight ωᵢ</th></tr>";
    tb.appendChild(thead);

    const tbody = document.createElement("tbody");
    crit.forEach((c,i)=>{
      const tr = document.createElement("tr");
      tr.innerHTML =
        `<td>${c}</td>
         <td><b>${critType[c] || "Benefit"}</b></td>
         <td>${prod[i].toExponential(6)}</td>
         <td>${g[i].toFixed(6)}</td>
         <td><b>${w[i].toFixed(6)}</b></td>`;
      tbody.appendChild(tr);
    });
    tb.appendChild(tbody);
  }

  function renderConsistency(lamMax, CI, CR, ri){
    const box = $("consBox");
    const ok = (CR <= 0.10);
    box.innerHTML =
      `<div>m = <b>${crit.length}</b></div>
       <div>λ<sub>max</sub> = <b>${lamMax.toFixed(6)}</b></div>
       <div>CI = <b>${CI.toFixed(6)}</b></div>
       <div>RI = <b>${ri.toFixed(2)}</b></div>
       <div>CR = <b>${CR.toFixed(6)}</b> → ${ok ? "<span class='ok'>ACCEPTABLE (≤ 0.10)</span>" : "<span class='bad'>NOT OK (&gt; 0.10)</span>"}</div>
       <div class="hint" style="margin-top:6px">If CR not OK, revise pairwise values until CR ≤ 0.10.</div>`;
  }

  // preload sample
  initAll(SAMPLE_TEXT);

})();
</script>
</body>
</html>
"""

# Inject sample csv (SAFE)
html = html.replace("__INJECT_SAMPLE_CSV__", SAFE_SAMPLE_CSV)

components.html(html, height=2400, scrolling=True)
