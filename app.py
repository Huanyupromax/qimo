import sys,os,json,hashlib,uuid,random,time
sys.stdout.reconfigure(encoding="utf-8")
from flask import Flask,jsonify,request
import pathlib
from database import UserDB
from scoring import ScoringEngine as SE
app=Flask(__name__)
app.secret_key=os.urandom(24).hex()
HTML=pathlib.Path(__file__).parent/"template.html";HTML=HTML.read_text(encoding="utf-8") if HTML.exists() else "<h1>No template</h1>"
def ai(sid):
    s=sessions[sid]
    if ds:
        try:
            r=ds.chat.completions.create(model="deepseek-chat",messages=s["conv"],temperature=0.8,max_tokens=600)
            if r.choices[0].message.content:return r.choices[0].message.content
        except:pass
    rrs=RR.get(s["topic"],{}).get(s.get("ap","pro"),["请继续发言..."])
    return random.choice(rrs)

db=UserDB();sessions={}
ds=None;k=os.environ.get("DEEPSEEK_API_KEY","")
if k:
    import httpx,openai
    ds=openai.OpenAI(api_key=k,base_url="https://api.deepseek.com",http_client=httpx.Client(verify=False))
def hp(p,s=""):return hashlib.sha256((p+s).encode()).hexdigest()
RR={"AI是否应该取代人类工作":{"pro":["AI提升生产效率，解放人类"],"con":["失业问题严重"]},"社交媒体对青少年利大于弊":{"pro":["拓展视野和社交圈"],"con":["成瘾和信息茧房"]},"大学教育是否应该免费":{"pro":["打破阶层固化"],"con":["资源浪费"]},"城市化应保留传统街区":{"pro":["保护历史文化遗产"],"con":["城市发展需要改造"]},"远程办公比办公室更好":{"pro":["节省通勤时间和成本"],"con":["缺乏团队协作"]}}
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
    d=request.get_json(force=True);t=d.get("topic","");pos=d.get("position","pro")
    if not t:return jsonify({"success":False})
    sid=str(uuid.uuid4());ap="con" if pos=="pro" else "pro"
    sm={"pro":"正方","con":"反方"}
    conv=[{"role":"system","content":"你是辩论AI。辩题:"+t+"。立场:"+sm[ap]},{"role":"user","content":"辩题:"+t+"。请开场陈词。"}]
    sessions[sid]={"sid":sid,"topic":t,"ap":ap,"conv":conv,"r":0,"st":"active"}
    msg=ai(sid);sessions[sid]["r"]=1
    return jsonify({"success":True,"session_id":sid,"message":msg})
def dm():
    d=request.get_json(force=True);sid=d.get("session_id","");msg=d.get("message","")
    if not sid or sid not in sessions:return jsonify({"success":False,"message":"会话不存在"})
    s=sessions[sid]
    if s["st"]!="active":return jsonify({"success":False,"message":"已结束"})
    s["conv"].append({"role":"user","content":msg})
    resp=ai(sid);s["conv"].append({"role":"assistant","content":resp});s["r"]+=1
    return jsonify({"success":True,"message":resp})
def de():
    sid=request.get_json(force=True).get("session_id","")
    if sid in sessions:sessions[sid]["st"]="ended"
    return jsonify({"success":True})
@app.route("/api/scoring/report",methods=["POST"])
def sr():
    d=request.get_json(force=True);sid=d.get("session_id","")
    if not sid or sid not in sessions:return jsonify({"success":False})
    s=sessions[sid];se=SE()
    for m in s["conv"]:
        if m["role"]=="user":
            se.from_nlp({"rebuttal_ratio":0.3,"logical_density":0.5,"evidence_density":0.2,"emotion_score":0.1})
    rpt=se.report(user=d.get("username",""),topic=s["topic"],rd=s["r"])
    return jsonify({"success":True,"report":rpt})
def sr():
    d=request.get_json(force=True);sid=d.get("session_id","")
    if not sid or sid not in sessions:return jsonify({"success":False})
    s=sessions[sid];se=SE()
    return jsonify({"success":True,"report":se.report(user=d.get("username",""),topic=s["topic"],rd=s["r"])})
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
