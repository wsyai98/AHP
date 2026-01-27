# app.py
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AHP-Rank", layout="wide")

# ================= SAMPLE CSV =================
SAMPLE_CSV = """Criteria,B1,B2,B3,B4,B5
B1,1,1/2,1/3,1/3,1
B2,2,1,1/3,1,1
B3,3,3,1,3,1
B4,3,1,1/3,1,1/2
B5,1,1,1,2,1
"""

html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>AHP Rank</title>

<style>
:root{{
  --dark-bg:#0b0b0f;
  --light-bg:#f8fafc;

  --purple:#a78bfa;
  --purple-dark:#7c3aed;
  --purple-soft:#e9d5ff;

  --card-dark:#0f1115cc;
  --card-light:#ffffffcc;

  --text-dark:#e5e7eb;
  --text-light:#111;
}}

body{{
  margin:0;
  font-family:system-ui,Segoe UI,Roboto,Arial;
}}

body.dark{{
  background:linear-gradient(180deg,var(--dark-bg),var(--dark-bg),var(--purple-soft));
  color:var(--text-dark);
}}

body.light{{
  background:linear-gradient(180deg,var(--light-bg),var(--light-bg),var(--purple-soft));
  color:var(--text-light);
}}

.container{{max-width:1200px;margin:24px auto;padding:0 16px}}

.header{{display:flex;justify-content:space-between;align-items:center}}
.title{{font-size:28px;font-weight:900;color:var(--purple)}}

.btn{{
  padding:10px 14px;
  border-radius:12px;
  border:1px solid var(--purple-dark);
  background:var(--purple);
  color:#111;
  font-weight:800;
  cursor:pointer;
}}

.toggle{{
  padding:10px 14px;
  border-radius:12px;
  border:1px solid #999;
  background:transparent;
  font-weight:800;
  cursor:pointer;
}}

.grid{{display:grid;grid-template-columns:1fr 2fr;gap:16px}}

.card{{
  padding:18px;
  border-radius:16px;
  border:1px solid #ddd;
}}

.dark .card{{background:var(--card-dark)}}
.light .card{{background:var(--card-light)}}

.section-title{{font-weight:800;margin-bottom:10px;color:var(--purple)}}

.chart{{width:100%;height:360px;border:1px dashed #aaa;border-radius:12px}}

table{{width:100%;border-collapse:collapse}}
th,td{{padding:8px;border-bottom:1px solid #ccc;font-size:14px;text-align:center}}

</style>
</head>

<body class="dark">

<div class="container">

  <div class="header">
    <div class="title">AHP-Rank (Purple Pastel)</div>
    <div>
      <button class="btn" id="loadSample">Load Sample</button>
      <button class="toggle" id="themeBtn">🌙 Dark</button>
    </div>
  </div>

  <div class="grid">

    <!-- LEFT -->
    <div>
      <div class="card">
        <div class="section-title">Upload Pairwise CSV</div>
        <input type="file" id="csvFile"/>
      </div>

      <div class="card">
        <div class="section-title">Weights (ω)</div>
        <svg id="barW" class="chart"></svg>
      </div>

      <div class="card">
        <div class="section-title">λᵢ Trend — Line Chart</div>
        <svg id="lineL" class="chart"></svg>
      </div>
    </div>

    <!-- RIGHT -->
    <div>
      <div class="card">
        <div class="section-title">Pairwise Matrix (Numeric)</div>
        <table id="tblP"></table>
      </div>

      <div class="card">
        <div class="section-title">Weights Table</div>
        <table id="tblW"></table>
      </div>

      <div class="card">
        <div class="section-title">Consistency</div>
        <table id="tblC"></table>
      </div>
    </div>

  </div>
</div>

<script>
const SAMPLE = `{SAMPLE_CSV.replace("`","\\`")}`;

let dark=true;
const body=document.body;
const themeBtn=document.getElementById("themeBtn");

themeBtn.onclick=()=>{
  dark=!dark;
  body.className = dark?"dark":"light";
  themeBtn.innerText = dark?"🌙 Dark":"☀️ Light";
  redraw();
};

function parseRatio(v){{
  if(v.includes("/")){{
    const p=v.split("/");
    return parseFloat(p[0])/parseFloat(p[1]);
  }}
  return parseFloat(v);
}}

function parseCSV(txt){{
  return txt.trim().split("\\n").map(r=>r.split(","));
}}

function renderTable(id,head,rows){{
  const t=document.getElementById(id);
  let html="<tr>"+head.map(h=>`<th>${{h}}</th>`).join("")+"</tr>";
  rows.forEach(r=>{{
    html+="<tr>"+r.map(c=>`<td>${{c}}</td>`).join("")+"</tr>";
  }});
  t.innerHTML=html;
}}

let labels=[], weights=[], lambdas=[];

function computeAHP(txt){{
  const arr=parseCSV(txt);
  labels = arr.slice(1).map(r=>r[0]);
  const m=labels.length;

  const P=[];
  for(let i=0;i<m;i++){{
    const row=[];
    for(let j=0;j<m;j++){{
      row.push(parseRatio(arr[i+1][j+1]));
    }}
    P.push(row);
  }}

  const Pi=P.map(r=>r.reduce((a,b)=>a*b,1));
  const GM=Pi.map(v=>Math.pow(v,1/m));
  const s=GM.reduce((a,b)=>a+b,0);
  weights=GM.map(v=>v/s);

  const Pw=P.map((r,i)=> r.reduce((s,v,j)=>s+v*weights[j],0));
  lambdas=Pw.map((v,i)=> v/weights[i]);
  const lamMax=lambdas.reduce((a,b)=>a+b,0)/m;

  const SI=(lamMax-m)/(m-1);
  const RI={{1:0,2:0,3:0.58,4:0.90,5:1.12}}[m]||1.12;
  const CR=SI/RI;

  renderTable("tblP",[" "].concat(labels),
    labels.map((l,i)=> [l].concat(P[i].map(x=>x.toFixed(3)))) );

  renderTable("tblW",["Criteria","ω"],
    labels.map((l,i)=>[l,weights[i].toFixed(6)]));

  renderTable("tblC",
    ["λmax","SI","RI","CR","Decision"],
    [[lamMax.toFixed(6),SI.toFixed(6),RI.toFixed(2),CR.toFixed(6),CR<=0.1?"ACCEPT":"REJECT"]]
  );

  redraw();
}}

function drawBar(){{
  const svg=document.getElementById("barW");
  svg.innerHTML="";
  const W=svg.clientWidth, H=svg.clientHeight;
  const max=Math.max(...weights);
  const bw=W/weights.length*0.6;

  weights.forEach((v,i)=>{{
    const h= (v/max)*(H-40);
    const x=i*(W/weights.length)+(W/weights.length-bw)/2;
    const y=H-h-20;

    const r=document.createElementNS("http://www.w3.org/2000/svg","rect");
    r.setAttribute("x",x);
    r.setAttribute("y",y);
    r.setAttribute("width",bw);
    r.setAttribute("height",h);
    r.setAttribute("fill","#a78bfa");
    svg.appendChild(r);

    const t=document.createElementNS("http://www.w3.org/2000/svg","text");
    t.setAttribute("x",x+bw/2);
    t.setAttribute("y",H-5);
    t.setAttribute("text-anchor","middle");
    t.setAttribute("fill", dark?"#fff":"#000");
    t.textContent=labels[i];
    svg.appendChild(t);
  }});
}}

function drawLine(){{
  const svg=document.getElementById("lineL");
  svg.innerHTML="";
  const W=svg.clientWidth, H=svg.clientHeight;
  const max=Math.max(...lambdas);

  let d="";
  lambdas.forEach((v,i)=>{{
    const x=i*(W/(lambdas.length-1));
    const y=H-(v/max)*(H-40)-20;
    d += (i==0?"M":"L")+x+" "+y+" ";
  }});

  const p=document.createElementNS("http://www.w3.org/2000/svg","path");
  p.setAttribute("d",d);
  p.setAttribute("fill","none");
  p.setAttribute("stroke", dark?"#f5f3ff":"#111");
  p.setAttribute("stroke-width","3");
  svg.appendChild(p);

  lambdas.forEach((v,i)=>{{
    const x=i*(W/(lambdas.length-1));
    const y=H-(v/max)*(H-40)-20;

    const c=document.createElementNS("http://www.w3.org/2000/svg","circle");
    c.setAttribute("cx",x);
    c.setAttribute("cy",y);
    c.setAttribute("r",4);
    c.setAttribute("fill", dark?"#fff":"#000");
    svg.appendChild(c);
  }});
}}

function redraw(){{
  if(weights.length>0){{
    drawBar();
    drawLine();
  }}
}}

document.getElementById("loadSample").onclick=()=>computeAHP(SAMPLE);

document.getElementById("csvFile").addEventListener("change",e=>{{
  const f=e.target.files[0];
  if(!f) return;
  const r=new FileReader();
  r.onload=()=>computeAHP(r.result);
  r.readAsText(f);
}});

// auto load sample
computeAHP(SAMPLE);

</script>
</body>
</html>
"""

components.html(html, height=2600, scrolling=True)
