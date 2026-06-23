DBTI_TYPES={}
def get_dbti_code(a,l,r,p,th=50):
 return ("A" if a>=th else "a")+("L" if l>=th else "l")+("R" if r>=th else "r")+("P" if p>=th else "p")
def get_dbti_info(a,l,r,p,th=50):
 code=get_dbti_code(a,l,r,p,th)
 return (code,"自由辩手","独特的辩论风格")
