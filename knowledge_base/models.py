from pydantic import BaseModel
from typing import List,Dict,Optional
from enum import Enum

class BehaviorCategory(str,Enum):
    ATTACK="attack"
    DEFENSE="defense"
    NEUTRAL="neutral"

class BehaviorType(str,Enum):
    TECHNICAL="technical"
    TACTICAL="tactical"
    PSYCHOLOGICAL="psychological"

class AttackDefenseBehavior(BaseModel):
    behavior_id:str
    name:str
    category:BehaviorCategory
    weight:float=1.0
    trigger_keywords:List[str]=[]
    related_dimensions:List[str]=[]
    impact_scores:Dict[str,float]={}
    description:str=""

class EmotionFeatureLayer1(BaseModel):
    emotion:str
    debate_features:Dict[str,float]={}

class EmotionFeatureLayer2(BaseModel):
    debate_feature:str
    dimension_adjustments:Dict[str,float]={}

class CompetitiveBehavior(BaseModel):
    behavior_id:str
    name:str
    behavior_type:BehaviorType
    category:BehaviorCategory
    description:str=""
    detection_text:List[str]=[]
    detection_voice:List[str]=[]
    detection_face:List[str]=[]
    score_impact:Dict[str,float]={}

class KBConfig(BaseModel):
    enabled:bool=True
    debug_mode:bool=False
