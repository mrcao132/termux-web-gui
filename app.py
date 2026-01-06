from flask import Flask, render_template_string, request, redirect, jsonify
import datetime, os, json

app = Flask(__name__)

UPLOAD_DIR = "static"
BG_PATH = os.path.join(UPLOAD_DIR, "bg.jpg")
SCORE_FILE = "scores.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ===== SCORE =====
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
    return scores

# ===== LOG =====
def log_access(page, extra=""):
    print("\n[+] ACCESS")
    print("IP        :", request.remote_addr)
    print("Page      :", page)
    print("UserAgent :", request.headers.get("User-Agent"))
    print("Time      :", datetime.datetime.now())
    if extra:
        print(extra)
    print("-" * 40)

def bg_style():
    if os.path.exists(BG_PATH):
        return f"background:url('/{BG_PATH}') center/cover fixed;"
    return "background:#111;"

def device_info(extra=""):
    return f"""IP: {request.remote_addr}
UA: {request.headers.get("User-Agent")}
Time: {datetime.datetime.now()}
{extra}"""

# ===== GUI MAIN =====
HTML_MAIN = """
<!DOCTYPE html>
<html>
<head>
<title>Termux GUI</title>
<style>
body { font-family:Arial; color:white; text-align:center; margin-top:30px; {{ bg }} }
button { font-size:16px; padding:14px 30px; border:none; border-radius:10px; cursor:pointer; margin:12px; }
.game { background:#00bfff; }
.panel { background:#ff5555; }
.upload { background:#00ff99; color:black; }
.box { width:90%; max-width:700px; margin:auto; background:rgba(0,0,0,.7); padding:20px; border-radius:10px; text-align:left; }
pre { background:black; padding:10px; border-radius:6px; }
</style>
</head>
<body>

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

# ===== DINO GAME (FULL) =====
HTML_DINO = """
<!DOCTYPE html>
<html>
<head>
<title>Dino Game</title>
<style>
body { margin:0; color:white; {{ bg }} }
canvas { display:block; margin:auto; background:rgba(0,0,0,.5); }
h2 { text-align:center; margin:0; padding:10px; background:rgba(0,0,0,.7); }
#controls, #scorebox { text-align:center; background:rgba(0,0,0,.7); padding:10px; }
#controls button { padding:6px 14px; margin:4px; border:none; border-radius:6px; cursor:pointer; }
.active { background:#00ff99; color:black; }
</style>
</head>
<body>

<h2>🦖 Dino Game – Space / Click để nhảy</h2>

<div id="controls">
<b>Độ khó:</b>
<button onclick="setLevel(1)" id="lv1">1</button>
<button onclick="setLevel(2)" id="lv2" class="active">2</button>
<button onclick="setLevel(3)" id="lv3">3</button>
</div>

<canvas id="game" width="800" height="300"></canvas>

<div id="scorebox">
<h3>🏆 TOP 5 SCORE</h3>
<ol id="scores"></ol>
</div>

<script>
let scores = {{ scores }};
document.getElementById("scores").innerHTML =
 scores.map((s,i)=>`<li>Mốc ${i+1}: ${s}</li>`).join("");

let gravity=1.2, speed=6, level=2;
function setLevel(lv){
 level=lv;
 document.querySelectorAll("#controls button").forEach(b=>b.classList.remove("active"));
 document.getElementById("lv"+lv).classList.add("active");
 if(lv===1){gravity=0.9; speed=4}
 if(lv===2){gravity=1.2; speed=6}
 if(lv===3){gravity=1.6; speed=9}
}

const c=document.getElementById("game"),ctx=c.getContext("2d");
let d={x:50,y:220,w:40,h:40,vy:0,j:false};
let obs=[], score=0, over=false;

function spawn(){
 let r=Math.random(), o;
 if(r<0.4) o={w:20,h:30,y:230};
 else if(r<0.7) o={w:30,h:50,y:210};
 else o={w:30,h:20,y:Math.random()>0.5?190:160};
 o.x=820; obs.push(o);
}
spawn();

function loop(){
 ctx.clearRect(0,0,800,300);
 ctx.fillStyle="white";
 ctx.fillRect(d.x,d.y,d.w,d.h);

 obs.forEach(o=>{
  ctx.fillRect(o.x,o.y,o.w,o.h);
  o.x-=speed;
 });

 if(obs[0].x+obs[0].w<0){obs.shift();spawn();score++}
 ctx.fillText("Score: "+score,10,20);

 if(d.j){d.vy+=gravity;d.y+=d.vy;if(d.y>=220){d.y=220;d.j=false;d.vy=0}}

 obs.forEach(o=>{
  if(d.x<o.x+o.w&&d.x+d.w>o.x&&d.y<o.y+o.h&&d.y+d.h>o.y) over=true;
 });

 if(!over) requestAnimationFrame(loop);
 else{
  fetch("/save-score",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({score})});
  ctx.fillText("GAME OVER - Reload",300,150);
 }
}

document.addEventListener("keydown",e=>{if(e.code==="Space"&&!d.j){d.j=true;d.vy=-18}});
c.addEventListener("click",()=>{if(!d.j){d.j=true;d.vy=-18}});
loop();
</script>

</body>
</html>
"""

# ===== PANEL =====
HTML_PANEL = """
<!DOCTYPE html>
<html>
<head>
<title>Panel</title>
<style>
body { color:white; text-align:center; {{ bg }} }
.box { background:rgba(0,0,0,.7); padding:20px; width:90%; max-width:600px; margin:auto; border-radius:10px; }
</style>
</head>
<body>
<h1>🧩 PANEL</h1>
<div class="box"><pre>{{ info }}</pre></div>
<form action="/"><button>⬅ Back</button></form>
</body>
</html>
"""

# ===== ROUTES =====
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
    if f: f.save(BG_PATH)
    return redirect("/")

@app.route("/panel")
def panel():
    return render_template_string(HTML_PANEL, info=device_info("Panel"), bg=bg_style())

app.run(host="0.0.0.0", port=5000)


