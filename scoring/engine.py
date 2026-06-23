from .dbti import get_dbti_info
class ScoringEngine:
 DIMS=["aggression","logic","rhythm","adaptability","presence"]
 NMS={"aggression":"进攻性","logic":"逻辑密度","rhythm":"节奏控制","adaptability":"弹性适应","presence":"气势压制"}
 def __init__(s):s.bufs={d:[] for d in s.DIMS}
 def from_nlp(s,n):
  if not n:return
  s._add("aggression",n.get("rebuttal_ratio",0)*100)
  s._add("logic",min(100,(n.get("logical_density",0)+n.get("evidence_density",0)*2)*10))
 def _add(s,d,v):s.bufs[d].append(max(0,min(100,v)))
 def get(s):return {d:round(sum(v)/max(len(v),1)) for d,v in s.bufs.items() if v}
 def dbti(s,th=50):
  sc=s.get()
  return get_dbti_info(sc.get("aggression",50),sc.get("logic",50),sc.get("rhythm",50),sc.get("presence",50),th)
 def report(s,u="",t="",rd=0):
  sc=s.get();total=sum(sc.values())
  code,nm,desc=s.dbti()
  return {"user":u,"topic":t,"rounds":rd,"scores":sc,"total":total,"avg":round(total/5,1),"dbti_code":code,"dbti_name":nm,"dbti_desc":desc}
