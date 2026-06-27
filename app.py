import sys,os,json,hashlib,uuid,random
sys.stdout.reconfigure(encoding="utf-8")
from flask import Flask,jsonify,request
import pathlib
from database import UserDB,ReportDB
from scoring import ScoringEngine as SE
from debate_engine.prompts import build_system_prompt as bsp
from modalities.text import TextAnalyzer
app=Flask(__name__)
app.secret_key=os.urandom(24).hex()
TPL=pathlib.Path(__file__).parent/"template.html"
HTML=TPL.read_text(encoding="utf-8") if TPL.exists() else "<h1>No template</h1>"
db=UserDB()
report_db=ReportDB()
text_analyzer=TextAnalyzer()
# face/voice analyzers initialized lazily
sessions={}
# 从.env文件加载环境变量（兼容没有python-dotenv的情况）
try:
    with open(".env","r",encoding="utf-8") as _env_f:
        for _line in _env_f:
            _line=_line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k,_v=_line.split("=",1)
                os.environ[_k.strip()]=_v.strip()
except:
    pass

ds=None;k=os.environ.get("DEEPSEEK_API_KEY","")
if k:
    import httpx,openai
    ds=openai.OpenAI(api_key=k,base_url="https://api.deepseek.com",http_client=httpx.Client(verify=False))

# 知识库纠偏系统
_kb_corrector = None
_kb_mode = False

def get_kb_corrector():
    global _kb_corrector
    if _kb_corrector is None:
        from knowledge_base.enhanced_corrector import EnhancedCorrector
        from knowledge_base.models import KBConfig
        _kb_corrector = EnhancedCorrector(KBConfig(enabled=_kb_mode))
    return _kb_corrector

def hp(pw,s=""):
    return hashlib.sha256((pw+s).encode()).hexdigest()

@app.route("/")
def idx(): return HTML

@app.route("/api/register",methods=["POST"])
def reg():
    d=request.get_json(force=True)
    u=d.get("username","").strip();p=d.get("password","")
    if not u or not p: return jsonify({"success":False,"message":"请填写辩手名和密码"})
    if len(u)<2 or len(u)>20: return jsonify({"success":False,"message":"辩手名长度应在2-20个字符之间"})
    if len(p)<4: return jsonify({"success":False,"message":"密码长度至少4位"})
    if db.user_exists(u): return jsonify({"success":False,"message":"该辩手名已被注册"})
    s=os.urandom(8).hex();db.add_user(u,hp(p,s),s)
    return jsonify({"success":True,"message":"注册成功"})

@app.route("/api/login",methods=["POST"])
def log():
    d=request.get_json(force=True)
    u=d.get("username","").strip();p=d.get("password","")
    if not u or not p: return jsonify({"success":False,"message":"请填写辩手名和密码"})
    user=db.get_user(u)
    if not user or user["password_hash"]!=hp(p,user["salt"]): return jsonify({"success":False,"message":"辩手名或密码错误"})
    return jsonify({"success":True,"message":"登录成功"})

RR={"AI是否应该取代人类工作":{"pro":["AI提升效率，解放创造力","取代的是岗位而非职业，历史上每次技术革命都创造了新工种","AI在医疗、危险环境比人类更精准安全"],"con":["大规模失业影响社会稳定","许多行业需要人类的情感理解和道德判断","技术受益者往往是资本拥有者，收入差距可能扩大"]},
    "社交媒体对青少年利大于弊":{"pro":["拓展视野和社交圈","培养数字时代必备的信息素养","提供自我表达和创意展示平台"],"con":["成瘾和信息茧房问题突出","算法推荐导致思维极端化","网络霸凌频发，造成长期心理伤害"]},
    "大学教育是否应该免费":{"pro":["打破阶层固化，让每个有才华的学生都有机会","教育是公共品，国家投资获得更高人力资本回报","减轻年轻人经济压力，专注学业"],"con":["免费可能导致资源浪费","需要巨额财政支出挤占其他公共服务","适当收费能维持教育质量和竞争机制"]},
    "城市化应保留传统街区":{"pro":["传统街区承载城市历史记忆和文化基因","有利于发展文化旅游，保护文化遗产","传统社区关系网是现代小区难以替代的"],"con":["城市更新必然涉及旧区改造","传统街区基础设施落后，居住条件差","保留应与现代化改造并行"]},
    "远程办公比办公室更好":{"pro":["节省通勤成本，提高效率和满意度","可招聘全球人才不受地理限制","减少交通碳排放更环保"],"con":["削弱团队协作和即时沟通效果","模糊工作生活边界导致倦怠","办公室的企业文化无法替代"]}}

@app.route("/api/debate/start",methods=["POST"])
def dstart():
    d=request.get_json(force=True);t=d.get("topic","");pos=d.get("position","pro")
    if not t: return jsonify({"success":False})
    sid=str(uuid.uuid4());ap="con" if pos=="pro" else "pro"
    sm={"pro":"正方","con":"反方"}
    conv=[{"role":"system","content":bsp(t,ap)}]
    conv.append({"role":"user","content":f"辩题:{t}。你作为{sm[ap]}（反对{'正方观点' if ap=='con' else '反方观点'}），请开场陈词，阐述你的核心论点。要求：发言200-400字，逻辑清晰，有论据支撑。"})
    sessions[sid]={"sid":sid,"topic":t,"ap":ap,"conv":conv,"r":0,"st":"active","face_data":[],"voice_data":[],"kb_mode":_kb_mode}
    msg=ai_enhanced(sid);sessions[sid]["conv"].append({"role":"assistant","content":msg});sessions[sid]["r"]=1
    return jsonify({"success":True,"session_id":sid,"message":msg})

@app.route("/api/debate/message",methods=["POST"])
def dmsg():
    d=request.get_json(force=True);sid=d.get("session_id","");msg=d.get("message","")
    if not sid or sid not in sessions: return jsonify({"success":False,"message":"会话不存在"})
    s=sessions[sid]
    if s["st"]!="active": return jsonify({"success":False,"message":"已结束"})
    s["conv"].append({"role":"user","content":msg})
    resp=ai(sid);s["conv"].append({"role":"assistant","content":resp});s["r"]+=1
    return jsonify({"success":True,"message":resp})

@app.route("/api/debate/end",methods=["POST"])
def dend():
    sid=request.get_json(force=True).get("session_id","")
    if sid in sessions: sessions[sid]["st"]="ended"
    return jsonify({"success":True})

@app.route("/api/scoring/report",methods=["POST"])
def sr():
    d=request.get_json(force=True);sid=d.get("session_id","")
    if not sid or sid not in sessions: return jsonify({"success":False})
    s=sessions[sid];se=SE()
    if _kb_mode:
        se.set_kb_mode(True)
        se.set_kb_corrector(get_kb_corrector())
    for m in s["conv"]:
        if m["role"]=="user":
            try:
                a=text_analyzer.analyze(m["content"])
                nd={"rebuttal_ratio":a.rebuttal_ratio,"logical_density":a.logical_density/100,
                    "evidence_density":a.evidence_density/100,"emotion_score":a.emotion_score,
                    "rebuttal_sentences":a.rebuttal_sentences}
                se.from_nlp(nd)
                if _kb_mode:
                    se.apply_kb_correction(text={"dominant_emotion":"neutral","text":m["content"],**nd})
            except:
                se.from_nlp({"rebuttal_ratio":0.3,"logical_density":0.5,"evidence_density":0.2,"emotion_score":0.1})
    for fd in s.get("face_data",[]):
        try:
            se.from_face(fd)
            if _kb_mode:
                se.apply_kb_correction(face=fd)
        except: pass
    for vd in s.get("voice_data",[]):
        try:
            se.from_voice(vd)
            if _kb_mode:
                se.apply_kb_correction(voice=vd)
        except: pass
    rpt=se.report(user=d.get("username",""),topic=s["topic"],rd=s["r"])
    rid=str(uuid.uuid4());rpt["report_id"]=rid
    try: report_db.save(rid,d.get("username",""),rpt)
    except: pass
    return jsonify({"success":True,"report":rpt})

# === 知识库纠偏模式 API ===
@app.route("/api/kb/status",methods=["GET"])
def kb_status():
    corr = get_kb_corrector()
    return jsonify({"success":True,"kb_mode":_kb_mode,"stats":corr.get_stats()})

@app.route("/api/kb/toggle",methods=["POST"])
def kb_toggle():
    global _kb_mode
    d=request.get_json(force=True) or {}
    enabled = d.get("enabled")
    if enabled is not None:
        _kb_mode = bool(enabled)
    else:
        _kb_mode = not _kb_mode
    corr = get_kb_corrector()
    corr.toggle_mode(_kb_mode)
    return jsonify({"success":True,"kb_mode":_kb_mode})

@app.route("/api/kb/logs",methods=["GET"])
def kb_logs():
    corr = get_kb_corrector()
    return jsonify({"success":True,"logs":corr.get_correction_log(100)})

# === 知识库训练 API ===
@app.route("/api/kb/train",methods=["POST"])
def kb_train():
    try:
        from knowledge_base.kb_train import run_pipeline
        result = run_pipeline()
        return jsonify({"success":True,"result":result})
    except Exception as e:
        return jsonify({"success":False,"error":str(e)})

@app.route("/api/report/list",methods=["POST"])
def rlist():
    try:
        d=request.get_json(force=True);u=d.get("username","")
        if not u: return jsonify({"success":False})
        return jsonify({"success":True,"reports":report_db.list(u)})
    except Exception as e:
        print(f"rlist error: {e}")
        return jsonify({"success":False,"error":str(e)})

@app.route("/api/report/get",methods=["POST"])
def rget():
    d=request.get_json(force=True);rid=d.get("report_id","")
    if not rid: return jsonify({"success":False})
    r=report_db.get(rid)
    if r: return jsonify({"success":True,"report":r})
    return jsonify({"success":False})

@app.route("/api/report/save",methods=["POST"])
def rsave():
    d=request.get_json(force=True)
    rid=d.get("report_id","");u=d.get("username","");data=d.get("data",{})
    if not rid or not u: return jsonify({"success":False})
    try: report_db.save(rid,u,data);return jsonify({"success":True})
    except: return jsonify({"success":False})

@app.route("/api/analyze/face",methods=["POST"])
def af():
    d=request.get_json(force=True);sid=d.get("session_id","");img=d.get("image","")
    if not sid or sid not in sessions or not img: return jsonify({"success":False})
    try:
        from modalities.face import FaceAnalyzer
        fa=FaceAnalyzer()
        r=fa.analyze_base64(img)
        if r: sessions[sid]["face_data"].append(r.model_dump());return jsonify({"success":True,"emotion":r.dominant_emotion})
    except: pass
    return jsonify({"success":False})

@app.route("/api/analyze/voice",methods=["POST"])
def av():
    sid=request.form.get("session_id","")
    if not sid or sid not in sessions: return jsonify({"success":False})
    if "audio" not in request.files: return jsonify({"success":False})
    import tempfile
    try:
        from modalities.voice import VoiceAnalyzer
        va=VoiceAnalyzer()
        f=request.files["audio"];tmp=tempfile.NamedTemporaryFile(suffix=".wav",delete=False)
        f.save(tmp);tmp.close()
        r=va.analyze(tmp.name)
        os.unlink(tmp.name)
        if r: sessions[sid]["voice_data"].append(r.model_dump());return jsonify({"success":True})
    except: pass
    return jsonify({"success":False})

def ai_enhanced(sid):
    """增强版AI辩论函数 - 带对话截断和重试"""
    s = sessions[sid]
    if ds:
        for attempt in range(2):
            try:
                conv = list(s["conv"])
                if len(conv) > 13:
                    conv = conv[:1] + conv[-12:]
                if len(conv) > 1 and conv[-1]["role"] == "user":
                    conv[-1]["content"] += "\n\n请用专业辩论技巧回应：找出对方论证漏洞，引用论据支撑观点，使用逻辑推理反驳。发言300-500字。"
                r = ds.chat.completions.create(
                    model="deepseek-chat",
                    messages=conv,
                    temperature=0.85,
                    max_tokens=1500,
                    timeout=60
                )
                if r.choices[0].message.content:
                    return r.choices[0].message.content
            except Exception as e:
                print(f"DeepSeek API Error (attempt {attempt+1}): {e}")
                import time
                time.sleep(1)
    rrs = RR.get(s["topic"],{}).get(s["ap"],["请继续发言..."])
    return random.choice(rrs)

def ai(sid):
    s=sessions[sid]
    if ds:
        try:
            r=ds.chat.completions.create(model="deepseek-chat",messages=s["conv"][:],temperature=0.85,max_tokens=800)
            if r.choices[0].message.content: return r.choices[0].message.content
        except: pass
    rrs=RR.get(s["topic"],{}).get(s["ap"],["请继续发言..."])
    return random.choice(rrs)



@app.route("/api/tts",methods=["POST"])
def tts_api():
    d=request.get_json(force=True);txt=d.get("text","")
    if not txt: return jsonify({"success":False})
    import tempfile, base64, asyncio, edge_tts
    tmp=tempfile.NamedTemporaryFile(suffix=".mp3",delete=False);tmp.close()
    try:
        asyncio.run(edge_tts.Communicate(txt,"zh-CN-XiaoxiaoNeural").save(tmp.name))
        with open(tmp.name,"rb") as f: audio=base64.b64encode(f.read()).decode("ascii")
        os.unlink(tmp.name)
        return jsonify({"success":True,"audio":audio})
    except Exception as e:
        try: os.unlink(tmp.name)
        except: pass
        return jsonify({"success":False,"error":str(e)})

if __name__ == "__main__":
    import webbrowser
    webbrowser.open("http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
