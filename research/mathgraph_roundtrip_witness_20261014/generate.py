#!/usr/bin/env python3
"""Generate fixed source-independent YAML string metamorphic cases, without target diff."""
import hashlib
import json
from pathlib import Path
import random
import sys

HERE=Path(__file__).resolve().parent
P=json.loads((HERE/"FROZEN_PROTOCOL.json").read_text())
rng=random.Random(P["seed"])
budget=P["case_budgets"]
cases=[]
def add_family(kind,count,make):
    used=set()
    for trial in range(count*150):
        if len(used)==count:break
        value=make()
        if not isinstance(value,str) or value in used:continue
        used.add(value)
        cases.append({"id":kind+"_{:03d}".format(len(used)-1),
                      "kind":kind,"value":value})
    assert len(used)==count, "CASE_GENERATION_QUOTA_UNMET_"+kind

numbers=[0,1,2,3,5,7,10,11,12,15,99,100,101,999,1000,1200,123456]
def numeric():
    sign=rng.choice(["","-","+"])
    num=str(rng.choice(numbers))
    typ=rng.choice(["int","leadingzero","hex","oct","bin","decimal","scientific","underscores"])
    if typ=="int":return sign+num
    if typ=="leadingzero":return sign+"0"+num
    if typ=="hex":return sign+"0x"+format(int(num),"x")
    if typ=="oct":return sign+"0o"+format(int(num),"o")
    if typ=="bin":return sign+"0b"+format(int(num),"b")
    if typ=="decimal":return sign+num+"."+str(rng.choice(numbers))
    if typ=="scientific":return sign+num+rng.choice(["e","E"])+rng.choice(["+","-",""])+str(rng.randrange(0,13))
    return sign+num+"_"+str(rng.choice(numbers))
add_family("number_like",budget["number_like"],numeric)

symbols=list("#:%&*@\\{}[],!|>?/^$'\"-+=()")
letters="abXYZ09._"
def punctuation():
    a=rng.choice(["a","prefix","v","x",""])
    b="".join(rng.choice(symbols+list(letters)) for _ in range(rng.randrange(1,12)))
    return a+b+rng.choice(["","y","tail","0"])
add_family("punctuation",budget["punctuation"],punctuation)

special=["","null","NULL","Null","~","true","false","TRUE","FALSE","True","False",
         "yes","no","YES","NO","on","off","ON","OFF","y","n","Y","N",
         ".nan",".NaN",".NAN",".inf","-.inf","+.Inf","NaN","Infinity",
         "2015-01-01","2026-10-14","2020-12-31T00:00:00Z",
         "0","-0","01","001","0x1e3","1e3","-1e3",
         "[]","{}","---","...","<null>","?","!","&a","*a"]
cursor=[0]
def keywords():
    i=cursor[0];cursor[0]+=1
    base=special[i%len(special)]
    if i<len(special):return base
    return base+rng.choice([" ","_","-",":","#","?","/"])+str(i)
add_family("keywords",budget["keywords"],keywords)

unicodePieces=["你好","漢字","é","café","🚀","😀","🇳🇿","π","∞","λ","数学",
              "عربي","हिन्दी","אמת","ñ","Ø","𝛼","e\u0301","ö","\u00a0","Ж"]
def unicode():
    return "".join(rng.choice(unicodePieces) for _ in range(rng.randrange(1,5)))+rng.choice(["","42","-x"," alpha"])
add_family("unicode",budget["unicode"],unicode)

spaces=[" ","  ","   ","\t","\n","\r\n","\n  "," \n","\t ","\n\n"," \t"]
words=["x","alpha","#token","a:b","1e3","true","null","🚀","hello"]
def whitespace():
    return rng.choice(spaces)+rng.choice(words)+rng.choice(spaces)
add_family("whitespace",budget["whitespace"],whitespace)

assert len(cases)==P["total_cases"]==1088
assert len({x["id"] for x in cases})==len(cases)
assert all(isinstance(x["value"],str) for x in cases)
serialized=(json.dumps(cases,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode("utf8")
path=Path(sys.argv[1]) if len(sys.argv)>1 else HERE/"metamorphic_cases.json"
path.write_bytes(serialized)
print("MATHGRAPH_ROUNDTRIP_GENERATOR "+json.dumps({
 "cases":len(cases),"kinds":budget,"sha256":hashlib.sha256(serialized).hexdigest(),
 "method":"human_authored_generic_metamorphic_invariant","pr_patch_exposure":False
},sort_keys=True),flush=True)
