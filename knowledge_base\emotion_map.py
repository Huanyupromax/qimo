from typing import Dict
from .models import EmotionFeatureLayer1, EmotionFeatureLayer2

EMOTION_TO_FEATURE: Dict[str, EmotionFeatureLayer1] = {}
LAYER2: Dict[str, EmotionFeatureLayer2] = {}

def _init():
    e1 = [
        EmotionFeatureLayer1(emotion="angry", debate_features={"aggression":0.85,"intensity":0.9}),
        EmotionFeatureLayer1(emotion="happy", debate_features={"aggression":0.3,"intensity":0.6}),
        EmotionFeatureLayer1(emotion="neutral", debate_features={"aggression":0.5,"intensity":0.5}),
        EmotionFeatureLayer1(emotion="sad", debate_features={"aggression":0.2,"intensity":0.3}),
    ]
    for item in e1: EMOTION_TO_FEATURE[item.emotion] = item
    e2 = [
        EmotionFeatureLayer2(debate_feature="aggression", dimension_adjustments={"aggression":5,"presence":2}),
        EmotionFeatureLayer2(debate_feature="intensity", dimension_adjustments={"presence":4}),
    ]
    for item in e2: LAYER2[item.debate_feature] = item
_init()

class EmotionFeatureMapper:
    def __init__(self):
        self.l1 = EMOTION_TO_FEATURE
        self.l2 = LAYER2
    def full_map(self, label):
        entry = self.l1.get(label) or self.l1.get("neutral")
        feats = entry.debate_features
        result = {}
        for feat, strength in feats.items():
            entry2 = self.l2.get(feat)
            if entry2:
                for dim, val in entry2.dimension_adjustments.items():
                    result[dim] = result.get(dim, 0) + val * strength
        return result