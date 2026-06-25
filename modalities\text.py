"""文本模态粗判模块 — 规则 NLP 分析"""

import re
from typing import List, Tuple
from .models import TextFeatures


# ====== 情感词典（辩论场景常用词） ======
POSITIVE_WORDS = {
    "正确", "合理", "有效", "必要", "关键", "重要", "优势", "进步", "发展",
    "创新", "突破", "提高", "增强", "促进", "推动", "保障", "维护", "支持",
    "赞同", "同意", "认可", "肯定", "相信", "希望", "成功", "成就", "贡献",
    "积极", "正面", "有益", "有利", "利好", "繁荣", "昌盛", "稳定", "和谐",
    "公平", "正义", "自由", "民主", "科学", "理性", "明智", "明智", "远见",
}

NEGATIVE_WORDS = {
    "错误", "失败", "问题", "风险", "危机", "威胁", "危害", "损害", "破坏",
    "否定", "反对", "拒绝", "批评", "质疑", "担忧", "担心", "恐惧", "焦虑",
    "不足", "缺陷", "漏洞", "弊端", "劣势", "落后", "倒退", "下降", "恶化",
    "加剧", "严重", "危险", "负面", "消极", "有害", "无益", "无效", "无用",
    "虚假", "欺骗", "剥削", "压迫", "歧视", "不公", "失衡", "混乱", "冲突",
}

INTENSIFIERS = {
    "非常", "极其", "十分", "特别", "相当", "很", "太", "更", "最",
    "极为", "格外", "异常", "无比", "绝对", "完全", "彻底", "严重",
}

# ====== 反驳标记词 ======
REBUTTAL_PATTERNS = [
    r"但(是)?", r"然而", r"不过", r"可(是)?", r"却", r"虽然",
    r"尽管", r"即使", r"即便", r"固然",
    r"反驳", r"不同意", r"不赞同", r"恰恰相反", r"相反",
    r"对方(辩友)?[的]?(观点|说法|看法|论述)",
    r"我不(同意|赞同|认为|觉得)",
    r"这(一观点|说法|看法)?(站不住脚|有问题|不正确|不成立)",
    r"值得商榷", r"有待考量", r"难以认同",
]

# ====== 逻辑连接词 ======
LOGICAL_WORDS = {
    # 因果
    "因为": "因果", "所以": "因果", "因此": "因果", "因而": "因果",
    "从而": "因果", "以致": "因果", "由于": "因果",
    # 转折
    "但是": "转折", "然而": "转折", "不过": "转折", "可是": "转折",
    "却": "转折", "但": "转折",
    # 条件
    "如果": "条件", "假如": "条件", "倘若": "条件", "若": "条件",
    "只要": "条件", "只有": "条件", "除非": "条件",
    # 让步
    "虽然": "让步", "尽管": "让步", "即使": "让步", "即便": "让步",
    # 递进
    "不仅": "递进", "不但": "递进", "而且": "递进", "并且": "递进",
    "甚至": "递进", "况且": "递进",
    # 归纳
    "总之": "归纳", "综上所述": "归纳", "因此": "归纳",
    "首先": "序列", "其次": "序列", "最后": "序列",
    "第一": "序列", "第二": "序列", "第三": "序列",
}

# ====== 证据引用词 ======
EVIDENCE_WORDS = [
    "研究表明", "研究显示", "研究指出", "研究发现",
    "数据显示", "统计显示", "统计表明", "数字表明",
    "调查显示", "调查表明",
    "根据", "据", "报告", "报道",
    "专家指出", "学者认为", "专家表示", "学者指出",
    "数据表明", "事实表明", "实践证明",
    "例如", "比如", "举例", "譬如", "以.*?为例",
    "参考", "引自", "来源",
]


class TextAnalyzer:
    """文本模态分析器 — 辩论文本特征提取"""

    def __init__(self):
        self._rebuttal_re = [re.compile(p) for p in REBUTTAL_PATTERNS]
        self._evidence_re = re.compile("|".join(EVIDENCE_WORDS))

    def analyze(self, text: str) -> TextFeatures:
        """对一段辩论文本进行完整特征分析"""
        if not text or not text.strip():
            return TextFeatures()

        features = TextFeatures()
        features.word_count = len(text)
        sentences = self._split_sentences(text)
        features.sentence_count = len(sentences)

        # 1. 基础情绪分析
        emotion_score = self._analyze_sentiment(text)
        features.emotion_score = round(emotion_score, 4)
        features.basic_emotion = (
            "积极" if emotion_score > 0.15 else
            "消极" if emotion_score < -0.15 else
            "中性"
        )

        # 2. 反驳句标记
        rebuttals = []
        for s in sentences:
            if self._is_rebuttal(s):
                rebuttals.append(s.strip())
        features.rebuttal_sentences = rebuttals
        features.rebuttal_ratio = round(len(rebuttals) / max(len(sentences), 1), 4)

        # 3. 逻辑词统计
        logical_words, logical_total = self._count_words(text, LOGICAL_WORDS)
        features.logical_word_count = logical_total
        features.logical_density = round(logical_total / max(features.word_count, 1) * 100, 4)

        # 4. 证据词统计
        evidence_total = len(self._evidence_re.findall(text))
        features.evidence_word_count = evidence_total
        features.evidence_density = round(evidence_total / max(features.word_count, 1) * 100, 4)

        return features

    def _split_sentences(self, text: str) -> List[str]:
        """按标点分句"""
        return [s.strip() for s in re.split(r"[。！？!?\n]", text) if s.strip()]

    def _analyze_sentiment(self, text: str) -> float:
        """计算情感得分 (-1 ~ 1)"""
        words = re.findall(r"[\u4e00-\u9fff]{2,4}", text)
        score = 0.0
        count = 0
        for i, w in enumerate(words):
            if w in POSITIVE_WORDS:
                intensifier = 1.0
                if i > 0 and words[i - 1] in INTENSIFIERS:
                    intensifier = 1.5
                score += 0.25 * intensifier
                count += 1
            elif w in NEGATIVE_WORDS:
                intensifier = 1.0
                if i > 0 and words[i - 1] in INTENSIFIERS:
                    intensifier = 1.5
                score -= 0.25 * intensifier
                count += 1
        if count == 0:
            return 0.0
        return max(-1.0, min(1.0, score / max(count, 1) * 2))

    def _is_rebuttal(self, sentence: str) -> bool:
        """判断是否为反驳句"""
        for pattern in self._rebuttal_re:
            if pattern.search(sentence):
                return True
        return False

    def _count_words(self, text: str, word_dict: dict) -> Tuple[dict, int]:
        """统计词表中各词出现次数"""
        result = {}
        total = 0
        for word, category in word_dict.items():
            count = text.count(word)
            if count > 0:
                result[word] = {"count": count, "category": category}
                total += count
        return result, total
