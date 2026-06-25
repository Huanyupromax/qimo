"""辩论结构化输出模型"""
from pydantic import BaseModel
from typing import List, Optional

class DebateSpeech(BaseModel):
    """单轮辩论发言的结构化数据"""
    speech: str
    argument_type: str  # "opening" | "rebuttal" | "supplement" | "closing"
    main_claim: str = ""
    reasoning: List[str] = []
    evidence: List[str] = []
    rebuttal_target: Optional[str] = None
    logical_connectors: List[str] = []
    emotion_markers: List[str] = []

    def to_text_analysis(self) -> dict:
        """转换为文本分析模块需要的特征数据"""
        text = self.speech
        nlp_input = {
            "text": text,
            "argument_type": self.argument_type,
            "main_claim": self.main_claim,
            "reasoning_count": len(self.reasoning),
            "evidence_count": len(self.evidence),
            "has_rebuttal": self.rebuttal_target is not None and len(self.rebuttal_target) > 0,
            "rebuttal_target": self.rebuttal_target or "",
            "logical_words": self.logical_connectors,
            "emotion_markers": self.emotion_markers,
            "has_structured_data": True
        }
        return nlp_input

class StructuredResponse(BaseModel):
    """辩论 API 完整响应"""
    success: bool = True
    session_id: str = ""
    message: str = ""  # 纯文本（兼容旧版）
    speech: Optional[DebateSpeech] = None  # 结构化数据\n