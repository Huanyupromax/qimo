from typing import List, Dict
from .models import AttackDefenseBehavior, BehaviorCategory

AD_MAP = {}

def _init():
    items = [
        AttackDefenseBehavior(behavior_id="interrupt", name="打断发言", category=BehaviorCategory.ATTACK, weight=0.8, trigger_keywords=["你错了"], related_dimensions=["aggression"], impact_scores={"aggression": 8}),
        AttackDefenseBehavior(behavior_id="rebuttal", name="逻辑反驳", category=BehaviorCategory.ATTACK, weight=0.9, trigger_keywords=["但是","然而"], related_dimensions=["aggression","logic"], impact_scores={"aggression":5,"logic":3}),
        AttackDefenseBehavior(behavior_id="evidence", name="证据引用", category=BehaviorCategory.ATTACK, weight=0.7, trigger_keywords=["研究表明","数据显示"], related_dimensions=["logic","presence"], impact_scores={"logic":10,"presence":3}),
        AttackDefenseBehavior(behavior_id="concede", name="承认对方", category=BehaviorCategory.DEFENSE, weight=0.5, trigger_keywords=["我承认"], related_dimensions=["adaptability"], impact_scores={"adaptability":6}),
    ]
    for b in items:
        AD_MAP[b.behavior_id] = b
_init()

class DABehaviorMap:
    def __init__(self):
        self.m = AD_MAP
    def detect(self, text):
        result = []
        for b in self.m.values():
            for kw in b.trigger_keywords:
                if kw in text:
                    result.append(b)
                    break
        return result