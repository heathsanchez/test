#!/usr/bin/env python3
"""Hold-out input generator. Separate source and seed from the native-qualified 1088 examples."""
from pathlib import Path
import hashlib
import json
import random
import sys
HERE=Path(__file__).resolve().parent
P=json.loads((HERE/"HELDOUT_5000_PROTOCOL.json").read_text())
rng=random.Random(P["independent_input_seed"])
cases=[]
used=set()
def register(kind,value):
  if not isinstance(value,str) or value in used:return False
  used.add(value)
  cases.append({"id":kind+"_{:04d}".format(sum(x["id"].startswith(kind+"_") for x in cases)),
                "kind":kind,"value":value})
  return True
def populate(kind,make):
  needed=P["case_families"][kind]
  attempts=0
  while sum(x["kind"]==kind for x in cases)<needed:
    attempts+=1
    assert attempts<needed*150,"CASE_GENERATION_DIVERSITY_FAILURE_"+kind
    register(kind,make())

digits=[0,1,2,3,5,9,10,12,15,99,111,1000,1234567]
def numbers():
  n=str(rng.choice(digits))
  sign=rng.choice(["","-","+"])
  fmt=rng.choice(["plain","scientific","frac","leading_zero","hex","oct","bin","underscore"])
  if fmt=="plain":return sign+n
  if fmt=="scientific":return sign+n+rng.choice(["e","E"])+rng.choice(["","-","+"])+str(rng.randrange(0,20))
  if fmt=="frac":return sign+n+"."+str(rng.randrange(0,10000))
  if fmt=="leading_zero":return sign+"0"+n
  if fmt=="hex":return sign+"0x"+format(int(n),"x")
  if fmt=="oct":return sign+"0o"+format(int(n),"o")
  if fmt=="bin":return sign+"0b"+format(int(n),"b")
  return sign+n+"_"+str(rng.randrange(0,10000))
populate("number_like",numbers)

controls=["\t","\n","\r","\r\n","\n\n","\t\t","\n  ","\t ","\r  ","\r\n  "]
pieces=["alpha","beta","true","false","1e3","null","name:value","🚀","ä","."]
def leading():
  return rng.choice(controls)+"".join(rng.choice(pieces) for _ in range(rng.randrange(1,5)))+rng.choice(["","\n","\r\n","\t","  ","\n\n"])
populate("control_leading",leading)

prefixes=["v","x","hello","alpha","test","prefix","world","123abc"]
def internal():
  return rng.choice(prefixes)+rng.choice([" ",""]) +rng.choice(controls)+ "".join(rng.choice(pieces) for _ in range(rng.randrange(1,4)))+rng.choice([""," tail"," ","\n","\t"])
populate("control_internal",internal)

unicode=["你好","数学","π","∞","🚀","😀","🇳🇿","λ","e\u0301","\u00e9","\u2028","\u2029","Ж","عربي","हिन्दी","ש","€","°"]
specialChars=list("!@#$%^&*()-+={}[];:'\"\\|<>?,./")
def special_unicode():
  x="".join(rng.choice(unicode+specialChars+list("Aab01_")) for _ in range(rng.randrange(1,20)))
  return rng.choice(["","a","v",":"]) + x + rng.choice(["","z","2"," ","\t"])
populate("punctuation_unicode",special_unicode)

special=[".nan",".NaN",".NAN",".inf",".Inf",".INF","-.inf","-.Inf","-.INF",
         "+.inf","null","Null","NULL","true","TRUE","false","FALSE","~",
         "[]","{}","---","...","0x1e3","1e3","1E3","not-a-date",
         ".nanny",".infinite","0","01","0b100","0o12"]
cursor=[0]
def near_miss():
  i=cursor[0];cursor[0]+=1
  if i<len(special):return special[i]
  stem=rng.choice(special)
  return rng.choice([""," ",".","#","-","_","/",":","?"])+stem+rng.choice(["0","A"," ","_",":","!",str(i),"\t"])
populate("special_near_miss",near_miss)
assert len(cases)==P["generated_case_total"]==5000
from collections import Counter
assert dict(Counter(x["kind"] for x in cases))==P["case_families"]
serialized=(json.dumps(cases,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode("utf-8")
out=Path(sys.argv[1]) if len(sys.argv)>1 else HERE/"heldout_cases.json"
out.write_bytes(serialized)
print("MATHGRAPH_HELDOUT_GENERATED "+json.dumps({
 "total":len(cases),"families":P["case_families"],
 "seed":P["independent_input_seed"],
 "sha256":hashlib.sha256(serialized).hexdigest()
},sort_keys=True),flush=True)
