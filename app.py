# app.py
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AHP Rank", layout="wide")

SAMPLE_CSV = """
Criteria,C1,C2,C3
C1,1,1/3,3
C2,3,1,5
C3,1/3,1/5,1
"""

html = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>AHP Rank</title>

<style>
body{margin:0;font-family:Arial}
body.dark{background:#0b0b0f;color:#e5e7eb}
body.light{background:#f8fafc;color:#111}

.container{max-width:1200px;margin:20px auto;padding:10px}

.header{display:flex;justify-content:space-between;align-items:center}
.title{font-size:26px;font-weight:900;color:#a78bfa}

.btn{
  padding:10px 14px;border-radius:10px;
  background:#a78bfa;border:1px solid #7c3aed;
  font-weight:800;cursor:pointer;
}

.toggle{
  padding:10px 14px;border-radius:10px;
  background:transparent;border:1px solid #999;
  font-weight:800;cursor:pointer;
}

.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}

.card{
  border:1px solid #ccc;border-radius:14px;
  padding:14px;
}

.dark .card{background:#0f1115cc}
.light .card{background:#ffffffcc}

.section{font-weight:800;color:#a78bfa;margin-bottom:8px}

.chart{width:100%;height:300px;border:1px dashed #aaa;border-radius:10px}

table{width:100%;border-collapse:collapse}
th,td{border-bottom:1px solid #ccc;padding:6px;text-align:center}
</style>
</head>

<body class="dark">
<div class="container">

<div class="header">
  <div class="title">AHP Rank</div>
  <div>
    <button class="btn" id="loadSample">Load Sample</button>
    <button class="toggle" id="themeBtn">🌙 Dark</button>
  </div>
</div>

<div class="grid">

  <div>
    <div class="card">
      <div class="section">Upload CSV</div>
      <input type="file" id="csvFile">
    </div>

    <div class="card">
      <div class="section">Weights (ω)</div>
      <svg id="bar" class="chart"></svg>
    </div>

    <div class="card">
      <div class="section">λᵢ Line Chart</div>
      <svg id="line" class="chart"></svg>
    </div>
  </div>

  <div>
    <div class="card">
      <div class="section">Pairwise Matrix</div>
      <table id="tblP"></table>
    </div>

    <div class="card">
      <div class="section">Weights</div>
      <table id="tblW"></table>
    </div>

    <div class="card">
      <div class="section">Consistency</div>
      <table id="tblC"></table>
    </div>
  </div>

</div>
</div>

<script>
const SAMPLE = `__CSV__`;

let dark=true;
const body=document.body;
const themeBtn=document.getElementById("themeBtn");

themeBtn.onclick=()=>{
  dark=!dark;
  body.className = dark?"dark":"light";
  themeBtn.innerText = dark?"🌙 Dark":"☀️ Light";
  redraw();
};

function parseCSV(txt){
  return txt.trim().split("\\n").map(r=>r.split(","));
}

function parseRatio(v){
  if(v.includes("/")){
    let p=v.split("/");
    return parseFloat(p[0])/parseFloat(p[1]);
  }
  return parseFloat(v);
}

function table(id,head,rows){
  let h="<tr>"+head.map(x=>"<th>"+x+"</th>").join("")+"</tr>";
  rows.forEach(r=>{
    h+="<tr>"+r.map(x=>"<td>"+x+"</td>").join("")+"</tr>";
  });
  document.getElementById(id).innerHTML=h;
}

let labels=[],weights=[],lambdas=[];

function compute(txt){
  const a=parseCSV(txt);
  labels=a.slice(1).map(r=>r[0]);
  const m=labels.length;

  let P=[];
  for(let i=0;i<m;i++){
    let row=[];
    for(let j=0;j<m;j++){
      row.push(parseRatio(a[i+1][j+1]));
    }
    P.push(row);
  }

  let Pi=P.map(r=>r.reduce((x,y)=>x*y,1));
  let GM=Pi.map(v=>Math.pow(v,1/m));
  let s=GM.reduce((a,b)=>a+b,0);
  weights=GM.map(v=>v/s);

  let Pw=P.map((r,i)=> r.reduce((s,v,j)=>s+v*weights[j],0));
  lambdas=Pw.map((v,i)=> v/weights[i]);
  let lamMax=lambdas.reduce((a,b)=>a+b,0)/m;

  let SI=(lamMax-m)/(m-1);
  let RI={1:0,2:0,3:0.58}[m]||0.58;
  let CR=SI/RI;

  table("tblP",[" "].concat(labels),
    labels.map((l,i)=>[l].concat(P[i].map(x=>x.toFixed(3))))
  );

  table("tblW",["Criteria","ω"],
    labels.map((l,i)=>[l,weights[i].toFixed(6)])
  );

  table("tblC",
    ["λmax","SI","RI","CR","Decision"],
    [[lamMax.toFixed(4),SI.toFixed(4),RI.toFixed(2),CR.toFixed(4),CR<=0.1?"OK":"NOT OK"]]
  );

  redraw();
}

function drawBar(){
  const svg=document.getElementById("bar");
  svg.innerHTML="";
  const W=svg.clientWidth, H=svg.clientHeight;
  let max=Math.max(...weights);
  let bw=W/weights.length*0.6;

  weights.forEach((v,i)=>{
    let h=(v/max)*(H-40);
    let x=i*(W/weights.length)+(W/weights.length-bw)/2;
    let y=H-h-20;

    let r=document.createElementNS("http://www.w3.org/2000/svg","rect");
    r.setAttribute("x",x);r.setAttribute("y",y);
    r.setAttribute("width",bw);r.setAttribute("height",h);
    r.setAttribute("fill","#a78bfa");
    svg.appendChild(r);
  });
}

function drawLine(){
  const svg=document.getElementById("line");
  svg.innerHTML="";
  const W=svg.clientWidth, H=svg.clientHeight;
  let max=Math.max(...lambdas);

  let d="";
  lambdas.forEach((v,i)=>{
    let x=i*(W/(lambdas.length-1));
    let y=H-(v/max)*(H-40)-20;
    d+=(i==0?"M":"L")+x+" "+y+" ";
  });

  let p=document.createElementNS("http://www.w3.org/2000/svg","path");
  p.setAttribute("d",d);
  p.setAttribute("fill","none");
  p.setAttribute("stroke", dark?"#fff":"#000");
  p.setAttribute("stroke-width","3");
  svg.appendChild(p);
}

function redraw(){
  if(weights.length>0){
    drawBar();
    drawLine();
  }
}

document.getElementById("loadSample").onclick=()=>compute(SAMPLE);

document.getElementById("csvFile").addEventListener("change",e=>{
  const f=e.target.files[0];
  if(!f) return;
  const r=new FileReader();
  r.onload=()=>compute(r.result);
  r.readAsText(f);
});

compute(SAMPLE);
</script>
</body>
</html>
"""

html = html.replace("__CSV__", SAMPLE_CSV.replace("\\","\\\\").replace("`","\\`"))

components.html(html, height=2000, scrolling=True)
