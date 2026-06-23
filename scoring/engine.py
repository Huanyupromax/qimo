import time
from .dbti import get_dbti_info

class ScoringEngine:
    DIMS = ["aggression","logic","rhythm","adaptability","presence"]
    NMS = {"aggression":"进攻性","logic":"逻辑密度","rhythm":"节奏控制","adaptability":"弹性适应","presence":"气势压制"}
    def __init__(self):
        self.bufs = {k:[] for k in self.DIMS}
        self.stats = {"talk_time":0,"rebuttals":0,"evidences":0}
        self.rounds = 0
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
    def _add(self, d, v):
        c = max(0, min(100, v))
        self.bufs[d].append(c)
        if len(self.bufs[d]) > 50: self.bufs[d] = self.bufs[d][-50:]
    def get(self):
        return {d: round(sum(v)/max(len(v),1)) for d,v in self.bufs.items() if v}
    def dbti(self, th=50):
        s = self.get()
        return get_dbti_info(s.get("aggression",50), s.get("logic",50), s.get("rhythm",50), s.get("presence",50), th)
    def report(self, user="", topic="", rd=0):
        s = self.get(); total = sum(s.values())
        code,name,desc = self.dbti()
        dr = {d: {"name":self.NMS.get(d,d), "score":s.get(d,50), "samples":len(self.bufs.get(d,[]))} for d in self.DIMS}
        return {"user":user,"topic":topic,"rounds":rd or self.rounds,"timestamp":time.time(),"scores":dr,"total":total,"avg":round(total/5,1),"dbti_code":code,"dbti_name":name,"dbti_desc":desc,"stats":{"talk_time":self.stats["talk_time"],"rebuttals":self.stats["rebuttals"]}}
