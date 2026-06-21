# -*- coding: utf-8 -*-
"""
辩境 - AI 辩论系统后端
"""
import sys, os, json, hashlib, uuid, datetime
sys.stdout.reconfigure(encoding="utf-8")

# 尝试加载依赖
OPENAI_AVAILABLE = False
MONGODB_AVAILABLE = False
try:
    import openai
    OPENAI_AVAILABLE = True
except:
    pass
try:
    from pymongo import MongoClient
    MONGODB_AVAILABLE = True
except:
    pass

from flask import Flask, render_template_string, request, jsonify, send_file
import pathlib

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()

# 读取 HTML 模板
TEMPLATE_PATH = pathlib.Path(__file__).parent / "template.html"
if TEMPLATE_PATH.exists():
    HTML_TEMPLATE = TEMPLATE_PATH.read_text(encoding="utf-8")
    print("* 模板文件已加载")
else:
    HTML_TEMPLATE = "<h1>模板文件缺失</h1>"
    print("* 错误：未找到 template.html")

# ---- MongoDB 连接（可选） ----
mongo_db = None
if MONGODB_AVAILABLE:
    mongo_uri = os.environ.get("MONGODB_URI", "")
    if mongo_uri:
        try:
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
            mongo_db = client["bianjing"]
            print("* MongoDB 已连接")
        except:
            print("* MongoDB 连接失败，使用内存存储")

# ---- OpenAI 配置（可选） ----
openai_client = None
if OPENAI_AVAILABLE:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key:
        openai_client = openai.OpenAI(api_key=api_key)
        print("* OpenAI 已配置")
    else:
        print("* 未设置 OPENAI_API_KEY，使用规则辩论引擎")

# ---- 内存用户存储（MongoDB不可用时回退） ----
users_db = {}
# 内存辩论会话
debate_sessions = {}

# ---- 工具函数 ----
def hash_password(password, salt=""):
    return hashlib.sha256((password + salt).encode()).hexdigest()

# ---- 规则辩论引擎（当 OpenAI 不可用时） ----
RULE_RESPONSES = {
    "AI是否应该取代人类工作": {
        "pro": [
            "AI能大幅提升生产效率，将人类从重复劳动中解放出来，让人类专注于创造性工作。",
            "取代的是岗位而不是职业。历史上每次技术革命都创造了更多新工种，AI时代也不例外。",
            "AI在医疗诊断、危险环境作业等领域比人类更精准、更安全，取代是人类进步的必然。"
        ],
        "con": [
            "AI取代工作会导致大规模失业，社会稳定的基石——就业将受到严重冲击。",
            "许多行业需要人类的情感理解和道德判断，这是AI无法替代的核心价值。",
            "技术发展的受益者往往是资本拥有者，普通劳动者可能面临收入差距扩大。"
        ]
    },
    "社交媒体对青少年利大于弊": {
        "pro": [
            "社交媒体拓展了青少年的社交圈和学习渠道，让他们能接触多元观点和知识。",
            "社交媒体培养了数字时代必备的信息素养和网络沟通能力。",
            "社交媒体为青少年提供了自我表达和创意展示的平台。"
        ],
        "con": [
            "社交媒体成瘾严重影响青少年睡眠质量和学习效率，心理健康问题日益突出。",
            "算法推荐导致信息茧房，青少年难以接触多元观点，思维变得极端化。",
            "网络霸凌在社交媒体上频发，对青少年心理造成长期伤害。"
        ]
    },
    "大学教育是否应该免费": {
        "pro": [
            "免费大学教育能打破阶层固化，让每个有才华的学生都有接受高等教育的机会。",
            "教育是公共品，国家投资教育能获得更高的人力资本回报和经济增长。",
            "免除学费能减轻年轻人的经济压力，让他们更专注于学业而非打工还贷。"
        ],
        "con": [
            "免费教育需要巨额财政支出，可能挤占其他公共服务的预算。",
            "免费可能导致教育资源被滥用，学生缺乏珍惜意识，学习动力下降。",
            "适当收费能维持教育质量和竞争机制，免费反而可能降低教育水准。"
        ]
    },
    "城市化应保留传统街区": {
        "pro": [
            "传统街区承载着城市的历史记忆和文化基因，是城市独一无二的名片。",
            "保留传统街区有利于发展文化旅游，创造经济价值的同时保护文化遗产。",
            "传统街区的社区关系网络是现代小区难以替代的社会资本。"
        ],
        "con": [
            "城市更新和现代化必然涉及旧区改造，一味保留会阻碍城市发展。",
            "传统街区基础设施落后，居住条件差，保留不等于让居民继续生活在不便利中。",
            "保留传统应与现代化改造并行，而非完全维持原状。"
        ]
    },
    "远程办公比办公室更好": {
        "pro": [
            "远程办公节省通勤时间和成本，提高工作效率和员工满意度。",
            "远程办公让企业可以招聘全球人才，不受地理位置限制。",
            "远程办公减少了交通碳排放，对环境更加友好。"
        ],
        "con": [
            "远程办公削弱了团队协作和即时的沟通效果，创意碰撞减少。",
            "远程办公模糊了工作与生活的边界，容易导致过度工作和职业倦怠。",
            "办公室的企业文化和归属感是远程办公无法替代的。"
        ]
    }
}

RULE_FALLBACK = [
    "这个观点很有启发性。不过从另一个角度来看……",
    "我理解你的立场，但让我们换个思路——",
    "有趣的观点。不过我需要指出的是……",
    "你的论证有道理，但我们不能忽视……",
    "让我们重新审视这个问题。首先，……"
]
# ---- Flask 路由 ----
@app.route("/")
def index():
    return HTML_TEMPLATE

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"success": False, "message": "辩手名和密码不能为空"})
    if len(username) < 2 or len(username) > 20:
        return jsonify({"success": False, "message": "辩手名长度应在2-20个字符之间"})
    if len(password) < 4:
        return jsonify({"success": False, "message": "密码长度至少4位"})
    # 检查是否已注册（数据库优先）
    if mongo_db:
        if mongo_db.users.find_one({"_id": username}):
            return jsonify({"success": False, "message": "该辩手名已被注册"})
        salt = os.urandom(8).hex()
        mongo_db.users.insert_one({"_id": username, "password_hash": hash_password(password, salt), "salt": salt, "created_at": datetime.datetime.utcnow()})
    else:
        if username in users_db:
            return jsonify({"success": False, "message": "该辩手名已被注册"})
        salt = os.urandom(8).hex()
        users_db[username] = {"password_hash": hash_password(password, salt), "salt": salt}
    return jsonify({"success": True, "message": "注册成功"})

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"success": False, "message": "请填写辩手名和密码"})
    user = None
    if mongo_db:
        user = mongo_db.users.find_one({"_id": username})
    else:
        user = users_db.get(username)
    if not user:
        return jsonify({"success": False, "message": "辩手名或密码错误"})
    if user["password_hash"] != hash_password(password, user["salt"]):
        return jsonify({"success": False, "message": "辩手名或密码错误"})
    return jsonify({"success": True, "message": "登录成功"})

# ---- 辩论 API ----
@app.route("/api/debate/start", methods=["POST"])
def api_debate_start():
    data = request.get_json(force=True)
    username = data.get("username", "")
    topic = data.get("topic", "")
    position = data.get("position", "pro")  # "pro" or "con"
    if not topic:
        return jsonify({"success": False, "message": "请选择辩题"})
    session_id = str(uuid.uuid4())
    ai_position = "con" if position == "pro" else "pro"
    side_map = {"pro": "正方", "con": "反方"}

    # 构建系统提示
    system_prompt = f"你是一位辩论AI。辩题：{topic}\n你的立场：{side_map[ai_position]}\n用户立场：{side_map[position]}\n规则：1.每次发言阐述一个论点 2.用逻辑和事实说话 3.反驳对方观点 4.保持礼貌理性 5.每轮150字以内"

    conversation = [{"role": "system", "content": system_prompt}]
    conversation.append({"role": "user", "content": f"辩题是：{topic}。你作为{side_map[ai_position]}，请首先发表你的开场陈词。"})

    session = {
        "session_id": session_id,
        "username": username,
        "topic": topic,
        "user_position": position,
        "ai_position": ai_position,
        "conversation": conversation,
        "round": 0,
        "status": "active",
        "created_at": str(datetime.datetime.utcnow())
    }

    # 获取 AI 首轮发言
    first_message = get_ai_debate_response(session)
    session["conversation"].append({"role": "assistant", "content": first_message})
    session["round"] = 1
    debate_sessions[session_id] = session

    # 存 MongoDB
    if mongo_db:
        mongo_db.debates.insert_one(dict(session))
    return jsonify({"success": True, "session_id": session_id, "message": first_message})

@app.route("/api/debate/message", methods=["POST"])
def api_debate_message():
    data = request.get_json(force=True)
    sid = data.get("session_id", "")
    msg = data.get("message", "")
    if not sid or sid not in debate_sessions:
        return jsonify({"success": False, "message": "辩论会话不存在"})
    session = debate_sessions[sid]
    if session["status"] != "active":
        return jsonify({"success": False, "message": "辩论已结束"})
    session["conversation"].append({"role": "user", "content": msg})
    response = get_ai_debate_response(session)
    session["conversation"].append({"role": "assistant", "content": response})
    session["round"] += 1
    # 更新 MongoDB
    if mongo_db:
        mongo_db.debates.update_one({"session_id": sid}, {"$set": {"round": session["round"], "conversation": session["conversation"]}})
    return jsonify({"success": True, "message": response})

@app.route("/api/debate/end", methods=["POST"])
def api_debate_end():
    data = request.get_json(force=True)
    sid = data.get("session_id", "")
    if sid in debate_sessions:
        debate_sessions[sid]["status"] = "ended"
        if mongo_db:
            mongo_db.debates.update_one({"session_id": sid}, {"$set": {"status": "ended"}})
    return jsonify({"success": True})

def get_ai_debate_response(session):
    """获取 AI 辩论回应，优先使用 OpenAI"""
    if openai_client:
        try:
            messages = session["conversation"][:]  # 复制
            resp = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.8,
                max_tokens=300
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API 错误: {e}")
            pass

    # 规则引擎回退
    topic = session["topic"]
    ai_pos = session["ai_position"]
    if topic in RULE_RESPONSES:
        responses = RULE_RESPONSES[topic][ai_pos]
        idx = session["round"] % len(responses)
        return responses[idx]
    import random
    return random.choice(RULE_FALLBACK)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"* 辩境 -- AI 辩论系统 http://127.0.0.1:{port}")
    print(f"* OpenAI: {'已配置' if openai_client else '未配置（使用规则引擎）'}")
    print(f"* MongoDB: {'已连接' if mongo_db else '未连接（使用内存存储）'}")
    print("* 按 Ctrl+C 停止服务")
    app.run(debug=False, host="0.0.0.0", port=port)
