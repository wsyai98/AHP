# app.py
import base64
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AHP-Rank", layout="wide")
APP_DIR = Path(__file__).resolve().parent

# ---------- Single source of truth for SAMPLE (PAIRWISE) CSV ----------
def load_sample_csv_text() -> str:
    # Fallback: AHP pairwise sample (7x7) using fractions
    return (
        "Criteria,B1,B2,B3,B4,B5,B6,B7\n"
        "B1,1,1/2,1/3,1/3,1/3,1/5,1\n"
        "B2,2,1,1/3,1,1/3,1/5,1\n"
        "B3,3,3,1,3,1,1,1\n"
        "B4,3,1,1/3,1,1/3,1/3,1/3\n"
        "B5,3,3,1,3,1,1,1\n"
        "B6,5,5,1,3,1,1,1\n"
        "B7,1,1,1,3,1,1,1\n"
    )

SAMPLE_CSV = load_sample_csv_text()

# ------------------------------- HTML APP -------------------------------
html = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>AHP-Rank</title>
<style>
  :root{
    --bg-dark:#0b0b0f;
    --grad-light:#e9d5ff; /* purple blush */
    --card-dark:#0f1115cc;
    --card-light:#ffffffcc;

    --text-light:#f5f5f5;

    /* PURPLE PASTEL THEME */
    --pri:#a78bfa;        /* purple */
    --pri-700:#7c3aed;    /* deeper purple */
    --pri-soft:#ede9fe;   /* very light purple */
    --border-dark:#262b35;
    --border-light:#f1f5f9;
  }

  *{box-sizing:border-box}
  html,body{height:100%;margin:0}
  html{scroll-behavior:smooth;}

  /* THEME TOKENS */
  body.dark{
    --ink:#f5f5f5;
    --grid:rgba(245,245,245,.22);
    --tt-bg:#fff;
    --tt-fg:#111;
    font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial;
    color:var(--text-light);
    background:linear-gradient(180deg,#0b0b0f 0%,#0b0b0f 35%,var(--grad-light) 120%);
  }
  body.light{
    --ink:#111;
    --grid:rgba(0,0,0,.16);
    --tt-bg:#111;
    --tt-fg:#fff;
    font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial;
    color:#111;
    background:linear-gradient(180deg,#f8fafc 0%,#f8fafc 40%,var(--pri-soft) 120%);
  }

  .container{max-width:1200px;margin:24px auto;padding:0 16px}
  .header{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
  .title{font-weight:800;font-size:28px;color:#f3e8ff} /* purple-ish white */
  body.light .title{color:#2e1065}
  .row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}

  .btn{
    display:inline-flex;align-items:center;gap:8px;
    padding:10px 14px;border-radius:12px;
    border:1px solid var(--pri-700);
    background:var(--pri);
    color:#111; /* readable on pastel */
    cursor:pointer;
    font-weight:700;
    text-decoration:none;
    user-select:none;
  }
  .btn:hover{filter:brightness(0.96)}

  .tabs{display:flex;gap:8px;margin:12px 0;position:relative;z-index:10}
  .tab{
    padding:10px 14px;border-radius:12px;
    border:1px solid #333;background:#202329;color:#ddd;cursor:pointer
  }
  body.light .tab{background:#ffffffaa;color:#111;border-color:#e5e7eb}
  .tab.active{background:var(--pri);border-color:var(--pri-700);color:#111;font-weight:800}

  /* Step navigation bar (sticky) */
  .stepbar{
    position: sticky;
    top: 12px;
    z-index: 50;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    padding: 10px 12px;
    border-radius: 16px;
    border: 1px solid rgba(167,139,250,.35);
    background: rgba(15,17,21,.55);
    backdrop-filter: blur(10px);
    margin: 12px 0 16px 0;
  }
  body.light .stepbar{
    background: rgba(255,255,255,.65);
    border-color: rgba(124,58,237,.25);
  }
  .stepbtn{
    display:inline-flex;align-items:center;gap:8px;
    padding:8px 12px;border-radius:999px;
    border:1px solid rgba(167,139,250,.6);
    background:rgba(167,139,250,.12);
    color: inherit;
    text-decoration:none;
    font-size:12px;
    font-weight:700;
    user-select:none;
  }
  .stepbtn:hover{filter:brightness(0.97)}

  .grid{display:grid;gap:16px;grid-template-columns:1fr}
  @media (min-width:1024px){.grid{grid-template-columns:1fr 2fr}}

  .card{
    border-radius:16px;padding:18px;
    border:1px solid var(--border-light);
    backdrop-filter:blur(6px)
  }
  .card.dark{background:var(--card-dark);color:#e5e7eb;border-color:var(--border-dark)}
  .card.light{background:var(--card-light);color:#111;border-color:var(--border-light)}

  /* In light mode, make "dark" cards also light */
  body.light .card.dark{background:var(--card-light);color:#111;border-color:var(--border-light)}

  .section-title{font-weight:700;font-size:18px;margin-bottom:12px;color:#e9d5ff}
  body.light .section-title{color:#5b21b6}
  .hint{font-size:12px;opacity:.85}

  .table-wrap{overflow:auto;max-height:360px}
  table{width:100%;border-collapse:collapse;font-size:14px;color:#111}
  th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #e5e7eb;white-space:nowrap}

  .chart2{width:100%;height:360px;border:1px dashed #9ca3af;border-radius:12px;background:transparent}

  .pill{
    display:inline-flex;align-items:center;gap:8px;
    padding:6px 10px;border-radius:999px;
    border:1px solid rgba(167,139,250,.6);
    background:rgba(167,139,250,.12);
    margin:0 6px 6px 0;font-size:12px;color:inherit
  }

  /* Tooltip */
  #tt{
    position:fixed;display:none;pointer-events:none;
    background:var(--tt-bg);
    color:var(--tt-fg);
    padding:6px 8px;border-radius:8px;font-size:12px;
    box-shadow:0 12px 24px rgba(0,0,0,.18);
    border:1px solid rgba(229,231,235,.9);
    z-index:9999
  }

  .ok{color:#16a34a;font-weight:900}
  .bad{color:#dc2626;font-weight:900}
</style>
</head>

<body class="dark">
<div class="container">

  <div class="header">
    <div class="title">AHP-Rank</div>
    <div class="row">
      <a class="btn" id="downloadSample">⬇️ Download Sample</a>
      <button class="btn" id="loadSample" type="button">📄 Load Sample</button>
      <button class="btn" id="themeToggle" type="button">🌙 Dark</button>
    </div>
  </div>

  <div class="tabs">
    <button type="button" class="tab active" id="tabAHP">AHP Method (Saaty)</button>
  </div>

  <!-- STEP NAV BAR (show only after results exist) -->
  <div id="stepbar" class="stepbar" style="display:none">
    <a class="stepbtn" href="#s2">Step 2 Π</a>
    <a class="stepbtn" href="#s3">Step 3 GM</a>
    <a class="stepbtn" href="#s4">Step 4 ω</a>
    <a class="stepbtn" href="#s5">Step 5 P×ω</a>
    <a class="stepbtn" href="#s6">Step 6 λmax</a>
    <a class="stepbtn" href="#s7">Step 7 SI & CR</a>
  </div>

  <div class="grid">
    <!-- LEFT -->
    <div>
      <div class="card dark">
        <div class="section-title">Step 1: Upload Pairwise Matrix (CSV)</div>
        <label for="csv1" class="btn">📤 Choose CSV</label>
        <input id="csv1" type="file" accept=".csv" style="display:none"/>
        <p class="hint">Format: first column = row labels, first row = column labels. Must be square. Values can be <b>1</b>, <b>2</b>, <b>1/3</b>, etc.</p>
      </div>

      <div id="stat" class="card dark" style="display:none">
        <div class="section-title">Consistency Summary</div>
        <div id="statBox" class="hint"></div>
        <div style="margin-top:10px">
          <span class="pill">Step 2 Π</span>
          <span class="pill">Step 3 GM</span>
          <span class="pill">Step 4 ω</span>
          <span class="pill">Step 5 P×ω</span>
          <span class="pill">Step 6 λmax</span>
          <span class="pill">Step 7 SI & CR</span>
        </div>
      </div>

      <div id="wcard" class="card dark" style="display:none">
        <div class="section-title">Weights (ω) — Bar Chart</div>
        <div class="chart2"><svg id="barW" width="100%" height="100%"></svg></div>
        <div class="hint" style="margin-top:8px">Hover bar untuk nilai ω.</div>
      </div>

      <div id="lcard" class="card dark" style="display:none">
        <div class="section-title">λᵢ Trend — Line Chart</div>
        <div class="chart2"><svg id="lineL" width="100%" height="100%"></svg></div>
        <div class="hint" style="margin-top:8px">Line menunjukkan λᵢ = (Pω)ᵢ / ωᵢ.</div>
      </div>
    </div>

    <!-- RIGHT -->
    <div>
      <div id="m1" class="card light" style="display:none">
        <div class="section-title">Pairwise Matrix P (numeric)</div>
        <div class="table-wrap"><table id="tblP"></table></div>
      </div>

      <div id="s2" class="card light" style="display:none">
        <div class="section-title">Step 2: Row Product Πᵢ = ∏ⱼ pᵢⱼ</div>
        <div class="table-wrap"><table id="tblPi"></table></div>
      </div>

      <div id="s3" class="card light" style="display:none">
        <div class="section-title">Step 3: GMᵢ = (Πᵢ)^(1/m)</div>
        <div class="table-wrap"><table id="tblGM"></table></div>
      </div>

      <div id="s4" class="card light" style="display:none">
        <div class="section-title">Step 4: Weights ωᵢ = GMᵢ / ΣGM</div>
        <div class="table-wrap"><table id="tblW"></table></div>
      </div>

      <div id="s5" class="card light" style="display:none">
        <div class="section-title">Step 5: (pᵢⱼ × ωⱼ) and (Pω)ᵢ (row-sum)</div>
        <div class="table-wrap"><table id="tblMul"></table></div>
        <div style="margin-top:10px" class="table-wrap"><table id="tblPw"></table></div>
      </div>

      <div id="s6" class="card light" style="display:none">
        <div class="section-title">Step 6: λᵢ = (Pω)ᵢ / ωᵢ and λmax</div>
        <div class="table-wrap"><table id="tblLam"></table></div>
      </div>

      <div id="s7" class="card light" style="display:none">
        <div class="section-title">Step 7: SI and CR</div>
        <div class="table-wrap"><table id="tblCR"></table></div>
      </div>
    </div>
  </div>

</div>

<!-- tooltip -->
<div id="tt"></div>

<script>
(function(){
  const $  = (id)=> document.getElementById(id);
  const show = (el,on=true)=> el.style.display = on ? "" : "none";

  // purple-ish pastels for bars
  const PASTELS = ["#a78bfa","#c4b5fd","#ddd6fe","#f5d0fe","#e9d5ff","#c7d2fe","#fbcfe8","#bfdbfe","#d1fae5","#fde68a"];

  // ---------- injected by Python ----------
  const SAMPLE_TEXT = `__INJECT_SAMPLE_CSV__`;

  $("downloadSample").href = "data:text/csv;charset=utf-8,"+encodeURIComponent(SAMPLE_TEXT);
  $("downloadSample").download = "ahp_pairwise_sample.csv";
  $("loadSample").onclick = ()=> initAHP(SAMPLE_TEXT);

  // ---------- theme toggle ----------
  const body = document.body;
  const themeBtn = $("themeToggle");
  function setTheme(isDark){
    if(isDark){
      body.classList.remove("light");
      body.classList.add("dark");
      themeBtn.innerText = "🌙 Dark";
    }else{
      body.classList.remove("dark");
      body.classList.add("light");
      themeBtn.innerText = "☀️ Light";
    }
    // redraw charts if we already computed
    if(window.__AHP__ && window.__AHP__.labels){
      const {labels,w,lam} = window.__AHP__;
      drawBar("barW", labels.map((name,i)=>({name, value:w[i]})));
      drawLine("lineL", labels.map((name,i)=>({name, x:i+1, value:lam[i]})));
    }
  }
  themeBtn.onclick = ()=> setTheme(!body.classList.contains("dark"));
  setTheme(true); // default dark

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
    return rows.map(r=> r.map(x=> String(x ?? "").trim()));
  }

  function parseRatio(v){
    const s = String(v??"").trim();
    if(!s) return NaN;
    if(s.includes("/")){
      const parts = s.split("/");
      if(parts.length!==2) return NaN;
      const a = parseFloat(parts[0].trim());
      const b = parseFloat(parts[1].trim());
      if(!isFinite(a) || !isFinite(b) || b===0) return NaN;
      return a/b;
    }
    const x = parseFloat(s);
    return isFinite(x) ? x : NaN;
  }

  // Saaty RI table
  const RI_TABLE = {1:0,2:0,3:0.58,4:0.90,5:1.12,6:1.24,7:1.32,8:1.41,9:1.45,10:1.49,11:1.51,12:1.48,13:1.56,14:1.57,15:1.59};
  function RI(m){
    if(RI_TABLE[m]!=null) return RI_TABLE[m];
    if(m<=2) return 0;
    return 1.98*(m-2)/m;
  }

  // ---------- render table ----------
  function renderTable(tableId, cols, rows){
    const tb=$(tableId); tb.innerHTML="";
    const thead=document.createElement("thead");
    const trh=document.createElement("tr");
    cols.forEach(c=>{ const th=document.createElement("th"); th.textContent=c; trh.appendChild(th); });
    thead.appendChild(trh); tb.appendChild(thead);

    const tbody=document.createElement("tbody");
    rows.forEach(r=>{
      const tr=document.createElement("tr");
      r.forEach(cell=>{
        const td=document.createElement("td");
        td.textContent = cell;
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    tb.appendChild(tbody);
  }

  // ---------- Tooltip ----------
  const TT = $("tt");
  function showTT(x,y,html){ TT.style.display="block"; TT.style.left=(x+12)+"px"; TT.style.top=(y+12)+"px"; TT.innerHTML=html; }
  function hideTT(){ TT.style.display="none"; }

  // ---------- colors from CSS vars ----------
  function ink(){ return getComputedStyle(document.body).getPropertyValue("--ink").trim() || "#111"; }
  function grid(){ return getComputedStyle(document.body).getPropertyValue("--grid").trim() || "rgba(0,0,0,.15)"; }

  // ---------- Charts ----------
  function drawBar(svgId, data){
    const svg=$(svgId); while(svg.firstChild) svg.removeChild(svg.firstChild);
    const W=(svg.getBoundingClientRect().width||800), H=(svg.getBoundingClientRect().height||360);
    svg.setAttribute("viewBox","0 0 "+W+" "+H);
    const padL=50,padR=20,padT=18,padB=44;
    const max=Math.max(...data.map(d=>d.value))||1;
    const cell=(W-padL-padR)/data.length, barW=cell*0.8;

    const axis = ink();
    const gcol = grid();

    const yAxis=document.createElementNS("http://www.w3.org/2000/svg","line");
    yAxis.setAttribute("x1",padL); yAxis.setAttribute("x2",padL); yAxis.setAttribute("y1",padT); yAxis.setAttribute("y2",H-padB); yAxis.setAttribute("stroke",axis); svg.appendChild(yAxis);
    const xAxis=document.createElementNS("http://www.w3.org/2000/svg","line");
    xAxis.setAttribute("x1",padL); xAxis.setAttribute("x2",W-padR); xAxis.setAttribute("y1",H-padB); xAxis.setAttribute("y2",H-padB); xAxis.setAttribute("stroke",axis); svg.appendChild(xAxis);

    for(let t=0;t<=5;t++){
      const val=max*t/5, y=H-padB-(H-padT-padB)*(val/max);
      const gl=document.createElementNS("http://www.w3.org/2000/svg","line");
      gl.setAttribute("x1",padL); gl.setAttribute("x2",W-padR); gl.setAttribute("y1",y); gl.setAttribute("y2",y);
      gl.setAttribute("stroke",gcol); gl.setAttribute("stroke-dasharray","3 3"); svg.appendChild(gl);
      const tx=document.createElementNS("http://www.w3.org/2000/svg","text");
      tx.setAttribute("x",padL-10); tx.setAttribute("y",y+4); tx.setAttribute("text-anchor","end");
      tx.setAttribute("font-size","12"); tx.setAttribute("fill",axis); tx.textContent=val.toFixed(3); svg.appendChild(tx);
    }

    data.forEach((d,i)=>{
      const x=padL+i*cell+(cell-barW)/2, h=(H-padT-padB)*(d.value/max), y=H-padB-h;
      const r=document.createElementNS("http://www.w3.org/2000/svg","rect");
      r.setAttribute("x",x); r.setAttribute("y",y); r.setAttribute("width",barW); r.setAttribute("height",h);
      r.setAttribute("fill", PASTELS[i%PASTELS.length]);
      r.addEventListener("mousemove",(ev)=> showTT(ev.clientX, ev.clientY, `<b>${d.name}</b><br/>ω = ${d.value.toFixed(6)}`));
      r.addEventListener("mouseleave", hideTT);
      svg.appendChild(r);

      const lbl=document.createElementNS("http://www.w3.org/2000/svg","text");
      lbl.setAttribute("x",x+barW/2); lbl.setAttribute("y",H-12); lbl.setAttribute("text-anchor","middle");
      lbl.setAttribute("font-size","12"); lbl.setAttribute("fill",axis); lbl.textContent=d.name; svg.appendChild(lbl);
    });
  }

  function drawLine(svgId, data){
    const svg=$(svgId); while(svg.firstChild) svg.removeChild(svg.firstChild);
    const W=(svg.getBoundingClientRect().width||800), H=(svg.getBoundingClientRect().height||300);
    svg.setAttribute("viewBox","0 0 "+W+" "+H);
    const padL=50,padR=20,padT=14,padB=30;

    const axis = ink();
    const gcol = grid();

    const maxY=Math.max(...data.map(d=>d.value))||1;
    const minX=1, maxX=Math.max(...data.map(d=>d.x))||1;

    const sx=(x)=> padL+(W-padL-padR)*((x-minX)/(maxX-minX||1));
    const sy=(v)=> H-padB-(H-padT-padB)*(v/maxY);

    const yAxis=document.createElementNS("http://www.w3.org/2000/svg","line");
    yAxis.setAttribute("x1",padL); yAxis.setAttribute("x2",padL); yAxis.setAttribute("y1",padT); yAxis.setAttribute("y2",H-padB); yAxis.setAttribute("stroke",axis); svg.appendChild(yAxis);
    const xAxis=document.createElementNS("http://www.w3.org/2000/svg","line");
    xAxis.setAttribute("x1",padL); xAxis.setAttribute("x2",W-padR); xAxis.setAttribute("y1",H-padB); xAxis.setAttribute("y2",H-padB); xAxis.setAttribute("stroke",axis); svg.appendChild(xAxis);

    // gridlines
    for(let t=0;t<=5;t++){
      const val=maxY*t/5, y=H-padB-(H-padT-padB)*(val/maxY);
      const gl=document.createElementNS("http://www.w3.org/2000/svg","line");
      gl.setAttribute("x1",padL); gl.setAttribute("x2",W-padR); gl.setAttribute("y1",y); gl.setAttribute("y2",y);
      gl.setAttribute("stroke",gcol); gl.setAttribute("stroke-dasharray","3 3"); svg.appendChild(gl);
    }

    const p=document.createElementNS("http://www.w3.org/2000/svg","path");
    let dstr="";
    data.sort((a,b)=> a.x-b.x).forEach((pt,i)=>{
      const x=sx(pt.x), y=sy(pt.value);
      dstr += (i===0? "M":"L")+x+" "+y+" ";

      const c=document.createElementNS("http://www.w3.org/2000/svg","circle");
      c.setAttribute("cx",x); c.setAttribute("cy",y); c.setAttribute("r","4"); c.setAttribute("fill",axis);
      c.addEventListener("mousemove",(ev)=> showTT(ev.clientX, ev.clientY, `<b>${pt.name}</b><br/>λᵢ = ${pt.value.toFixed(6)}`));
      c.addEventListener("mouseleave", hideTT);
      svg.appendChild(c);

      const tx=document.createElementNS("http://www.w3.org/2000/svg","text");
      tx.setAttribute("x",x); tx.setAttribute("y",H-10);
      tx.setAttribute("text-anchor","middle"); tx.setAttribute("font-size","11"); tx.setAttribute("fill",axis);
      tx.textContent = pt.x; svg.appendChild(tx);
    });
    p.setAttribute("d", dstr.trim());
    p.setAttribute("fill","none");
    p.setAttribute("stroke",axis);
    p.setAttribute("stroke-width","2");
    svg.appendChild(p);
  }

  // ---------- AHP core ----------
  function initAHP(txt){
    const arr=parseCSVText(txt);
    if(!arr.length) return;

    const header = arr[0];
    if(header.length<2) return;

    const colLabels = header.slice(1);     // columns after first
    const rowLabels = arr.slice(1).map(r=> r[0]).filter(x=> x!=="" );

    const m = rowLabels.length;
    if(m<2){ alert("Need at least 2 criteria."); return; }
    if(colLabels.length !== m){ alert("Matrix must be square: number of columns must equal number of rows."); return; }

    // Build numeric matrix P
    const P = [];
    for(let i=0;i<m;i++){
      const r = arr[i+1];
      if(!r || r.length < m+1){ alert("Some rows are incomplete."); return; }
      const row = [];
      for(let j=0;j<m;j++){
        const v = parseRatio(r[j+1]);
        if(!isFinite(v) || v<=0){ alert(`Invalid value at row ${rowLabels[i]}, col ${colLabels[j]}`); return; }
        row.push(v);
      }
      P.push(row);
    }

    // Reciprocal check
    let maxErr = 0;
    for(let i=0;i<m;i++){
      maxErr = Math.max(maxErr, Math.abs(P[i][i]-1));
      for(let j=i+1;j<m;j++){
        maxErr = Math.max(maxErr, Math.abs(P[i][j]*P[j][i]-1));
      }
    }

    // Step 2: Pi
    const Pi = P.map(row => row.reduce((a,b)=> a*b, 1));

    // Step 3: GM
    const GM = Pi.map(v => Math.pow(v, 1/m));

    // Step 4: w
    const sumGM = GM.reduce((a,b)=> a+b, 0) || 1;
    const w = GM.map(v => v/sumGM);

    // Step 5: multiply table (p_ij * w_j) and Pw
    const Mul = [];
    const Pw = [];
    for(let i=0;i<m;i++){
      const r = [];
      let s = 0;
      for(let j=0;j<m;j++){
        const x = P[i][j]*w[j];
        r.push(x);
        s += x;
      }
      Mul.push(r);
      Pw.push(s);
    }

    // Step 6: lambda_i and lambda_max
    const lam = Pw.map((v,i)=> v/(w[i] || 1e-18));
    const lam_max = lam.reduce((a,b)=> a+b, 0)/m;

    // Step 7: SI and CR
    const SI = (m<=2) ? 0 : (lam_max - m)/(m-1);
    const ri = RI(m);
    const CR = (ri===0) ? 0 : (SI/ri);

    // store for redraw on theme toggle
    window.__AHP__ = {labels: rowLabels, w, lam};

    // ---------- Render tables ----------
    const Pcols = [" "].concat(colLabels);
    const Prows = rowLabels.map((rl,i)=> [rl].concat(P[i].map(x=> x.toFixed(6))) );
    renderTable("tblP", Pcols, Prows);

    renderTable("tblPi", ["Criteria","Π_i"], rowLabels.map((rl,i)=> [rl, Pi[i].toFixed(9)]) );
    renderTable("tblGM", ["Criteria","GM_i"], rowLabels.map((rl,i)=> [rl, GM[i].toFixed(9)]) );
    renderTable("tblW", ["Criteria","GM_i","ΣGM","ω_i"], rowLabels.map((rl,i)=> [rl, GM[i].toFixed(9), sumGM.toFixed(9), w[i].toFixed(9)]) );

    const mulCols = [" "].concat(colLabels);
    const mulRows = rowLabels.map((rl,i)=> [rl].concat(Mul[i].map(x=> x.toFixed(9))) );
    renderTable("tblMul", mulCols, mulRows);
    renderTable("tblPw", ["Criteria","(Pω)_i (row-sum)"], rowLabels.map((rl,i)=> [rl, Pw[i].toFixed(9)]) );

    renderTable("tblLam", ["Criteria","ω_i","(Pω)_i","λ_i"], rowLabels.map((rl,i)=> [rl, w[i].toFixed(9), Pw[i].toFixed(9), lam[i].toFixed(9)]) );

    renderTable("tblCR",
      ["m","λmax","SI","RI","CR","Decision"],
      [[
        String(m),
        lam_max.toFixed(9),
        SI.toFixed(9),
        ri.toFixed(4),
        CR.toFixed(9),
        (CR<=0.10 ? "ACCEPTABLE (≤0.10)" : "NOT OK (>0.10)")
      ]]
    );

    // ---------- Summary box ----------
    const ok = (CR<=0.10);
    $("statBox").innerHTML = `
      <div>Reciprocal check max error: <b>${maxErr.toExponential(2)}</b></div>
      <div style="margin-top:6px"><b>λmax</b> = ${lam_max.toFixed(9)}</div>
      <div><b>SI</b> = ${SI.toFixed(9)}</div>
      <div><b>RI</b> = ${ri.toFixed(4)}</div>
      <div><b>CR</b> = ${CR.toFixed(9)} &nbsp;→&nbsp; ${ok ? '<span class="ok">ACCEPTABLE</span>' : '<span class="bad">NOT OK</span>'}</div>
    `;

    // ---------- Charts ----------
    drawBar("barW", rowLabels.map((name,i)=> ({name, value:w[i]})));
    drawLine("lineL", rowLabels.map((name,i)=> ({name, x:i+1, value:lam[i]})));

    // ---------- Show sections ----------
    show($("stepbar"),true);
    show($("stat"),true);
    show($("wcard"),true);
    show($("lcard"),true);
    show($("m1"),true);
    show($("s2"),true);
    show($("s3"),true);
    show($("s4"),true);
    show($("s5"),true);
    show($("s6"),true);
    show($("s7"),true);
  }

  // file upload
  $("csv1").onchange = (e)=>{
    const f=e.target.files[0];
    if(!f) return;
    const r=new FileReader();
    r.onload=()=> initAHP(String(r.result));
    r.readAsText(f);
  };

  // IMPORTANT:
  // Start EMPTY until user uploads CSV or clicks "Load Sample".
  // (If you want auto preload sample, uncomment next line)
  // initAHP(SAMPLE_TEXT);

})();
</script>
</body>
</html>
"""

# inject sample
html = html.replace("__INJECT_SAMPLE_CSV__", SAMPLE_CSV.replace("`", "\\`"))

components.html(html, height=4200, scrolling=True)
