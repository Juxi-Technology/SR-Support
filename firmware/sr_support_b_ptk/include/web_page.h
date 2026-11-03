// Status page served on the SR-Support access point (port 80).
// Self-contained: inline CSS/JS, no external assets (the robot's AP has
// no internet). Data comes from /data as JSON every 300 ms.
#pragma once

static const char WEB_PAGE[] PROGMEM = R"HTML(<!doctype html>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SR-Support</title>
<style>
body{background:#14161a;color:#dfe3ea;font-family:system-ui,sans-serif;
margin:0;padding:18px;max-width:420px}
h1{font-size:18px;color:#8ab4ff;margin:0 0 10px}
.card{background:#1d2129;border-radius:12px;padding:14px;margin-bottom:12px}
.row{display:flex;justify-content:space-between;gap:12px;margin:4px 0;
font-variant-numeric:tabular-nums}
.k{color:#9aa4b2}.v{font-weight:600}
.big{font-size:20px;color:#7ee08a}
.bar{height:10px;background:#2a2f3a;border-radius:5px;overflow:hidden;
margin-top:8px}
.fill{height:100%;background:#4f8cff;width:0%;transition:width .2s}
</style>
<h1>SR-Support status</h1>
<div class="card">
<div class="row"><span class="k">State</span>
<span class="v big" id="st">-</span></div>
<div class="bar"><div class="fill" id="upbar"></div></div>
<div class="row"><span class="k">up z</span><span class="v" id="upz">-</span></div>
</div>
<div class="card">
<div class="row"><span class="k">up x,y,z</span><span class="v" id="up">-</span></div>
<div class="row"><span class="k">BigArm / SmallArm</span><span class="v" id="q">-</span></div>
<div class="row"><span class="k">Get-up</span><span class="v" id="ph">-</span></div>
<div class="row"><span class="k">Switches</span><span class="v" id="sw">-</span></div>
<div class="row"><span class="k">Uptime</span><span class="v" id="ms">-</span></div>
</div>
<script>
var P=['roll_pos','roll_neg','pitch_pos','pitch_neg'];
function $(i){return document.getElementById(i)}
async function poll(){try{
var d=await (await fetch('/data')).json();
$('st').textContent=d.state;
$('upz').textContent=d.upz.toFixed(3);
$('upbar').style.width=Math.round((d.upz+1)/2*100)+'%';
$('up').textContent=d.upx.toFixed(2)+', '+d.upy.toFixed(2)+', '+d.upz.toFixed(2);
$('q').textContent=d.q1.toFixed(2)+' / '+d.q2.toFixed(2);
$('ph').textContent=d.exec?(P[d.pose]+' ph '+d.ph+' t '+d.tick):'-';
$('sw').textContent=d.sw;
$('ms').textContent=Math.round(d.ms/1000)+' s';
}catch(e){$('st').textContent='offline'}}
setInterval(poll,300);poll();
</script>
)HTML";
