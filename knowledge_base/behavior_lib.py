from typing import Dict,List,Optional
from .models import CompetitiveBehavior,BehaviorType,BehaviorCategory

BEHAVIOR_LIBRARY: Dict[str,CompetitiveBehavior] = {}

def _init():
    blist = [
        CompetitiveBehavior(behavior_id="quick_rebuttal",name="快速反驳",behavior_type=BehaviorType.TECHNICAL,category=BehaviorCategory.ATTACK,
            description="快速组织反驳",detection_text=["但是","然而","问题是"],score_impact={"aggression":6,"adaptability":5}),
        CompetitiveBehavior(behavior_id="data_citation",name="数据引用",behavior_type=BehaviorType.TECHNICAL,category=BehaviorCategory.ATTACK,
            description="引用数据支撑",detection_text=["数据显示","据统计"],score_impact={"logic":10,"presence":4}),
        CompetitiveBehavior(behavior_id="logic_chain",name="逻辑链推",behavior_type=BehaviorType.TECHNICAL,category=BehaviorCategory.ATTACK,
            description="多层逻辑推理",detection_text=["因此","由此可见","进一步说"],score_impact={"logic":8,"rhythm":3}),
        CompetitiveBehavior(behavior_id="calm_response",name="沉着回应",behavior_type=BehaviorType.PSYCHOLOGICAL,category=BehaviorCategory.DEFENSE,
            description="面对攻击保持冷静",detection_face=["neutral"],score_impact={"adaptability":7,"rhythm":5}),
        CompetitiveBehavior(behavior_id="topic_switch",name="话题转换",behavior_type=BehaviorType.TACTICAL,category=BehaviorCategory.DEFENSE,
            description="引导辩论方向",detection_text=["我们不如来看","更重要的是"],score_impact={"adaptability":8,"rhythm":4}),
    ]
    for b in blist: BEHAVIOR_LIBRARY[b.behavior_id] = b
_init()

class BehaviorLibrary:
    def __init__(self):
        self.lib = BEHAVIOR_LIBRARY
    def get_by_id(self, bid): return self.lib.get(bid)
    def detect_text(self, text):
        results = []
        for b in self.lib.values():
            for kw in b.detection_text:
                if kw in text: results.append(b); break
        return results