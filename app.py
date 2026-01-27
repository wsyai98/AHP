# app.py
import base64
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AHP — Section 3 (GM + Consistency)", layout="wide")
APP_DIR = Path(__file__).resolve().parent

# ---------- Sample CSV (pairwise matrix only) ----------
SAMPLE_CSV = """B,B1,B2,B3,B4,B5,B6,B7
B1,1,1/2,1/3,1/3,1/3,1/5,1
B2,2,1,1/3,1,1/3,1/5,1
B3,3,3,1,3,1,1,1
B4,3,1,1/3,1,1/3,1/3,1/3
B5,3,3,1,3,1,1,1
B6,5,5,1,3,1,1,1
B7,1,1,1,3,1,1,1
"""

def escape_for_js_template_literal(s: str) -> str:
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

SAFE_SAMPLE = escape_for_js_template_literal(SAMPLE_CSV)

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
<title>AHP — Section 3</title>
<style>
  :root{
    --bg1:#0b0b10; --bg2:#141227;

    --lav:#f3e8ff;
    --lav2:#e9d5ff;
    --vio:#c4b5fd;
    --vio2:#a78bfa;
    --vio3:#8b5cf6;

    --text:#f8fafc;
    --cardDark: rgba(18,16,35,.78);
    --cardLight: rgba(255,255,255,.82);

    --bdDark:#2c2a45;
    --bdLight:#e5e7eb;

    --btn:#a78bfa;
    --btnBd:#8b5cf6;

    --muted: rgba(255,255,255,.78);
  }
  *{box-sizing:border-box}
  html,body{height:100%;margin:0}
  body{font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial}

  body.theme-dark{
    color:var(--text);
    background:
      radial-gradient(1200px 600px at 20% 0%, rgba(167,139,250,.25), transparent 55%),
      radial-gradient(900px 500px at 85% 10%, rgba(196,181,253,.22), transparent 60%),
      linear-gradient(180deg, var(--bg1) 0%, var(--bg2) 55%, rgba(243,232,255,.28) 140%);
  }
  body.theme-light{
    color:#111;
    background:
      radial-gradient(1100px 520px at 15% 0%, rgba(167,139,250,.22), transparent 55%),
      radial-gradient(900px 460px at 85% 10%, rgba(196,181,253,.18), transparent 60%),
      linear-gradient(180deg, #fbfaff 0%, #f8fafc 55%, var(--lav) 140%);
  }

  .container{max-width:1200px;margin:24px auto;padding:0 16px}
  .header{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;gap:12px;flex-wrap:wrap}
  .title{
    font-weight:900;font-size:28px;letter-spacing:.2px;
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
    text-decoration:none;font-weight:900;
  }
  .btn:hover{filter:brightness(0.98); transform: translateY(-.5px)}
  .toggle{
    padding:8px 12px;border-radius:14px;
    border:1px solid var(--bdDark);
    background: rgba(255,255,255,.06);
    color:#eee;cursor:pointer;font-weight:900;
  }
  body.theme-light .toggle{background:#fff;color:#111;border-color:#cbd5e1}

  .grid{display:grid;gap:16px;grid-template-columns:1fr}
  @media (min-width:1024px){.grid{grid-template-columns:1fr 2fr}}

  .card{border-radius:18px;padding:18px;border:1px solid var(--bdLight);backdrop-filter: blur(8px)}
  .card.dark{background:var(--cardDark);color:#e5e7eb;border-color:var(--bdDark)}
  .card.light{background:var(--cardLight);color:#111;border-color:var(--bdLight)}
  body.theme-light .card.dark{background:#fff;color:#111;border-color:#e5e7eb}

  .section-title{font-weight:900;font-size:18px;margin-bottom:12px;color: var(--lav2)}
  body.theme-light .section-title{color:#4c1d95}

  .hint{font-size:12px;opacity:.86}
  .mini{font-size:12px;opacity:.9;line-height:1.55}
  .pill{
    display:inline-flex;align-items:center;gap:8px;
    padding:6px 10px;border-radius:999px;
    border:1px solid #c4b5fd;
    background: rgba(237,233,254,.7);
    margin:0 6px 6px 0;font-size:12px;color:#111;font-weight:900;
  }
  .ok{color:#16a34a;font-weight:900}
  .bad{color:#dc2626;font-weight:900}

  .table-wrap{overflow:auto;max-height:460px}
  table{width:100%;border-collapse:collapse;font-size:14px;color:#111}
  th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #e5e7eb}
  th{background:rgba(243,232,255,.65); position:sticky; top:0}

  .subgrid{display:grid;gap:16px;grid-template-columns:1fr}
  @media (min-width:1024px){.subgrid{grid-template-columns:1fr 1fr}}

  /* simple chart */
  .chart{width:100%;height:260px;border-radius:14px;border:1px solid #e5e7eb;background:rgba(255,255,255,.55);overflow:hidden}
  body.theme-dark .chart{background:rgba(255,255,255,.10);border-color:rgba(226,232,240,.25)}
  #tt{position:fixed;display:none;pointer-events:none;background:#fff;color:#111;
      padding:6px 8px;border-radius:8px;font-size:12px;box-shadow:0 12px 24px rgba(0,0,0,.18);border:1px solid #e5e7eb;z-index:9999}
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

  <div class="grid">
    <div>
      <div class="card dark">
        <div class="section-title">Step 1 — Upload CSV (Pairwise Matrix P)</div>
        <label for="csvP" class="btn">📤 Choose CSV</label>
        <input id="csvP" type="file" accept=".csv,.txt" style="display:none"/>
        <div class="hint" style="margin-top:10px">Square matrix (m×m). First column = row labels. Values can be <b>1/3</b>.</div>
      </div>

      <div id="cardPraw" class="card dark" style="display:none;margin-top:14px">
        <div class="section-title">Step 1A — Raw CSV (preview)</div>
        <div class="table-wrap"><table id="tblRaw"></table></div>
      </div>

      <div id="cardPnum" class="card dark" style="display:none;margin-top:14px">
        <div class="section-title">Step 1B — Numeric P</div>
        <div class="mini" id="metaP"></div>
        <div class="table-wrap" style="margin-top:10px"><table id="tblP"></table></div>
      </div>
    </div>

    <div>
      <div id="cardSteps" class="card light" style="display:none">
        <div class="section-title">Results (Step 2 — Step 7)</div>
        <div style="margin-bottom:10px">
          <span class="pill">Step 2 Π</span>
          <span class="pill">Step 3 GM</span>
          <span class="pill">Step 4 ω</span>
          <span class="pill">Step 5 pᵢⱼωⱼ + Pω</span>
          <span class="pill">Step 6 λ</span>
          <span class="pill">Step 7 SI & CR</span>
        </div>

        <div class="subgrid">
          <div>
            <div class="mini" style="font-weight:900;margin:8px 0">Step 2 — Πᵢ = ∏ⱼ pᵢⱼ</div>
            <div class="table-wrap"><table id="tblPi"></table></div>

            <div class="mini" style="font-weight:900;margin:14px 0 8px">Step 3 — GMᵢ = (Πᵢ)^(1/m)</div>
            <div class="table-wrap"><table id="tblGM"></table></div>

            <div class="mini" style="font-weight:900;margin:14px 0 8px">Step 4 — ωᵢ = GMᵢ / ΣGM</div>
            <div class="table-wrap"><table id="tblW"></table></div>
          </div>

          <div>
            <div class="mini" style="font-weight:900;margin:8px 0">Weights (ω) — Bar</div>
            <div class="chart"><svg id="wbar" width="100%" height="100%"></svg></div>

            <div class="mini" style="font-weight:900;margin:14px 0 8px">Step 6 — λᵢ = (Pω)ᵢ / ωᵢ ; λmax</div>
            <div class="table-wrap"><table id="tblLam"></table></div>

            <div class="mini" style="font-weight:900;margin:14px 0 8px">Step 7 — SI & CR</div>
            <div id="consBox" class="mini"></div>
          </div>
        </div>

        <div class="mini" style="font-weight:900;margin:16px 0 8px">Step 5 — Table (pᵢⱼ × ωⱼ) and row-sum (Pω)ᵢ</div>
        <div class="table-wrap"><table id="tblMul"></table></div>
        <div class="table-wrap" style="margin-top:10px"><table id="tblPw"></table></div>

        <div class="row" style="margin-top:14px">
          <a class="btn" id="downloadOut">⬇️ Download results CSV</a>
        </div>
      </div>
    </div>
  </div>
</div>

<div id="tt"></div>

<script>
(function(){
  const $ = (id)=> document.getElementById(id);
  const show = (el,on=true)=> el.style.display = on ? "" : "none";

  // tooltip
  const TT = $("tt");
  function showTT(x,y,html){ TT.style.display="block"; TT.style.left=(x+12)+"px"; TT.style.top=(y+12)+"px"; TT.innerHTML=html; }
  function hideTT(){ TT.style.display="none"; }

  // theme
  let dark=true;
  function applyTheme(){
    document.body.classList.toggle('theme-dark', dark);
    document.body.classList.toggle('theme-light', !dark);
    $("themeToggle").textContent = dark ? "🌙 Dark" : "☀️ Light";
  }
  $("themeToggle").onclick = ()=>{ dark=!dark; applyTheme(); };
  applyTheme();

  // sample injection
  const SAMPLE_TEXT = `__INJECT_SAMPLE_CSV__`;
  $("downloadSample").href = "data:text/csv;charset=utf-8," + encodeURIComponent(SAMPLE_TEXT);
  $("downloadSample").download = "sample_pairwise_matrix.csv";
  $("loadSample").onclick = ()=> initAll(SAMPLE_TEXT);

  // RI table
  const RI_TABLE = {1:0,2:0,3:0.58,4:0.90,5:1.12,6:1.24,7:1.32,8:1.41,9:1.45,10:1.49,11:1.51,12:1.48,13:1.56,14:1.57,15:1.59};
  function RI(m){
    if(RI_TABLE[m] !== undefined) return RI_TABLE[m];
    if(m<=2) return 0;
    return 1.98*(m-2)/m;
  }

  // CSV parser (simple)
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

  function parsePositiveNumberOrFraction(s){
    s = String(s ?? "").trim();
    if(!s) return NaN;
    s = s.replace("\\\\", "/");
    if(s.includes("/")){
      const parts = s.split("/");
      if(parts.length !== 2) return NaN;
      const num = parseFloat(parts[0].trim());
      const den = parseFloat(parts[1].trim());
      if(isFinite(num) && isFinite(den) && den !== 0) return num/den;
      return NaN;
    }
    const v = parseFloat(s);
    return v;
  }

  function renderTable(tableId, cols, rows){
    const tb=$(tableId); tb.innerHTML="";
    const thead=document.createElement("thead");
    const trh=document.createElement("tr");
    cols.forEach(c=>{ const th=document.createElement("th"); th.textContent=c; trh.appendChild(th); });
    thead.appendChild(trh); tb.appendChild(thead);
    const tbody=document.createElement("tbody");
    rows.forEach(r=>{
      const tr=document.createElement("tr");
      cols.forEach((_,ci)=>{ const td=document.createElement("td"); td.innerHTML = r[ci]; tr.appendChild(td); });
      tbody.appendChild(tr);
    });
    tb.appendChild(tbody);
  }

  // core state
  let labels = [];
  let P = [];

  function checkReciprocal(P){
    const m=P.length;
    let maxErr=0;
    for(let i=0;i<m;i++){
      maxErr = Math.max(maxErr, Math.abs(P[i][i]-1));
      for(let j=i+1;j<m;j++){
        maxErr = Math.max(maxErr, Math.abs(P[i][j]*P[j][i]-1));
      }
    }
    return maxErr;
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

  function initAll(csvText){
    const arr=parseCSVText(csvText);
    if(!arr.length) return;

    // Expect first row: header, first cell label col name, then labels
    const header = arr[0].map(x=> String(x??"").trim());
    labels = header.slice(1);
    const m = labels.length;

    // raw preview (first 12 rows)
    const rawPreview = arr.slice(0, Math.min(arr.length, 12)).map(r=> r.map(x=> String(x??"")));
    renderTable("tblRaw", header, rawPreview.slice(1).map(r=> r)); // render with header
    // The above uses header; but we want include header row? We'll show as standard table:
    // We'll re-render properly: cols = header, rows = arr.slice(1)
    renderTable("tblRaw", header, arr.slice(1, Math.min(arr.length, 12)).map(r=> r.map(x=> String(x??""))));
    show($("cardPraw"), true);

    // build numeric P from rows
    const rows = arr.slice(1).filter(r=> r.length >= m+1);
    if(rows.length !== m){
      alert("Matrix must be square m×m (rows = cols). Check CSV.");
      return;
    }

    P = Array.from({length:m}, ()=> Array.from({length:m}, ()=> 1));
    for(let i=0;i<m;i++){
      const rowLabel = String(rows[i][0]??"").trim();
      for(let j=0;j<m;j++){
        const v = parsePositiveNumberOrFraction(rows[i][j+1]);
        if(!isFinite(v) || v<=0){
          alert("Invalid value detected. Ensure all values are positive numbers or fractions (e.g., 1/3).");
          return;
        }
        P[i][j]=v;
      }
      // (optional) ignore mismatch of row labels, but keep labels from header
      (void)rowLabel;
    }

    // render numeric P
    const pCols = [" "].concat(labels);
    const pRows = labels.map((lab,i)=> {
      const row = [lab].concat(P[i].map(v=> v.toFixed(6)));
      return row;
    });
    renderTable("tblP", pCols, pRows);
    show($("cardPnum"), true);

    const recipErr = checkReciprocal(P);
    const meta = [];
    meta.push(`m = <b>${m}</b>`);
    if(recipErr <= 1e-6) meta.push(`<span class="ok">reciprocal OK</span>`);
    else meta.push(`<span class="bad">reciprocal not perfect</span> (max err ≈ ${recipErr.toExponential(2)})`);
    $("metaP").innerHTML = meta.join(" &nbsp;•&nbsp; ");

    // compute steps
    computeAndRender();
    show($("cardSteps"), true);
  }

  function computeAndRender(){
    const m = labels.length;

    // Step 2: Pi
    const Pi = new Array(m).fill(1);
    for(let i=0;i<m;i++){
      let prod=1;
      for(let j=0;j<m;j++) prod *= P[i][j];
      Pi[i]=prod;
    }

    // Step 3: GM
    const GM = Pi.map(v => Math.pow(v, 1/m));

    // Step 4: w
    const sumGM = GM.reduce((s,v)=> s+v, 0) || 1;
    const w = GM.map(v => v/sumGM);

    // Step 5: mult table pij * wj and row sums
    const Mul = Array.from({length:m}, ()=> Array.from({length:m}, ()=> 0));
    const Pw = new Array(m).fill(0);
    for(let i=0;i<m;i++){
      let s=0;
      for(let j=0;j<m;j++){
        Mul[i][j] = P[i][j] * w[j];
        s += Mul[i][j];
      }
      Pw[i]=s;
    }

    // Step 6: lambda
    const lam = Pw.map((v,i)=> v / (w[i] || 1e-18));
    const lamMax = lam.reduce((s,v)=> s+v, 0) / m;

    // Step 7: SI, CR
    const SI = (m<=1) ? 0 : (lamMax - m)/(m-1);
    const ri = RI(m);
    const CR = (ri===0) ? 0 : (SI/ri);

    // Render Step 2
    renderTable(
      "tblPi",
      ["Criterion","Πᵢ"],
      labels.map((c,i)=> [c, Pi[i].toPrecision(10)])
    );

    // Render Step 3
    renderTable(
      "tblGM",
      ["Criterion","GMᵢ"],
      labels.map((c,i)=> [c, GM[i].toPrecision(10)])
    );

    // Render Step 4
    renderTable(
      "tblW",
      ["Criterion","GMᵢ","ωᵢ"],
      labels.map((c,i)=> [c, GM[i].toPrecision(10), w[i].toFixed(9)])
    );

    // Step 5: Mul table
    const mulCols = [" "].concat(labels);
    const mulRows = labels.map((c,i)=> [c].concat(Mul[i].map(v=> v.toFixed(9))));
    renderTable("tblMul", mulCols, mulRows);

    // Step 5: Pw
    renderTable(
      "tblPw",
      ["Criterion","(Pω)ᵢ (row-sum)"],
      labels.map((c,i)=> [c, Pw[i].toFixed(9)])
    );

    // Step 6: lambdas table
    renderTable(
      "tblLam",
      ["Criterion","ωᵢ","(Pω)ᵢ","λᵢ"],
      labels.map((c,i)=> [c, w[i].toFixed(9), Pw[i].toFixed(9), lam[i].toFixed(9)])
      .concat([["","", "<b>λmax</b>", `<b>${lamMax.toFixed(9)}</b>`]])
    );

    // Step 7: consistency box
    const ok = CR <= 0.10;
    $("consBox").innerHTML = `
      <div>SI = (λmax − m)/(m − 1) = <b>${SI.toFixed(9)}</b></div>
      <div>RI = <b>${ri.toFixed(2)}</b></div>
      <div>CR = SI/RI = <b>${CR.toFixed(9)}</b> → ${
        ok ? "<span class='ok'>ACCEPTABLE (≤ 0.10)</span>" : "<span class='bad'>NOT OK (> 0.10)</span>"
      }</div>
    `;

    // download results csv
    const outRows = [["Criterion","Pi","GM","w","Pw","lambda"]];
    for(let i=0;i<m;i++){
      outRows.push([
        labels[i],
        String(Pi[i]),
        String(GM[i]),
        String(w[i]),
        String(Pw[i]),
        String(lam[i]),
      ]);
    }
    const csv = outRows.map(r=> r.map(x=>{
      const s=String(x??"");
      if(s.includes(",") || s.includes("\"") || s.includes("\n")) return `"${s.replace(/"/g,'""')}"`;
      return s;
    }).join(",")).join("\n");
    $("downloadOut").href = "data:text/csv;charset=utf-8," + encodeURIComponent(csv);
    $("downloadOut").download = "ahp_section3_results.csv";

    // draw weight bar (pastel)
    drawWeightBar("wbar", labels, w);
  }

  function drawWeightBar(svgId, labs, vals){
    const svg=$(svgId);
    while(svg.firstChild) svg.removeChild(svg.firstChild);

    const W=(svg.getBoundingClientRect().width||800);
    const H=(svg.getBoundingClientRect().height||260);
    svg.setAttribute("viewBox","0 0 "+W+" "+H);

    const padL=46,padR=16,padT=18,padB=42;
    const max = Math.max(...vals) || 1;
    const cell=(W-padL-padR)/vals.length, barW=cell*0.78;

    const PASTELS = ["#c4b5fd","#a78bfa","#e9d5ff","#ddd6fe","#f5d0fe","#bfdbfe","#bae6fd","#bbf7d0","#fde68a","#fecdd3"];

    // axes
    const yAxis=document.createElementNS("http://www.w3.org/2000/svg","line");
    yAxis.setAttribute("x1",padL); yAxis.setAttribute("x2",padL);
    yAxis.setAttribute("y1",padT); yAxis.setAttribute("y2",H-padB);
    yAxis.setAttribute("stroke","#111"); yAxis.setAttribute("opacity",".7");
    svg.appendChild(yAxis);

    const xAxis=document.createElementNS("http://www.w3.org/2000/svg","line");
    xAxis.setAttribute("x1",padL); xAxis.setAttribute("x2",W-padR);
    xAxis.setAttribute("y1",H-padB); xAxis.setAttribute("y2",H-padB);
    xAxis.setAttribute("stroke","#111"); xAxis.setAttribute("opacity",".7");
    svg.appendChild(xAxis);

    // ticks
    for(let t=0;t<=4;t++){
      const val=max*t/4;
      const y=H-padB-(H-padT-padB)*(val/max);
      const gl=document.createElementNS("http://www.w3.org/2000/svg","line");
      gl.setAttribute("x1",padL); gl.setAttribute("x2",W-padR);
      gl.setAttribute("y1",y); gl.setAttribute("y2",y);
      gl.setAttribute("stroke","#111"); gl.setAttribute("opacity",".15"); gl.setAttribute("stroke-dasharray","3 3");
      svg.appendChild(gl);

      const tx=document.createElementNS("http://www.w3.org/2000/svg","text");
      tx.setAttribute("x",padL-8); tx.setAttribute("y",y+4);
      tx.setAttribute("text-anchor","end"); tx.setAttribute("font-size","11");
      tx.setAttribute("fill","#111"); tx.setAttribute("opacity",".8");
      tx.textContent=val.toFixed(2);
      svg.appendChild(tx);
    }

    // bars
    vals.forEach((v,i)=>{
      const x=padL+i*cell+(cell-barW)/2;
      const h=(H-padT-padB)*(v/max);
      const y=H-padB-h;

      const r=document.createElementNS("http://www.w3.org/2000/svg","rect");
      r.setAttribute("x",x); r.setAttribute("y",y);
      r.setAttribute("width",barW); r.setAttribute("height",h);
      r.setAttribute("rx","10");
      r.setAttribute("fill", PASTELS[i%PASTELS.length]);
      r.setAttribute("opacity","0.95");
      r.addEventListener("mousemove",(ev)=> showTT(ev.clientX, ev.clientY, `<b>${labs[i]}</b><br/>ω = ${v.toFixed(9)}`));
      r.addEventListener("mouseleave", hideTT);
      svg.appendChild(r);

      const lbl=document.createElementNS("http://www.w3.org/2000/svg","text");
      lbl.setAttribute("x",x+barW/2); lbl.setAttribute("y",H-12);
      lbl.setAttribute("text-anchor","middle");
      lbl.setAttribute("font-size","11");
      lbl.setAttribute("fill","#111");
      lbl.setAttribute("opacity",".85");
      lbl.textContent=labs[i];
      svg.appendChild(lbl);
    });
  }

  // upload
  $("csvP").onchange = (e)=>{
    const f=e.target.files[0];
    if(!f) return;
    const r=new FileReader();
    r.onload = ()=> initAll(String(r.result));
    r.readAsText(f);
  };

  // preload sample once
  initAll(SAMPLE_TEXT);

})();
</script>
</body>
</html>
"""

html = html.replace("__INJECT_SAMPLE_CSV__", SAFE_SAMPLE)

components.html(html, height=4300, scrolling=True)
