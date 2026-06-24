import time
from .dbti import get_dbti_info

class ScoringEngine:
    DIMS = ["aggression","logic","rhythm","adaptability","presence"]
    NMS = {"aggression":"进攻性","logic":"逻辑密度","rhythm":"节奏控制","adaptability":"弹性适应","presence":"气势压制"}
    def __init__(self):
        self.bufs = {k:[] for k in self.DIMS}
        self.stats = {"talk_time":0,"rebuttals":0,"evidences":0}
        self.rounds = 0
        self.kb_mode = False
        self.kb_corrector = None
        self.kb_log = []
    def set_kb_corrector(self, corrector):
        self.kb_corrector = corrector
    def set_kb_mode(self, enabled: bool):
        self.kb_mode = enabled
    def from_nlp(self, nd):
        if not nd: return
        self._add("aggression", nd.get("rebuttal_ratio",0)*100)
        self._add("logic", min(100, (nd.get("logical_density",0)+nd.get("evidence_density",0)*2)*10))
        self._add("adaptability", 100-abs(nd.get("emotion_score",0))*50)
        self.stats["rebuttals"] += len(nd.get("rebuttal_sentences",[]))
        self.rounds += 1
    def from_voice(self, v):
        if not v: return
        self._add("aggression", v.get("volume_peak",0)*100)
        self._add("rhythm", min(100, v.get("speech_rate",0)*20))
        self._add("presence", v.get("volume_avg",0)*100)
        self.stats["talk_time"] += v.get("duration",0)
    def from_face(self, f):
        if not f: return
        de = f.get("dominant_emotion","neutral")
        if de in ("angry","surprise"): self._add("aggression",70)
        elif de in ("happy","neutral"): self._add("aggression",50)
        else: self._add("aggression",30)
    def apply_kb_correction(self, text=None, voice=None, face=None):
        """应用知识库纠偏"""
        if not self.kb_mode or not self.kb_corrector:
            return
        correction = self.kb_corrector.multimodal_correct(text, voice, face)
        dpm_adj = correction.get("dpm_adjustments", {})
        for dim, adj in dpm_adj.items():
            if dim in self.bufs and self.bufs[dim]:
                current = sum(self.bufs[dim][-3:]) / max(len(self.bufs[dim][-3:]), 1)
                self._add(dim, current + adj)
        if correction.get("logs"):
            self.kb_log.extend(correction["logs"])
        return correction
    def _add(self, d, v):
        c = max(0, min(100, v))
        self.bufs[d].append(c)
        if len(self.bufs[d]) > 50: self.bufs[d] = self.bufs[d][-50:]
    def get(self):
        return {d: round(sum(v)/max(len(v),1)) for d,v in self.bufs.items() if v}
    def get_kb_enhanced(self):
        """带KB修正的分数"""
        base = self.get()
        if not self.kb_mode or not self.kb_log:
            return base, {}, "disabled"
        adjustments = {}
        for log_entry in self.kb_log:
            for k, v in log_entry.get("corrections", {}).items():
                if k.startswith("dpm_"):
                    dim = k.replace("dpm_", "")
                    adjustments[dim] = adjustments.get(dim, 0) + v
        enhanced = {}
        for dim in self.DIMS:
            base_val = base.get(dim, 50)
            adj = adjustments.get(dim, 0)
            enhanced[dim] = max(0, min(100, base_val + adj))
        return enhanced, adjustments, "kb_enabled"
    def dbti(self, th=50):
        s = self.get()
        return get_dbti_info(s.get("aggression",50), s.get("logic",50), s.get("rhythm",50), s.get("presence",50), th)
    def dbti_enhanced(self, th=50):
        """带KB修正的DBTI"""
        enhanced, adj, mode = self.get_kb_enhanced()
        return get_dbti_info(enhanced.get("aggression",50), enhanced.get("logic",50),
                            enhanced.get("rhythm",50), enhanced.get("presence",50), th), adj, mode
    def report(self, user="", topic="", rd=0):
        s = self.get()
        total = sum(s.values())
        code,name,desc = self.dbti()
        dr = {d: {"name":self.NMS.get(d,d), "score":s.get(d,50), "samples":len(self.bufs.get(d,[]))} for d in self.DIMS}
        base = {"user":user,"topic":topic,"rounds":rd or self.rounds,"timestamp":time.time(),
                "scores":dr,"total":total,"avg":round(total/5,1),
                "dbti_code":code,"dbti_name":name,"dbti_desc":desc,
                "stats":{"talk_time":self.stats["talk_time"],"rebuttals":self.stats["rebuttals"]},
                "kb_mode":self.kb_mode}
        if self.kb_mode:
            enhanced, adj, mode = self.get_kb_enhanced()
            enh_scores = {d: {"name":self.NMS.get(d,d), "score":enhanced.get(d,50), "adjustment":adj.get(d,0)} for d in self.DIMS}
            enh_code, enh_name, enh_desc = self.dbti_enhanced()
            base["kb"] = {"enabled":True,"scores":enh_scores,"adjustments":adj,
                         "dbti_code":enh_code,"dbti_name":enh_name,"dbti_desc":enh_desc,
                         "logs":self.kb_log[-20:]}
        return base
