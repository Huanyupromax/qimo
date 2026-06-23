import json
S="You are a debate AI. Topic: {topic}. Position: {pos}."
def build_system_prompt(t,p):
 pn={"pro":"Pro","con":"Con"};return S.format(topic=t,pos=pn.get(p,p))
def parse_llm_response(t):
 try:d=json.loads(t.strip());return d if"speech"in d else{"speech":t}
 except:return{"speech":t,"argument_type":"rebuttal","_parsed":False}
def build_round_prompt(*a,**k):return""
