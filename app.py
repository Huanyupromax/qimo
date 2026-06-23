import sys,os,json,hashlib,uuid,random,time
sys.stdout.reconfigure(encoding="utf-8")
from flask import Flask,jsonify,request
import pathlib
from database import UserDB
from scoring import ScoringEngine as SE
app=Flask(__name__)
app.secret_key=os.urandom(24).hex()
HTML=pathlib.Path(__file__).parent/"template.html";HTML=HTML.read_text(encoding="utf-8") if HTML.exists() else "<h1>No template</h1>"
db=UserDB();sessions={}
ds=None;k=os.environ.get("DEEPSEEK_API_KEY","")
if k:
    import httpx,openai
    ds=openai.OpenAI(api_key=k,base_url="https://api.deepseek.com",http_client=httpx.Client(verify=False))
def hp(p,s=""):return hashlib.sha256((p+s).encode()).hexdigest()
RR={"AI是否应该取代人类工作":{"pro":["AI提升效率"],"con":["失业问题"]}}
@app.route("/")
def idx():return HTML
@app.route("/api/register",methods=["POST"])
def reg():
    d=request.get_json(force=True);u=d.get("username","").strip();p=d.get("password","")
    if not u or not p:return jsonify({"success":False,"message":"请填写"})
    if len(p)<4:return jsonify({"success":False,"message":"密码太短"})
    if db.user_exists(u):return jsonify({"success":False,"message":"已注册"})
    s=os.urandom(8).hex();db.add_user(u,hp(p,s),s)
    return jsonify({"success":True,"message":"注册成功"})
@app.route("/api/login",methods=["POST"])
def log():
    d=request.get_json(force=True);u=d.get("username","").strip();p=d.get("password","")
    if not u or not p:return jsonify({"success":False,"message":"请填写"})
    user=db.get_user(u)
    if not user or user["password_hash"]!=hp(p,user["salt"]):return jsonify({"success":False,"message":"错误"})
    return jsonify({"success":True,"message":"登录成功"})
@app.route("/api/debate/start",methods=["POST"])
def ds():
    d=request.get_json(force=True);t=d.get("topic","")
    if not t:return jsonify({"success":False})
    sid=str(uuid.uuid4());sessions[sid]={"sid":sid,"topic":t,"conv":[],"r":0,"st":"active"}
    return jsonify({"success":True,"session_id":sid,"message":random.choice(RR.get(t,{}).get("pro",["请发言..."]))})
@app.route("/api/debate/message",methods=["POST"])
def dm():
    d=request.get_json(force=True);sid=d.get("session_id","");msg=d.get("message","")
    if not sid or sid not in sessions:return jsonify({"success":False})
    s=sessions[sid]
    if s["st"]!="active":return jsonify({"success":False})
    s["conv"].append({"role":"user","content":msg})
    return jsonify({"success":True,"message":random.choice(RR.get(s["topic"],{}).get("con",["请继续..."]))})
@app.route("/api/debate/end",methods=["POST"])
def de():
    sid=request.get_json(force=True).get("session_id","")
    if sid in sessions:sessions[sid]["st"]="ended"
    return jsonify({"success":True})
@app.route("/api/scoring/report",methods=["POST"])
def sr():
    d=request.get_json(force=True);sid=d.get("session_id","")
    if not sid or sid not in sessions:return jsonify({"success":False})
    s=sessions[sid];se=SE()
    return jsonify({"success":True,"report":se.report(user=d.get("username",""),topic=s["topic"],rd=s["r"])})
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
