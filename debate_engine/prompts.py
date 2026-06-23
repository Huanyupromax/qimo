import json, re

SYSTEM = """你是辩境系统的专业AI辩手。
辩题: {topic}
立场: {position}
你必须始终维护这一立场。
每轮发言200-400字。
请用流畅的自然语言辩论，每次发言200-400字，用逻辑和事实支撑你的立场。注意反驳对方观点。"""

def build_system_prompt(topic, position):
    pm = {"pro":"正方（支持）","con":"反方（反对）"}
    return SYSTEM.format(topic=topic, position=pm.get(position,position))

def build_round_prompt(rt, topic="", position="", opponent=""):
    pm = {"pro":"正方","con":"反方"}
    pos = pm.get(position,position)
    prompts = {"opening": f"开场陈词。辩题:{topic}。立场:{pos}",
               "rebuttal": f"反驳对方。对方发言:{opponent}"}
    return prompts.get(rt, prompts["rebuttal"])

def parse_llm_response(text):
    t = text.strip()
    try:
        d = json.loads(t)
        if "speech" in d: return d
    except: pass
    return {"speech": t, "argument_type": "rebuttal", "main_claim": "", "reasoning": [], "evidence": [], "_parsed": False}
