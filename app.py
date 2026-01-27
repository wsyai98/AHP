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

  .tabs{display:flex;gap:8px;margin:12px 0}
  .tab{
    padding:10px 14px;border-radius:12px;
    border:1px solid #333;background:#202329;color:#ddd
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

  body.light .card.dark{
    background:var(--card-light);
    color:#111;
    border-color:var(--border-light);
  }

  .section-title{font-weight:700;font-size:18px;margin-bottom:12px;color:#e9d5ff}
  body.light .section-title{color:#7c3aed}

  .hint{font-size:12px;opacity:.85}
  .table-wrap{overflow:auto;max-height:360px}
  table{width:100%;border-collapse:collapse;font-size:14px;color:#111}
  th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #e5e7eb;white-space:nowrap}

  .chart2{width:100%;height:360px;border:1px dashed #9ca3af;border-radius:12px}

  .pill{
    display:inline-flex;align-items:center;gap:8px;
    padding:6px 10px;border-radius:999px;
    border:1px solid rgba(167,139,250,.6);
    background:rgba(167,139,250,.12);
    margin:0 6px 6px 0;font-size:12px;color:#fff
  }

  #tt{position:fixed;display:none;background:#fff;color:#111;
      padding:6px 8px;border-radius:8px;font-size:12px;
      box-shadow:0 12px 24px rgba(0,0,0,.18);border:1px solid #e5e7eb}

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
    <button class="tab active">AHP Method (Saaty)</button>
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
        <div class="section-title">Weights (ω)</div>
        <div class="chart2"><svg id="barW" width="100%" height="100%"></svg></div>
      </div>

      <div id="lcard" class="card dark" style="display:none">
        <div class="section-title">λᵢ Trend</div>
        <div class="chart2"><svg id="lineL" width="100%" height="100%"></svg></div>
      </div>
    </div>

    <div>
      <div id="m1" class="card light" style="display:none">
        <div class="section-title">Pairwise Matrix</div>
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

  const SAMPLE_TEXT = `__INJECT_SAMPLE_CSV__`;

  $("downloadSample").href = "data:text/csv;charset=utf-8,"+encodeURIComponent(SAMPLE_TEXT);
  $("downloadSample").download = "ahp_pairwise_sample.csv";
  $("loadSample").onclick = ()=> initAHP(SAMPLE_TEXT);

  /* ---------- DARK LIGHT MODE ---------- */
  let isDark = true;
  const themeBtn = $("themeToggle");
  const body = document.body;

  themeBtn.onclick = ()=>{
    isDark = !isDark;
    if(isDark){
      body.classList.remove("light");
      body.classList.add("dark");
      themeBtn.innerText="🌙 Dark";
    }else{
      body.classList.remove("dark");
      body.classList.add("light");
      themeBtn.innerText="☀️ Light";
    }

    if(window.__AHP_DATA__){
      const {labels,w,lam}=window.__AHP_DATA__;
      drawBar("barW", labels.map((n,i)=>({name:n,value:w[i]})));
      drawLine("lineL", labels.map((n,i)=>({name:n,x:i+1,value:lam[i]})));
    }
  };

  function parseCSVText(text){
    return text.trim().split("\n").map(r=>r.split(","));
  }

  function parseRatio(v){
    if(v.includes("/")){
      const p=v.split("/");
      return parseFloat(p[0])/parseFloat(p[1]);
    }
    return parseFloat(v);
  }

  function drawBar(svgId,data){
    const svg=$(svgId); svg.innerHTML="";
  }

  function drawLine(svgId,data){
    const svg=$(svgId); svg.innerHTML="";
  }

  function initAHP(txt){
    const arr=parseCSVText(txt);
    const labels=arr.slice(1).map(r=>r[0]);
    const P=arr.slice(1).map(r=>r.slice(1).map(parseRatio));
    const m=labels.length;

    const Pi=P.map(r=>r.reduce((a,b)=>a*b,1));
    const GM=Pi.map(v=>Math.pow(v,1/m));
    const sumGM=GM.reduce((a,b)=>a+b,0);
    const w=GM.map(v=>v/sumGM);

    const Pw=P.map((r,i)=>r.reduce((s,v,j)=>s+v*w[j],0));
    const lam=Pw.map((v,i)=>v/w[i]);
    const lam_max=lam.reduce((a,b)=>a+b,0)/m;

    window.__AHP_DATA__={labels,w,lam};

    show($("stat"),true);
    show($("wcard"),true);
    show($("lcard"),true);
    show($("m1"),true);

    $("statBox").innerHTML=`λmax = ${lam_max.toFixed(6)}`;
  }

  $("csv1").onchange=(e)=>{
    const f=e.target.files[0];
    if(!f)return;
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

# inject sample
html = html.replace("__INJECT_SAMPLE_CSV__", SAMPLE_CSV.replace("`","\\`"))

components.html(html, height=4200, scrolling=True)
