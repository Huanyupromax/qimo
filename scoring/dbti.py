DBTI_TYPES = {}
_codes = []
for a in ["A","a"]:
    for l in ["L","l"]:
        for r in ["R","r"]:
            for p in ["P","p"]:
                _codes.append(f"{a}{l}{r}{p}")
_names = ["辩坛霸主","热血辩论家","逻辑炮手","冷静战略家",
          "情绪煽动者","狂野攻击者","随性辩手","热血无双",
          "沉稳策略家","学术辩手","冰山逻辑师","深思者",
          "温和说服者","倾听者","亲和沟通者","观察者"]
_descs = ["高攻高逻高节奏高气势","高攻高逻高节奏低气势","高攻高逻低节奏高气势","高攻高逻低节奏低气势",
          "高攻低逻高节奏高气势","高攻低逻低节奏高气势","高攻低逻高节奏低气势","高攻低逻低节奏低气势",
          "低攻高逻高节奏高气势","低攻高逻高节奏低气势","低攻高逻低节奏高气势","低攻高逻低节奏低气势",
          "低攻低逻高节奏高气势","低攻低逻高节奏低气势","低攻低逻低节奏高气势","低攻低逻低节奏低气势"]
for i, c in enumerate(_codes):
    DBTI_TYPES[c] = {"name": _names[i], "desc": _descs[i]}

def get_dbti_code(a, l, r, p, th=50):
    return ("A" if a>=th else "a") + ("L" if l>=th else "l") + ("R" if r>=th else "r") + ("P" if p>=th else "p")

def get_dbti_info(a, l, r, p, th=50):
    code = get_dbti_code(a,l,r,p,th)
    info = DBTI_TYPES.get(code)
    return (code, info["name"], info["desc"]) if info else (code, "自由辩手", "独特的辩论风格")
