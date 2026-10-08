"use strict";
const $ = id => document.getElementById(id);
let state = null;
let viewSymbol = "BTC";
let working = false;
const money = (v, d = 2) => Number.isFinite(+v) ? (Number(v) < 0 ? "-$" : "$") + Math.abs(Number(v)).toLocaleString("en-US", {minimumFractionDigits:d,maximumFractionDigits:d}) : "--";
const signed = (v, d = 2) => (Number(v) > 0 ? "+" : "") + money(v, d);
const num = (v,d=2) => Number.isFinite(+v) ? Number(v).toLocaleString("en-US",{minimumFractionDigits:d,maximumFractionDigits:d}) : "--";
const safe = (el, text) => {el.textContent = String(text ?? "--");};
const colorize = (el, v) => {el.classList.toggle("green", +v >= 0);el.classList.toggle("red", +v < 0);};
function row(label,value) {
  const el=document.createElement("div");el.className="riskrow";
  const left=document.createElement("span"),right=document.createElement("strong");
  left.textContent=label;right.textContent=String(value??"--");el.append(left,right);return el;
}
function renderChart() {
  const canvas=$("priceChart"),dpr=Math.min(2,devicePixelRatio||1);
  const w=canvas.clientWidth||700,h=canvas.clientHeight||315;
  if(canvas.width!==Math.round(w*dpr)||canvas.height!==Math.round(h*dpr)) {
    canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);
  }
  const ctx=canvas.getContext("2d"); ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);
  const entries=state?.history?.[viewSymbol] || [];
  const points=entries.map(x=>Number(x.p)).filter(Number.isFinite);
  safe($("samples"), points.length+" / 90");
  const price=state?.prices?.[viewSymbol];
  safe($("mid"), price ? money(price,price>=100?2:4):"--");
  safe($("chartTitle"),viewSymbol+" / PUBLIC MID PRICES");
  if(points.length<2) {
    ctx.font="13px ui-monospace, monospace";ctx.fillStyle="#aa93b7";
    ctx.fillText("Waiting for 2+ actual market observations...", 14,h/2);
    safe($("chartRange"),"No chart data yet");return;
  }
  const min=Math.min(...points),max=Math.max(...points),range=Math.max((max-min)*1.3,min*.00005);
  const lo=(min+max)/2-range/2,hi=(min+max)/2+range/2, x=i=>18+(w-75)*i/(points.length-1);
  const y=p=>17+(hi-p)/(hi-lo)*(h-47);
  ctx.font="10px ui-monospace, monospace";
  for(let i=0;i<5;i++){const yy=18+i*(h-47)/4;ctx.strokeStyle="#4e2a5b80";ctx.lineWidth=1;ctx.setLineDash([3,7]);ctx.beginPath();ctx.moveTo(14,yy);ctx.lineTo(w-55,yy);ctx.stroke();ctx.setLineDash([]);
    ctx.fillStyle="#a58db6";ctx.fillText(num(hi-i*(hi-lo)/4,price>=100?0:3),w-51,yy-4);}
  const positive=points.at(-1)>=points[0],stroke=positive?"#3df5b8":"#ff567a";
  const grad=ctx.createLinearGradient(0,0,0,h);grad.addColorStop(0,positive?"#3df5b83f":"#ff567a3f");grad.addColorStop(1,"#10061a00");
  ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(x(i),y(p)):ctx.moveTo(x(i),y(p)));
  ctx.lineTo(x(points.length-1),h-20);ctx.lineTo(x(0),h-20);ctx.closePath();ctx.fillStyle=grad;ctx.fill();
  ctx.strokeStyle=stroke;ctx.lineWidth=2.3;ctx.shadowColor=stroke;ctx.shadowBlur=11;ctx.beginPath();
  points.forEach((p,i)=>i?ctx.lineTo(x(i),y(p)):ctx.moveTo(x(i),y(p)));ctx.stroke();ctx.shadowBlur=0;
  ctx.fillStyle=stroke;ctx.beginPath();ctx.arc(x(points.length-1),y(points.at(-1)),4,0,Math.PI*2);ctx.fill();
  safe($("chartRange"),num(min,2)+" - "+num(max,2));
}
function render(){
  if(!state)return;
  const s=state,risk=s.risk||{},svc=s.service||{};
  safe($("equity"), money(s.equity));
  safe($("net"),signed(s.net_pnl));colorize($("net"),s.net_pnl);
  safe($("today"),signed(s.daily_realized_pnl));colorize($("today"),s.daily_realized_pnl);
  safe($("wr"),num(s.win_rate,1)+"%");
  safe($("count"),s.trades_count+" closed paper trades");
  safe($("exposure"),s.positions.length+"/"+risk.max_positions);
  safe($("marketAge"),s.feed_age_seconds==null?"NO FEED":s.feed_age_seconds+"s age");
  $("feed").className="chip "+(s.feed_status==="LIVE"?"good":"bad");
  safe($("feed"),s.feed_status==="LIVE"?"● FEED LIVE":"● FEED STALE");
  $("autostatus").className="chip "+(s.killed?"bad":s.paused?"warn":"good");
  safe($("autostatus"),s.killed?"KILL LOCKED":s.paused?"PAUSED":svc.auto_paper?"AUTO PAPER":"MANUAL ONLY");
  safe($("serviceStatus"),svc.last_poll_error?"FEED ERROR":"SERVER ONLINE");
  const pairs=$("pairs");pairs.replaceChildren();
  for(const symbol of ["BTC","ETH","SOL"]){
    const el=document.createElement("div");el.className="pair"+(symbol===viewSymbol?" active":"");
    const one=document.createElement("div"),two=document.createElement("div");
    const b=document.createElement("b");b.textContent=symbol;one.append(b);
    const name=document.createElement("div");name.className="n";name.textContent=symbol+"-PERP / INDICATIVE MID";one.append(name);
    const p=document.createElement("div");p.className="price";p.textContent=s.prices?.[symbol]?money(s.prices[symbol],symbol==="BTC"?1:symbol==="ETH"?2:3):"--";
    const note=document.createElement("div");note.className="n";note.style.textAlign="right";
    note.textContent=s.positions.find(q=>q.symbol===symbol)?.side||"NO POSITION";two.append(p,note);
    el.append(one,two);el.title="View "+symbol;el.style.cursor="pointer";el.addEventListener("click",()=>{
      viewSymbol=symbol;$("symbol").value=symbol;render();});
    pairs.append(el);
  }
  renderChart();
  const pos=$("positions");pos.replaceChildren();
  for(const p of s.positions){
    const tr=document.createElement("tr");
    const fields=[p.symbol+"-PERP",p.side,money(p.entry,2),
      money(p.stop,2)+" / "+money(p.target,2),signed(p.upnl)];
    fields.forEach((f,i)=>{const td=document.createElement("td");td.textContent=f;
      if(i===1||i===4)td.className=(i===1?(p.side==="LONG"):p.upnl>=0)?"green":"red";
      tr.append(td);});pos.append(tr);
  }
  if(!s.positions.length){const tr=document.createElement("tr"),td=document.createElement("td");
    td.colSpan=5;td.className="empty";td.textContent="No open paper positions";tr.append(td);pos.append(tr);}
  safe($("posCount"),s.positions.length+" OPEN");
  const riskEl=$("risk");riskEl.replaceChildren(
    row("Risk per trade",risk.risk_per_trade_pct+"%"),
    row("Max notional",risk.max_notional_pct+"% equity"),
    row("Daily realized stop",risk.daily_loss_limit_pct+"%"),
    row("Stop / target",risk.stop_pct+"% / "+risk.take_profit_pct+"%"),
    row("Trade cooldown",risk.cooldown_seconds+"s"),
    row("Fee per side",risk.fee_bps+" bps"),
    row("Slippage per side",risk.slippage_bps+" bps")
  );
  const ops=$("operations");ops.replaceChildren(
    row("Mode","PAPER ONLY"),
    row("Strategy",svc.ai_enabled?"FOUR-MODEL AI":"RULES ONLY"),
    row("AI setup",svc.models_configured?"4/4 configured":"Missing keys/model IDs"),
    row("Autopilot",svc.auto_paper?"ENABLED":"DISABLED"),
    row("Polling", "Every 5 seconds (default)"),
    row("Data",s.feed_status),
    row("Last market error",svc.last_poll_error||"None"),
    row("Controls",svc.controls_available?"Token configured":"Disabled"),
    row("Protection",s.killed?"KILLED":s.paused?"PAUSED":"ACTIVE")
  );
  const active=s.signal||{};
  safe($("aiMode"),!svc.ai_enabled?"RULES ONLY":svc.models_configured?"4 AI CONNECTED":"KEYS MISSING");
  safe($("decision"),active.symbol?(active.symbol+" "+active.side+" · "+active.source+" · "+(active.reason||"")):"No active candidate");
  for(const model of ["HAIKU","GPT","GROK","GEMINI"]){
    const vote=(active.votes||[]).find(v=>v.model===model);
    const el=$("vote-"+model);safe(el,vote?vote.side+" "+Math.round(vote.confidence*100)+"%":(!svc.ai_enabled?"DISABLED":svc.models_configured?"WAITING":"OFFLINE"));
    el.className="vote "+(vote?.side==="LONG"?"green":vote?.side==="SHORT"?"red":"muted");
  }
  const eventBox=$("events");eventBox.replaceChildren();
  (s.events||[]).forEach(e=>{
    const line=document.createElement("div");line.className="log";
    const at=document.createElement("time");at.textContent=new Date(e.at*1000).toISOString().slice(11,19);
    const typ=document.createElement("b");typ.textContent=e.type;
    const msg=document.createElement("span");msg.textContent=e.message;
    line.append(at,typ,msg);eventBox.append(line);
  });
  safe($("logCount"),s.events?.length||0);
  safe($("updated"),"Last screen refresh: "+new Date().toISOString().replace("T"," ").slice(0,19)+" UTC");
}
async function refresh(){
  if(working) return;working=true;
  try {
    const response=await fetch("/api/status",{cache:"no-store"});
    if(!response.ok)throw new Error("HTTP "+response.status);
    state=await response.json();render();
  }catch(err){$("feed").className="chip bad";safe($("feed"),"● BACKEND OFFLINE");
    safe($("actionMsg"),"Cannot connect to server: "+err.message);}
  finally{working=false;}
}
async function send(endpoint,payload){
  const token=$("token").value.trim();
  if(!token){safe($("actionMsg"),"Enter CONTROL_TOKEN to authorize paper orders");return;}
  safe($("actionMsg"),"Submitting...");
  try{
    const response=await fetch(endpoint,{method:"POST",headers:{"Content-Type":"application/json","Authorization":"Bearer "+token},body:JSON.stringify(payload)});
    const json=await response.json();
    safe($("actionMsg"),json.ok?"OK · "+JSON.stringify(json):"Blocked · "+json.reason);
  }catch(err){safe($("actionMsg"),"Request failed: "+err.message);}
  refresh();
}
document.querySelectorAll("[data-order]").forEach(b=>b.addEventListener("click",()=>send("/api/order",{symbol:$("symbol").value,side:b.dataset.order})));
document.querySelectorAll("[data-control]").forEach(b=>b.addEventListener("click",()=>{
  if(b.dataset.control==="kill"&&!confirm("Latch the PAPER kill switch and attempt to flatten current paper positions? Restart will NOT clear the lock automatically."))return;
  send("/api/control",{action:b.dataset.control});
}));
$("close").addEventListener("click",()=>send("/api/close",{symbol:$("symbol").value}));
$("refresh").addEventListener("click",refresh);
$("symbol").addEventListener("change",()=>{viewSymbol=$("symbol").value;renderChart();});
window.addEventListener("resize",()=>{if(state)renderChart();});
function tickClock(){safe($("clock"),"UTC "+new Date().toISOString().slice(11,19));}
tickClock();refresh();setInterval(tickClock,1000);setInterval(refresh,5000);
