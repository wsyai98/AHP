# app.py
import base64
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AHP-Rank", layout="wide")
APP_DIR = Path(__file__).resolve().parent

# ---------- Single source of truth for SAMPLE (PAIRWISE) CSV ----------
def load_sample_csv_text() -> str:
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
  --grad-light:#e9d5ff;
  --card-dark:#0f1115cc;
  --card-light:#ffffffcc;
  --text-light:#f5f5f5;

  --pri:#a78bfa;
  --pri-700:#7c3aed;
  --pri-soft:#ede9fe;

  --border-dark:#262b35;
  --border-light:#f1f5f9;
}

*{box-sizing:border-box}
html,body{height:100%;margin:0}
body.dark{
  font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial;
  color:var(--text-light);
  background:linear-gradient(180deg,#0b0b0f 0%,#0b0b0f 35%,var(--grad-light) 120%);
}

body.light{
  font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial;
  color:#111;
  background:linear-gradient(180deg,#f8fafc 0%,#f8fafc 40%,var(--pri-soft) 120%);
}

body.light .card.dark{
  background:var(--card-light);
  color:#111;
  border-color:var(--border-light);
}

body.light .card.light{
  background:var(--card-light);
  color:#111;
  border-color:var(--border-light);
}

body.light table{color:#111}
body.light .section-title{color:#7c3aed}

.container{max-width:1200px;margin:24px auto;padding:0 16px}
.header{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
.title{font-weight:800;font-size:28px;color:#f3e8ff}

.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}

.btn{
  display:inline-flex;align-items:center;gap:8px;
  padding:10px 14px;border-radius:12px;
  border:1px solid var(--pri-700);
  background:var(--pri);
  color:#111;
  cursor:pointer;
  font-weight:700;
  text-decoration:none;
}

.btn:hover{filter:brightness(0.96)}

.tabs{display:flex;gap:8px;margin:12px 0}
.tab{
  padding:10px 14px;border-radius:12px;
  border:1px solid #333;background:#202329;color:#ddd;cursor:pointer
}
.tab.active{background:var(--pri);border-color:var(--pri-700);color:#111;font-weight:800}

.grid{display:grid;gap:16px;grid-template-columns:1fr}
@media (min-width:1024px){.grid{grid-template-columns:1fr 2fr}}

.card{
  border-radius:16px;padding:18px;
  border:1px solid var(--border-light);
  backdrop-filter:blur(6px)
}
.card.dark{background:var(--card-dark);color:#e5e7eb;border-color:var(--border-dark)}
.card.light{background:var(--card-light);color:#111;border-color:var(--border-light)}

.section-title{font-weight:700;font-size:18px;margin-bottom:12px;color:#e9d5ff}
.hint{font-size:12px;opacity:.85}

.table-wrap{overflow:auto;max-height:360px}
table{width:100%;border-collapse:collapse;font-size:14px;color:#111}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #e5e7eb;white-space:nowrap}

.chart2{width:100%;height:360px;border:1px dashed #9ca3af;border-radius:12px;background:transparent}

#tt{position:fixed;display:none;pointer-events:none;background:#fff;color:#111;
  padding:6px 8px;border-radius:8px;font-size:12px;
  box-shadow:0 12px 24px rgba(0,0,0,.18);border:1px solid #e5e7eb;z-index:9999}

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
      <button class="btn" id="loadSample">📄 Load Sample</button>
      <button class="btn" id="themeToggle">🌙 Dark</button>
    </div>
  </div>

  <div class="tabs">
    <button type="button" class="tab active">AHP Method (Saaty)</button>
  </div>

  <div class="grid">
    <div>
      <div class="card dark">
        <div class="section-title">Step 1: Upload Pairwise Matrix (CSV)</div>
        <label for="csv1" class="btn">📤 Choose CSV</label>
        <input id="csv1" type="file" accept=".csv" style="display:none"/>
      </div>

      <div id="stat" class="card dark" style="display:none">
        <div class="section-title">Consistency Summary</div>
        <div id="statBox" class="hint"></div>
      </div>

      <div id="wcard" class="card dark" style="display:none">
        <div class="section-title">Weights (ω) — Bar Chart</div>
        <div class="chart2"><svg id="barW" width="100%" height="100%"></svg></div>
      </div>

      <div id="lcard" class="card dark" style="display:none">
        <div class="section-title">λᵢ Trend — Line Chart</div>
        <div class="chart2"><svg id="lineL" width="100%" height="100%"></svg></div>
      </div>
    </div>

    <div>
      <div id="m1" class="card light" style="display:none">
        <div class="section-title">Pairwise Matrix P</div>
        <div class="table-wrap"><table id="tblP"></table></div>
      </div>
    </div>
  </div>

</div>

<div id="tt"></div>

<script>
(function(){
  const $  = (id)=> document.getElementById(id);
  const show = (el,on=true)=> el.style.display = on ? "" : "none";

  const PASTELS = ["#a78bfa","#c4b5fd","#ddd6fe","#f5d0fe","#e9d5ff","#c7d2fe"];

  /* ---------- THEME TOGGLE ---------- */
  let isDark = true;
  const themeBtn = $("themeToggle");
  const body = document.body;

  themeBtn.onclick = ()=>{
    isDark = !isDark;
    if(isDark){
      body.classList.remove("light");
      body.classList.add("dark");
      themeBtn.innerText = "🌙 Dark";
    }else{
      body.classList.remove("dark");
      body.classList.add("light");
      themeBtn.innerText = "☀️ Light";
    }

    if(window.__AHP_DATA__){
      const {labels,w,lam} = window.__AHP_DATA__;
      drawBar("barW", labels.map((name,i)=> ({name, value:w[i]})));
      drawLine("lineL", labels.map((name,i)=> ({name, x:i+1, value:lam[i]})));
    }
  };

  /* ---------- SAMPLE ---------- */
  const SAMPLE_TEXT = `__INJECT_SAMPLE_CSV__`;

  $("downloadSample").href = "data:text/csv;charset=utf-8,"+encodeURIComponent(SAMPLE_TEXT);
  $("downloadSample").download = "ahp_pairwise_sample.csv";
  $("loadSample").onclick = ()=> initAHP(SAMPLE_TEXT);

  /* ---------- CSV ---------- */
  function parseCSVText(text){
    return text.trim().split("\n").map(r=>r.split(",").map(x=>x.trim()));
  }

  function parseRatio(v){
    if(v.includes("/")){
      const [a,b]=v.split("/");
      return parseFloat(a)/parseFloat(b);
    }
    return parseFloat(v);
  }

  const RI_TABLE = {1:0,2:0,3:0.58,4:0.90,5:1.12,6:1.24,7:1.32};

  function drawBar(svgId, data){
    const svg=$(svgId); svg.innerHTML="";
    const W=800,H=360;
    svg.setAttribute("viewBox","0 0 "+W+" "+H);
    const max=Math.max(...data.map(d=>d.value));
    data.forEach((d,i)=>{
      const x=80+i*80;
      const h=250*(d.value/max);
      const y=300-h;
      svg.innerHTML+=`<rect x="${x}" y="${y}" width="40" height="${h}" fill="${PASTELS[i%PASTELS.length]}"/>`;
      svg.innerHTML+=`<text x="${x+20}" y="330" text-anchor="middle" font-size="12">${d.name}</text>`;
    });
  }

  function drawLine(svgId, data){
    const svg=$(svgId); svg.innerHTML="";
    const W=800,H=300;
    svg.setAttribute("viewBox","0 0 "+W+" "+H);
    let path="M ";
    data.forEach((d,i)=>{
      const x=80+i*80;
      const y=250-(d.value*120);
      path+=`${x} ${y} `;
      svg.innerHTML+=`<circle cx="${x}" cy="${y}" r="4" fill="#111"/>`;
    });
    svg.innerHTML+=`<path d="${path}" fill="none" stroke="#111" stroke-width="2"/>`;
  }

  function initAHP(txt){
    const arr=parseCSVText(txt);
    const labels = arr.slice(1).map(r=>r[0]);
    const m=labels.length;

    const P=[];
    for(let i=0;i<m;i++){
      const row=[];
      for(let j=0;j<m;j++){
        row.push(parseRatio(arr[i+1][j+1]));
      }
      P.push(row);
    }

    const Pi = P.map(r=>r.reduce((a,b)=>a*b,1));
    const GM = Pi.map(v=>Math.pow(v,1/m));
    const sumGM = GM.reduce((a,b)=>a+b,0);
    const w = GM.map(v=>v/sumGM);

    const Pw=[];
    for(let i=0;i<m;i++){
      let s=0;
      for(let j=0;j<m;j++) s+=P[i][j]*w[j];
      Pw.push(s);
    }

    const lam = Pw.map((v,i)=> v/w[i]);
    const lam_max = lam.reduce((a,b)=>a+b,0)/m;
    const SI = (lam_max-m)/(m-1);
    const RI = RI_TABLE[m] || 1.32;
    const CR = SI/RI;

    window.__AHP_DATA__ = { labels, w, lam };

    $("statBox").innerHTML = `
      <div><b>λmax</b> = ${lam_max.toFixed(6)}</div>
      <div><b>SI</b> = ${SI.toFixed(6)}</div>
      <div><b>CR</b> = ${CR.toFixed(6)}</div>
      <div>${CR<=0.1 ? '<span class="ok">ACCEPTABLE</span>' : '<span class="bad">NOT OK</span>'}</div>
    `;

    drawBar("barW", labels.map((n,i)=>({name:n,value:w[i]})));
    drawLine("lineL", labels.map((n,i)=>({name:n,x:i+1,value:lam[i]})));

    show($("stat"),true);
    show($("wcard"),true);
    show($("lcard"),true);
    show($("m1"),true);
  }

  $("csv1").onchange=(e)=>{
    const f=e.target.files[0];
    if(!f) return;
    const r=new FileReader();
    r.onload=()=>initAHP(r.result);
    r.readAsText(f);
  };

  initAHP(SAMPLE_TEXT);
})();
</script>
</body>
</html>
"""

html = html.replace("__INJECT_SAMPLE_CSV__", SAMPLE_CSV.replace("`","\\`"))
components.html(html, height=4200, scrolling=True)
