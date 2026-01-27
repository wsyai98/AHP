# app.py
from __future__ import annotations

from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AHP — Section 3 (GM + Consistency)", layout="wide")

# ---------- Sample CSV (pairwise) ----------
SAMPLE_PAIRWISE = """B,B1,B2,B3,B4,B5,B6,B7
B1,1,1/2,1/3,1/3,1/3,1/5,1
B2,2,1,1/3,1,1/3,1/5,1
B3,3,3,1,3,1,1,1
B4,3,1,1/3,1,1/3,1/3,1/3
B5,3,3,1,3,1,1,1
B6,5,5,1,3,1,1,1
B7,1,1,1,3,1,1,1
"""

def escape_for_js_template_literal(s: str) -> str:
    # Keep JS template literal safe
    return (
        s.replace("\\", "\\\\")
         .replace("`", "\\`")
         .replace("${", "\\${")
    )

SAFE_SAMPLE = escape_for_js_template_literal(SAMPLE_PAIRWISE)

# ---------- Streamlit background (subtle purple pastel) ----------
st.markdown(
    """
<style>
  .stApp{
    background:
      radial-gradient(1100px 520px at 15% 0%, rgba(167,139,250,.18), transparent 55%),
      radial-gradient(900px 460px at 85% 10%, rgba(196,181,253,.14), transparent 60%),
      linear-gradient(180deg, #0b0b10 0%, #141227 60%, rgba(243,232,255,.20) 140%) !important;
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
<title>AHP — Section 3</title>
<style>
  :root{
    --bg1:#0b0b10; --bg2:#141227;

    --lav:#f3e8ff; --lav2:#e9d5ff;
    --vio:#c4b5fd; --vio2:#a78bfa; --vio3:#8b5cf6;

    --textDark:#f8fafc;
    --textLight:#0f172a;

    --cardDark: rgba(18,16,35,.78);
    --cardLight: rgba(255,255,255,.88);

    --bdDark:#2c2a45;
    --bdLight:#e5e7eb;

    --btn:#a78bfa; --btnBd:#8b5cf6;

    --mutedDark: rgba(226,232,240,.82);
    --mutedLight: rgba(15,23,42,.82);
  }

  *{box-sizing:border-box}
  html,body{height:100%;margin:0}
  body{font-family: ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial}

  body.theme-dark{
    color:var(--textDark);
    background:
      radial-gradient(1100px 520px at 15% 0%, rgba(167,139,250,.22), transparent 55%),
      radial-gradient(900px 460px at 85% 10%, rgba(196,181,253,.18), transparent 60%),
      linear-gradient(180deg, var(--bg1) 0%, var(--bg2) 60%, rgba(243,232,255,.22) 140%);
  }
  body.theme-light{
    color:var(--textLight);
    background:
      radial-gradient(1100px 520px at 15% 0%, rgba(167,139,250,.20), transparent 55%),
      radial-gradient(900px 460px at 85% 10%, rgba(196,181,253,.16), transparent 60%),
      linear-gradient(180deg, #fbfaff 0%, #f8fafc 60%, #f3e8ff 140%);
  }

  /* Make it "memanjang ke bawah" (single column) */
  .container{max-width:980px;margin:20px auto;padding:0 14px}
  .header{
    display:flex;align-items:center;justify-content:space-between;
    gap:12px;flex-wrap:wrap;margin-bottom:12px
  }
  .title{
    font-weight:1000;font-size:30px;letter-spacing:.2px;
    color: var(--lav);
    text-shadow: 0 10px 28px rgba(167,139,250,.22);
  }
  body.theme-light .title{color:#0f172a;text-shadow:none}

  .row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
  .btn{
    display:inline-flex;align-items:center;gap:8px;
    padding:10px 14px;border-radius:14px;
    border:1px solid var(--btnBd);
    background: linear-gradient(180deg, var(--btn) 0%, var(--vio2) 100%);
    color:#fff;cursor:pointer;
    box-shadow: 0 12px 24px rgba(139,92,246,.18);
    text-decoration:none;font-weight:900;
  }
  .btn:hover{filter:brightness(.98); transform: translateY(-.5px)}
  .toggle{
    padding:8px 12px;border-radius:14px;
    border:1px solid var(--bdDark);
    background: rgba(255,255,255,.06);
    color:#eee;cursor:pointer;font-weight:900;
  }
  body.theme-light .toggle{background:#fff;color:#111;border-color:#cbd5e1}

  .card{
    border-radius:18px;padding:18px;
    border:1px solid var(--bdLight);
    backdrop-filter: blur(8px);
    margin-bottom:14px;
  }
  .card.dark{background:var(--cardDark);color:var(--mutedDark);border-color:var(--bdDark)}
  .card.light{background:var(--cardLight);color:var(--textLight);border-color:var(--bdLight)}
  body.theme-light .card.dark{background:#fff;color:var(--textLight);border-color:#e5e7eb}

  .section-title{
    font-weight:1000;font-size:18px;margin-bottom:10px;
    color: var(--lav2);
  }
  body.theme-light .section-title{color:#4c1d95}

  .hint{font-size:12px;opacity:.88;line-height:1.6}
  .mini{font-size:12.5px;opacity:.92;line-height:1.65}

  /* Pills */
  .pill{
    display:inline-flex;align-items:center;gap:8px;
    padding:6px 10px;border-radius:999px;
    border:1px solid rgba(196,181,253,.9);
    background: rgba(237,233,254,.78);
    margin:0 6px 6px 0;
    font-size:12px;color:#111;font-weight:1000;
  }

  /* Tables */
  .table-wrap{overflow:auto;max-height:360px;border-radius:14px}
  table{width:100%;border-collapse:collapse;font-size:14px}
  th,td{padding:8px 10px;border-bottom:1px solid rgba(148,163,184,.35);white-space:nowrap}
  thead th{position:sticky;top:0;z-index:5}

  /* IMPORTANT: dark mode Step1A/1B font white, light mode black */
  body.theme-dark table{color:#e5e7eb}
  body.theme-dark thead th{background: rgba(139,92,246,.18); color:#f8fafc}
  body.theme-dark td{color:#e5e7eb}

  body.theme-light table{color:#0f172a}
  body.theme-light thead th{background: rgba(237,233,254,.75); color:#0f172a}

  .ok{color:#16a34a;font-weight:1000}
  .bad{color:#dc2626;font-weight:1000}

  /* Chart box */
  .chartBox{
    border-radius:16px;
    border:1px solid rgba(148,163,184,.35);
    background: rgba(255,255,255,.50);
    padding:10px;
  }
  body.theme-dark .chartBox{
    background: rgba(255,255,255,.06);
    border-color: rgba(148,163,184,.22);
  }
  .chart{width:100%;height:260px}
  .chart svg{width:100%;height:100%}

  /* Tabs for results (Step 2..7) */
  .tabs{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 6px}
  .tab{
    padding:8px 12px;border-radius:999px;
    border:1px solid rgba(148,163,184,.35);
    background: rgba(255,255,255,.08);
    color:inherit;cursor:pointer;font-weight:900;font-size:12px;
  }
  body.theme-light .tab{background:#fff}
  .tab.active{
    background: rgba(167,139,250,.30);
    border-color: rgba(167,139,250,.60);
  }

  .hidden{display:none}

  /* Tooltip */
  #tt{
    position:fixed;display:none;pointer-events:none;
    background:#fff;color:#111;
    padding:6px 8px;border-radius:10px;font-size:12px;
    box-shadow:0 12px 24px rgba(0,0,0,.18);
    border:1px solid #e5e7eb;z-index:9999
  }
</style>
</head>

<body class="theme-dark">
<div class="container">

  <div class="header">
    <div class="title">AHP — Section 3 (GM + Consistency)</div>
    <div class="row">
      <a class="btn" id="downloadSample">⬇️ Sample CSV</a>
      <button class="btn" id="loadSample">📄 Load Sample</button>
      <button class="toggle" id="themeToggle">🌙 Dark</button>
    </div>
  </div>

  <!-- STEP 1 -->
  <div class="card dark">
    <div class="section-title">Step 1 — Upload CSV (Pairwise Matrix P)</div>
    <label for="csvAHP" class="btn">📤 Choose CSV</label>
    <input id="csvAHP" type="file" accept=".csv,.txt" style="display:none"/>
    <div class="hint" style="margin-top:10px">
      Square matrix (m×m). First column = row labels. Values can be <b>1/3</b>.
    </div>
  </div>

  <!-- BEFORE LOAD: nothing else -->
  <div id="beforeLoad" class="card light">
    <div class="section-title">Output</div>
    <div class="mini">Upload / Load dulu. Lepas tu baru semua Step 1A sampai Step 7 keluar ikut CSV yang user upload.</div>
  </div>

  <!-- AFTER LOAD -->
  <div id="afterLoad" class="hidden">

    <!-- Step 1A -->
    <div class="card dark">
      <div class="section-title">Step 1A — Raw CSV (preview)</div>
      <div class="table-wrap"><table id="tblRaw"></table></div>
    </div>

    <!-- Step 1B -->
    <div class="card dark">
      <div class="section-title">Step 1B — Numeric P</div>
      <div class="mini" id="metaLine" style="margin-bottom:10px"></div>
      <div class="table-wrap"><table id="tblP"></table></div>
    </div>

    <!-- Results -->
    <div class="card light">
      <div class="section-title">Results (Step 2 — Step 7)</div>

      <div class="tabs">
        <button class="tab active" data-tab="s2">Step 2 Π</button>
        <button class="tab" data-tab="s3">Step 3 GM</button>
        <button class="tab" data-tab="s4">Step 4 ω</button>
        <button class="tab" data-tab="s5">Step 5 pᵢⱼ·ωⱼ + Pω</button>
        <button class="tab" data-tab="s6">Step 6 λ</button>
        <button class="tab" data-tab="s7">Step 7 SI & CR</button>
      </div>

      <div id="s2">
        <div class="mini" style="margin:6px 0 10px"><b>Πᵢ = ∏ⱼ pᵢⱼ</b></div>
        <div class="table-wrap"><table id="tblPi"></table></div>
      </div>

      <div id="s3" class="hidden">
        <div class="mini" style="margin:6px 0 10px"><b>GMᵢ = (Πᵢ)^(1/m)</b></div>
        <div class="table-wrap"><table id="tblGM"></table></div>
      </div>

      <div id="s4" class="hidden">
        <div class="mini" style="margin:6px 0 10px"><b>ωᵢ = GMᵢ / ΣGM</b></div>

        <div class="table-wrap"><table id="tblW"></table></div>

        <div style="margin-top:14px" class="section-title">Weights (ω) — Bar</div>
        <div class="chartBox"><div class="chart"><svg id="wBar"></svg></div></div>
      </div>

      <div id="s5" class="hidden">
        <div class="mini" style="margin:6px 0 10px">
          Show <b>pᵢⱼ·ωⱼ</b> (row-wise) and <b>(Pω)ᵢ = Σⱼ pᵢⱼ·ωⱼ</b>
        </div>
        <div class="table-wrap"><table id="tblPWParts"></table></div>
      </div>

      <div id="s6" class="hidden">
        <div class="mini" style="margin:6px 0 10px"><b>λᵢ = (Pω)ᵢ / ωᵢ</b> and <b>λmax = average(λᵢ)</b></div>
        <div class="table-wrap"><table id="tblLam"></table></div>
        <div class="mini" style="margin-top:10px"><b id="lamMaxLine"></b></div>
      </div>

      <div id="s7" class="hidden">
        <div class="mini" style="margin:6px 0 10px">
          <b>SI = (λmax − m)/(m − 1)</b>, <b>CR = SI / RI</b> (acceptable if <b>CR ≤ 0.10</b>)
        </div>
        <div id="consBox" class="mini"></div>
      </div>
    </div>

  </div>
</div>

<div id="tt"></div>

<script>
(function(){
  const $ = (id)=> document.getElementById(id);
  const show = (el,on=true)=> el.classList.toggle("hidden", !on);

  // ---------- theme ----------
  let dark = true;
  function applyTheme(){
    document.body.classList.toggle("theme-dark", dark);
    document.body.classList.toggle("theme-light", !dark);
    $("themeToggle").textContent = dark ? "🌙 Dark" : "☀️ Light";
  }
  $("themeToggle").onclick = ()=>{ dark=!dark; applyTheme(); };
  applyTheme();

  // ---------- tooltip ----------
  const TT = $("tt");
  function showTT(x,y,html){
    TT.style.display="block"; TT.style.left=(x+12)+"px"; TT.style.top=(y+12)+"px"; TT.innerHTML=html;
  }
  function hideTT(){ TT.style.display="none"; }

  // ---------- injected sample ----------
  const SAMPLE_TEXT = `__INJECT_SAMPLE__`;
  $("downloadSample").href = "data:text/csv;charset=utf-8," + encodeURIComponent(SAMPLE_TEXT);
  $("downloadSample").download = "ahp_pairwise_sample.csv";

  // ---------- CSV parser (comma/semicolon/tab robust) ----------
  function parseCSV(text){
    // try split by lines, detect delimiter by header line
    const lines = text.replace(/\r/g,"").split("\n").filter(x=>x.trim().length>0);
    if(!lines.length) return {header:[], rows:[]};

    const headLine = lines[0];
    const delims = [",",";","\t"];
    let best = ",", bestCount = -1;
    delims.forEach(d=>{
      const c = headLine.split(d).length;
      if(c > bestCount){ bestCount = c; best = d; }
    });

    const rows = lines.map(line=>{
      // basic split (no quotes needed for your use-case)
      return line.split(best).map(x=>x.trim());
    });
    const header = rows[0];
    const body = rows.slice(1);
    return {header, rows: body};
  }

  // parse positive number or fraction "1/3"
  function parseRatio(s){
    s = String(s ?? "").trim();
    if(!s) return NaN;
    s = s.replace("\\","/"); // allow 1\3
    if(s.includes("/")){
      const parts = s.split("/");
      if(parts.length !== 2) return NaN;
      const num = parseFloat(parts[0].trim());
      const den = parseFloat(parts[1].trim());
      if(!isFinite(num) || !isFinite(den) || den===0) return NaN;
      const v = num/den;
      return (isFinite(v) && v>0) ? v : NaN;
    }
    const v = parseFloat(s);
    return (isFinite(v) && v>0) ? v : NaN;
  }

  // Render table from 2D array
  function renderTable(elId, head, body){
    const tb = $(elId);
    tb.innerHTML = "";
    const thead = document.createElement("thead");
    const trh = document.createElement("tr");
    head.forEach(h=>{
      const th=document.createElement("th"); th.textContent=h; trh.appendChild(th);
    });
    thead.appendChild(trh);
    tb.appendChild(thead);

    const tbody = document.createElement("tbody");
    body.forEach(r=>{
      const tr=document.createElement("tr");
      r.forEach(v=>{
        const td=document.createElement("td"); td.textContent=v; tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    tb.appendChild(tbody);
  }

  // ---------- AHP core ----------
  const RI = {1:0.00,2:0.00,3:0.58,4:0.90,5:1.12,6:1.24,7:1.32,8:1.41,9:1.45,10:1.49,11:1.51,12:1.48,13:1.56,14:1.57,15:1.59};
  function approxRI(m){
    if(RI[m] !== undefined) return RI[m];
    if(m<=2) return 0.0;
    return 1.98*(m-2)/m;
  }

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

  function reciprocalCheck(P){
    const m=P.length;
    let maxErr = 0;
    for(let i=0;i<m;i++){
      maxErr = Math.max(maxErr, Math.abs(P[i][i]-1));
      for(let j=i+1;j<m;j++){
        maxErr = Math.max(maxErr, Math.abs(P[i][j]*P[j][i]-1));
      }
    }
    return maxErr;
  }

  function computeAll(P){
    const m=P.length;

    // Step 2: Π
    const Pi = new Array(m).fill(1);
    for(let i=0;i<m;i++){
      let prod = 1;
      for(let j=0;j<m;j++) prod *= P[i][j];
      Pi[i] = prod;
    }

    // Step 3: GM
    const GM = Pi.map(v=> Math.pow(v, 1/m));

    // Step 4: w
    const sumGM = GM.reduce((s,v)=>s+v,0) || 1;
    const w = GM.map(v=> v/sumGM);

    // Step 5: p_ij*w_j table + Pw
    const PWparts = [];
    for(let i=0;i<m;i++){
      const row = new Array(m).fill(0);
      for(let j=0;j<m;j++) row[j] = P[i][j]*w[j];
      PWparts.push(row);
    }
    const Pw = matVec(P, w);

    // Step 6: lambda
    const lam = Pw.map((v,i)=> v / (w[i] || 1e-18));
    const lamMax = lam.reduce((s,v)=>s+v,0) / m;

    // Step 7: SI, CR
    const SI = (m<=1) ? 0 : (lamMax - m)/(m-1);
    const RIm = approxRI(m);
    const CR = (RIm===0) ? 0 : (SI / RIm);

    return {Pi, GM, w, PWparts, Pw, lam, lamMax, SI, RIm, CR};
  }

  // ---------- charts (weights bar) ----------
  function drawWeightsBar(svgId, labels, vals){
    const svg = $(svgId);
    while(svg.firstChild) svg.removeChild(svg.firstChild);

    const W = (svg.getBoundingClientRect().width||880);
    const H = (svg.getBoundingClientRect().height||260);
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);

    const padL=46, padR=16, padT=16, padB=46;
    const max = Math.max(...vals) || 1;

    // axis
    const yAxis = document.createElementNS("http://www.w3.org/2000/svg","line");
    yAxis.setAttribute("x1",padL); yAxis.setAttribute("x2",padL);
    yAxis.setAttribute("y1",padT); yAxis.setAttribute("y2",H-padB);
    yAxis.setAttribute("stroke", dark ? "rgba(226,232,240,.75)" : "rgba(15,23,42,.6)");
    svg.appendChild(yAxis);

    const xAxis = document.createElementNS("http://www.w3.org/2000/svg","line");
    xAxis.setAttribute("x1",padL); xAxis.setAttribute("x2",W-padR);
    xAxis.setAttribute("y1",H-padB); xAxis.setAttribute("y2",H-padB);
    xAxis.setAttribute("stroke", dark ? "rgba(226,232,240,.75)" : "rgba(15,23,42,.6)");
    svg.appendChild(xAxis);

    // grid + labels
    for(let t=0;t<=4;t++){
      const v=max*t/4;
      const y=H-padB-(H-padT-padB)*(v/max);
      const gl=document.createElementNS("http://www.w3.org/2000/svg","line");
      gl.setAttribute("x1",padL); gl.setAttribute("x2",W-padR);
      gl.setAttribute("y1",y); gl.setAttribute("y2",y);
      gl.setAttribute("stroke", dark ? "rgba(226,232,240,.18)" : "rgba(15,23,42,.10)");
      gl.setAttribute("stroke-dasharray","3 3");
      svg.appendChild(gl);

      const tx=document.createElementNS("http://www.w3.org/2000/svg","text");
      tx.setAttribute("x",padL-8); tx.setAttribute("y",y+4);
      tx.setAttribute("text-anchor","end");
      tx.setAttribute("font-size","11");
      tx.setAttribute("fill", dark ? "rgba(226,232,240,.80)" : "rgba(15,23,42,.75)");
      tx.textContent = v.toFixed(2);
      svg.appendChild(tx);
    }

    const cell=(W-padL-padR)/labels.length;
    const barW=cell*0.72;

    labels.forEach((lab,i)=>{
      const x=padL+i*cell+(cell-barW)/2;
      const h=(H-padT-padB)*(vals[i]/max);
      const y=H-padB-h;

      // pastel purple bars (vary a bit)
      const fills = ["rgba(167,139,250,.65)","rgba(196,181,253,.65)","rgba(216,180,254,.65)","rgba(221,214,254,.65)"];
      const r=document.createElementNS("http://www.w3.org/2000/svg","rect");
      r.setAttribute("x",x); r.setAttribute("y",y);
      r.setAttribute("width",barW); r.setAttribute("height",h);
      r.setAttribute("rx","10"); r.setAttribute("ry","10");
      r.setAttribute("fill", fills[i%fills.length]);
      r.setAttribute("stroke", dark ? "rgba(255,255,255,.10)" : "rgba(15,23,42,.08)");
      r.addEventListener("mousemove",(ev)=> showTT(ev.clientX, ev.clientY, `<b>${lab}</b><br/>ω = ${vals[i].toFixed(6)}`));
      r.addEventListener("mouseleave", hideTT);
      svg.appendChild(r);

      const xl=document.createElementNS("http://www.w3.org/2000/svg","text");
      xl.setAttribute("x", x+barW/2);
      xl.setAttribute("y", H-16);
      xl.setAttribute("text-anchor","middle");
      xl.setAttribute("font-size","11");
      xl.setAttribute("fill", dark ? "rgba(226,232,240,.85)" : "rgba(15,23,42,.85)");
      xl.textContent = lab;
      svg.appendChild(xl);
    });
  }

  // ---------- UI: tabs ----------
  document.querySelectorAll(".tab").forEach(btn=>{
    btn.addEventListener("click", ()=>{
      const key = btn.getAttribute("data-tab");
      document.querySelectorAll(".tab").forEach(b=>b.classList.remove("active"));
      btn.classList.add("active");

      ["s2","s3","s4","s5","s6","s7"].forEach(id=> show($(id), id===key));
    });
  });

  // ---------- load & upload behaviors ----------
  $("loadSample").onclick = ()=> initWithCSV(SAMPLE_TEXT);

  $("csvAHP").onchange = (e)=>{
    const f=e.target.files[0];
    if(!f) return;
    const r=new FileReader();
    r.onload = ()=> initWithCSV(String(r.result));
    r.readAsText(f);
  };

  function initWithCSV(csvText){
    const parsed = parseCSV(csvText);
    const header = parsed.header;
    const rows = parsed.rows;

    if(header.length < 3){
      alert("CSV tak cukup kolum. Pastikan format pairwise matrix (m×m) ada label.");
      return;
    }

    // Expect first header cell is a label column (e.g., B), then criteria names
    const crit = header.slice(1).map(s=>s.trim());
    const m = crit.length;

    // Build raw preview table (Step 1A)
    const rawHead = header;
    const rawBody = rows.slice(0, Math.min(rows.length, 30));
    renderTable("tblRaw", rawHead, rawBody);

    // Build numeric matrix P using the same file
    // rows: each row starts with label then m values
    if(rows.length < m){
      alert("Baris tak cukup untuk matrix square.");
      return;
    }

    const rowLabels = rows.slice(0, m).map(r=> String(r[0]??"").trim());
    const P = Array.from({length:m}, ()=> Array.from({length:m}, ()=> NaN));

    for(let i=0;i<m;i++){
      const r = rows[i];
      if(!r || r.length < m+1){
        alert("Ada row tak cukup kolum. Pastikan setiap row ada m value.");
        return;
      }
      for(let j=0;j<m;j++){
        const v = parseRatio(r[j+1]);
        if(!isFinite(v) || v<=0){
          alert(`Value invalid dekat row ${rowLabels[i]||("row"+(i+1))}, col ${crit[j]}: "${r[j+1]}"`);
          return;
        }
        P[i][j]=v;
      }
    }

    // Step 1B table
    const pHead = [" "].concat(crit);
    const pBody = [];
    for(let i=0;i<m;i++){
      const row = [rowLabels[i] || crit[i] || ("C"+(i+1))];
      for(let j=0;j<m;j++){
        row.push(Number(P[i][j]).toFixed(6).replace(/\.?0+$/,"")); // cleaner
      }
      pBody.push(row);
    }
    renderTable("tblP", pHead, pBody);

    // meta: size + reciprocal check
    const err = reciprocalCheck(P);
    const ok = err <= 1e-6;
    $("metaLine").innerHTML = `m = <b>${m}</b> • ` + (ok ? `<span class="ok">reciprocal OK</span>` : `<span class="bad">reciprocal not OK</span> (max err ${err.toExponential(2)})`);

    // compute all steps 2..7
    const out = computeAll(P);

    // Step 2 Π table
    renderTable("tblPi",
      ["Criterion","Πᵢ"],
      crit.map((c,i)=> [c, out.Pi[i].toFixed(10)])
    );

    // Step 3 GM table
    renderTable("tblGM",
      ["Criterion","GMᵢ"],
      crit.map((c,i)=> [c, out.GM[i].toFixed(10)])
    );

    // Step 4 weights table
    renderTable("tblW",
      ["Criterion","ωᵢ"],
      crit.map((c,i)=> [c, out.w[i].toFixed(9)])
    );
    // draw bar
    setTimeout(()=> drawWeightsBar("wBar", crit, out.w), 10);

    // Step 5 p_ij*w_j + Pw table
    // Build header: Criterion + each (pij*w_j) + sum(Pw)
    const s5Head = ["Criterion"].concat(crit.map(c=>`pᵢⱼ·ωⱼ (${c})`)).concat(["(Pω)ᵢ"]);
    const s5Body = [];
    for(let i=0;i<m;i++){
      const row = [crit[i]];
      for(let j=0;j<m;j++) row.push(out.PWparts[i][j].toFixed(9));
      row.push(out.Pw[i].toFixed(9));
      s5Body.push(row);
    }
    renderTable("tblPWParts", s5Head, s5Body);

    // Step 6 lambda table
    renderTable("tblLam",
      ["Criterion","ωᵢ","(Pω)ᵢ","λᵢ=(Pω)ᵢ/ωᵢ"],
      crit.map((c,i)=> [c, out.w[i].toFixed(9), out.Pw[i].toFixed(9), out.lam[i].toFixed(9)])
    );
    $("lamMaxLine").textContent = `λmax = average(λᵢ) = ${out.lamMax.toFixed(9)}`;

    // Step 7 SI & CR box
    const okCR = out.CR <= 0.10;
    $("consBox").innerHTML = `
      <div>m = <b>${m}</b></div>
      <div>RI = <b>${out.RIm.toFixed(2)}</b></div>
      <div>SI = (λmax − m)/(m − 1) = <b>${out.SI.toFixed(9)}</b></div>
      <div>CR = SI/RI = <b>${out.CR.toFixed(9)}</b>
        &nbsp;→&nbsp; ${okCR ? "<span class='ok'>ACCEPTABLE (≤ 0.10)</span>" : "<span class='bad'>NOT OK (> 0.10)</span>"}
      </div>
    `;

    // show afterLoad; hide beforeLoad
    show($("beforeLoad"), false);
    show($("afterLoad"), true);

    // reset results tab to Step 2
    document.querySelectorAll(".tab").forEach(b=>b.classList.remove("active"));
    document.querySelector('.tab[data-tab="s2"]').classList.add("active");
    ["s2","s3","s4","s5","s6","s7"].forEach(id=> show($(id), id==="s2"));
  }

})();</script>
</body>
</html>
"""

html = html.replace("__INJECT_SAMPLE__", SAFE_SAMPLE)

components.html(html, height=4300, scrolling=True)
