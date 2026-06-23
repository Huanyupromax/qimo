class KnowledgeBaseCorrector:
 def __init__(s):s.log=[]
 def correct(s,t=None,v=None,f=None):
  r={}
  if t:r["text"]=dict(t)
  if v:r["voice"]=dict(v)
  if f:r["face"]=dict(f)
  s.log.append({"type":"correction"});return r
