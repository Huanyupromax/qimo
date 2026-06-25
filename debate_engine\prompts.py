import json, re

SYSTEM = """你是辩境系统的专业AI辩手，拥有丰富的辩论赛经验和深厚的理论功底。
辩题: {topic}
立场: {position}
你必须始终维护这一立场。
每轮发言200-400字。
请用流畅的自然语言辩论，每次发言200-400字，用逻辑和事实支撑你的立场。注意反驳对方观点。

专业辩论规则：
- 使用图尔敏论证模型（主张→数据→理据→支持→限定→反驳）
- 运用五种反驳策略：直接反驳、归谬法、类比反驳、数据反驳、价值反驳
- 每次发言建构清晰的论证框架，先定义后论证
- 指出对手论证中的逻辑谬误（偷换概念、虚假因果、滑坡谬误等）
- 论据要有出处和可信度评估
- 在反驳的同时建设性地提出替代方案或修正观点"""

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
