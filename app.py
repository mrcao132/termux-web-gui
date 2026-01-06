from flask import Flask, render_template_string, request, redirect, jsonify
import datetime, os, json

app = Flask(__name__)

UPLOAD_DIR = "static"
BG_PATH = os.path.join(UPLOAD_DIR, "bg.jpg")
SCORE_FILE = "scores.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ================= SCORE =================
def load_scores():
    if not os.path.exists(SCORE_FILE):
        return []
    with open(SCORE_FILE, "r") as f:
        return json.load(f)

def save_score(score):
    scores = load_scores()
    scores.append(score)
    scores = sorted(scores, reverse=True)[:5]
    with open(SCORE_FILE, "w") as f:
        json.dump(scores, f)

# ================= LOG =================
def log_access(page):
    print("\n[ACCESS]")
    print("IP :", request.remote_addr)
    print("Page :", page)
    print("UA :", request.headers.get("User-Agent"))
    print("Time :", datetime.datetime.now())
    print("-" * 40)

# ================= BACKGROUND (FIX TRẮNG / ĐEN) =================
def bg_style():
    if os.path.exists(BG_PATH):
        ts = int(datetime.datetime.now().timestamp())
        return f"background-color:#111;background-image:url('/{BG_PATH}?v={ts}');background-size:cover;background-position:center;background-attachment:fixed;"
    return "background:#111;"

def device_info(extra=""):
    return f"""IP: {request.remote_addr}
UA: {request.headers.get("User-Agent")}
Time: {datetime.datetime.now()}
{extra}"""

# ================= GUI MAIN =================
HTML_MAIN = """
<!DOCTYPE html>
<html>
<head>
<title>Termux GUI</title>
<style>
body { font-family:Arial; color:white; text-align:center; margin-top:30px; }
button { font-size:16px; padding:14px 30px; border:none; border-radius:10px; cursor:pointer; margin:12px; }
.game { background:#00bfff; }
.panel { background:#ff5555; }
.upload { background:#00ff99; color:black; }
.box { width:90%; max-width:700px; margin:auto; background:rgba(0,0,0,.7); padding:20px; border-radius:10px; text-align:left; }
pre { background:black; padding:10px; border-radius:6px; }
</style>
</head>

<body style="{{ bg }}">
<h1>🧪 Termux Web GUI</h1>

<div class="box"><pre>{{ info }}</pre></div>

<div class="box">
<form action="/upload-bg" method="post" enctype="multipart/form-data">
<input type="file" name="bg" accept="image/*" required>
<button class="upload">⬆ Upload Background</button>
</form>
</div>

<form action="/dino"><button class="game">🦖 CHƠI DINO GAME</button></form>
<form action="/panel"><button class="panel">🔴 GUI KHÁC</button></form>
</body>
</html>
"""

# ================= DINO GAME =================
HTML_DINO = """
<!DOCTYPE html>
<html>
<head>
<title>Dino Game</title>
<style>
body { margin:0; color:white; }
canvas { display:block; margin:auto; background:rgba(0,0,0,.5); image-rendering:pixelated; }
h2, #controls, #scorebox { text-align:center; background:rgba(0,0,0,.7); padding:8px; }
button { padding:6px 14px; margin:4px; border:none; border-radius:6px; cursor:pointer; }
.active { background:#00ff99; color:black; }
</style>
</head>

<body style="{{ bg }}">
<h2>🦖 Dino Game – Space / Click để nhảy</h2>

<div id="controls">
<b>Độ khó:</b>
<button onclick="setLevel(1)" id="lv1">1</button>
<button onclick="setLevel(2)" id="lv2" class="active">2</button>
<button onclick="setLevel(3)" id="lv3">3</button>
<button onclick="restart()">🔄 Chơi lại</button>
</div>

<canvas id="game" width="800" height="300"></canvas>

<div id="scorebox">
<h3>🏆 TOP 5 SCORE</h3>
<ol id="scores"></ol>
</div>

<script>
let scores={{ scores }};
document.getElementById("scores").innerHTML =
 scores.map((s,i)=>`<li>Mốc ${i+1}: ${s}</li>`).join("");

let gravity=1.2, speed=6;
function setLevel(lv){
 document.querySelectorAll("#controls button").forEach(b=>b.classList.remove("active"));
 document.getElementById("lv"+lv).classList.add("active");
 if(lv===1){gravity=0.9; speed=4}
 if(lv===2){gravity=1.2; speed=6}
 if(lv===3){gravity=1.6; speed=9}
}

const c=document.getElementById("game"),ctx=c.getContext("2d");
let dino, obs, score, over, frame=0, running=false;

function init(){
 dino={x:50,y:220,w:32,h:32,vy:0,j:false,leg:0};
 obs=[];
 score=0;
 over=false;
 spawn();
}

function restart(){
 running=false;
 init();
 running=true;
 requestAnimationFrame(loop);
}

function spawn(){
 let r=Math.random(), o={};
 if(r<0.4)o={w:20,h:30,y:230};
 else if(r<0.7)o={w:30,h:50,y:210};
 else o={w:30,h:20,y:Math.random()>0.5?190:160};
 o.x=820;
 obs.push(o);
}

function drawDino(){
 ctx.fillStyle="white";
 ctx.fillRect(dino.x,dino.y,dino.w,dino.h-8);
 ctx.fillRect(dino.x+(dino.leg?18:4),dino.y+dino.h-8,6,8);
 ctx.fillRect(dino.x+(dino.leg?4:18),dino.y+dino.h-8,6,8);
 if(frame%10===0)dino.leg^=1;
}

function loop(){
 if(!running) return;
 ctx.clearRect(0,0,800,300);
 frame++;

 drawDino();

 obs.forEach(o=>{
  ctx.fillRect(o.x,o.y,o.w,o.h);
  o.x-=speed;
 });

 if(obs[0].x+obs[0].w<0){obs.shift();spawn();score++}
 ctx.fillText("Score: "+score,10,20);

 if(dino.j){
  dino.vy+=gravity;
  dino.y+=dino.vy;
  if(dino.y>=220){dino.y=220;dino.j=false;dino.vy=0}
 }

 obs.forEach(o=>{
  if(dino.x<o.x+o.w&&dino.x+dino.w>o.x&&dino.y<o.y+o.h&&dino.y+dino.h>o.y) over=true;
 });

 if(over){
  running=false;
  fetch("/save-score",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({score})});
  ctx.fillText("GAME OVER",360,150);
 } else {
  requestAnimationFrame(loop);
 }
}

document.addEventListener("keydown",e=>{
 if(e.code==="Space"&&!dino.j){dino.j=true;dino.vy=-18}
});
c.addEventListener("click",()=>{if(!dino.j){dino.j=true;dino.vy=-18}});

init();
running=true;
requestAnimationFrame(loop);
</script>
</body>
</html>
"""

# ================= PANEL =================
HTML_PANEL = """
<!DOCTYPE html>
<html>
<head>
<title>Panel</title>
<style>
body { color:white; text-align:center; }
.box { background:rgba(0,0,0,.7); padding:20px; width:90%; max-width:600px; margin:auto; border-radius:10px; }
</style>
</head>

<body style="{{ bg }}">
<h1>🧩 PANEL</h1>
<div class="box"><pre>{{ info }}</pre></div>
<form action="/"><button>⬅ Back</button></form>
</body>
</html>
"""

# ================= ROUTES =================
@app.route("/")
def index():
    log_access("/")
    return render_template_string(HTML_MAIN, info=device_info(), bg=bg_style())

@app.route("/dino")
def dino():
    log_access("/dino")
    return render_template_string(HTML_DINO, bg=bg_style(), scores=load_scores())

@app.route("/save-score", methods=["POST"])
def save_score_api():
    save_score(request.json.get("score",0))
    return jsonify(ok=True)

@app.route("/upload-bg", methods=["POST"])
def upload_bg():
    f=request.files.get("bg")
    if f and f.filename.lower().endswith((".jpg",".jpeg",".png",".webp")):
        f.save(BG_PATH)
    return redirect("/")

@app.route("/panel")
def panel():
    return render_template_string(HTML_PANEL, info=device_info("Panel"), bg=bg_style())

app.run(host="0.0.0.0", port=5000)

