#!/usr/bin/env python3
"""Deterministic source-independent YAML core scalar grammar generator, issue-informed only."""
import hashlib
import json
from pathlib import Path
import random
import sys
HERE=Path(__file__).resolve().parent
P=json.loads((HERE/"FROZEN_PROTOCOL.json").read_text())
rng=random.Random(P["seed"])
assert P["source_pr"]==939
assert P["contributor_patch_seen"] is False
assert P["generated_numeric_limit"]==256
assert P["generated_malformed_limit"]==36
assert P["generated_quoted_limit"]==96
mantissas=[1,2,3,5,7,9,10,11,12,13,21,23,42,99,101,123,456,987,1000,12345,999999]
exponents=[-12,-9,-7,-4,-3,-2,-1,0,1,2,3,4,6,9,12]
numeric=[]
seen=set()
for attempt in range(10000):
    if len(numeric)==256:break
    mantissa=rng.choice(mantissas)
    exponent=rng.choice(exponents)
    sign=rng.choice(["","-","+"])
    expchar=rng.choice(["e","E"])
    expstr=("+"+str(exponent) if exponent>=0 and rng.choice([True,False])
            else str(exponent))
    token=sign+str(mantissa)+expchar+expstr
    if token not in seen:
        numeric.append(token)
        seen.add(token)
assert len(numeric)==256
cases=[{"name":"numeric_{:03d}".format(i),"kind":"numeric","scalar":v}
    for i,v in enumerate(numeric)]
malformed=[str(m)+suffix
   for m in (1,2,3)
   for suffix in ("e","E","e+","e-","e++3","e--3","e+-3","e3.5","ee3","e3e4","e+z","E+bad")]
assert len(malformed)==36
cases.extend({"name":"malformed_{:03d}".format(i),"kind":"malformed","scalar":v}
 for i,v in enumerate(malformed))
cases.extend({"name":"quoted_{:03d}".format(i),"kind":"quoted","scalar":v}
 for i,v in enumerate(numeric[:96]))
cases.extend({"name":"control_{:03d}".format(i),"kind":"control","scalar":v}
 for i,v in enumerate(["alpha","beta-gamma","word_123","code@example"]))
assert len(cases)==392
assert len({x["name"] for x in cases})==len(cases)
assert all(":" not in x["scalar"] and "#" not in x["scalar"] for x in cases)
serialized=(json.dumps(cases,indent=2,sort_keys=True)+"\n").encode()
destination=Path(sys.argv[1]) if len(sys.argv)>1 else HERE/"generated_scalar_cases.json"
destination.write_bytes(serialized)
print("MATHGRAPH_GENERATED_CORPUS "+json.dumps({
    "cases":len(cases),"numeric":len(numeric),"quoted":96,"malformed":36,
    "controls":4,"sha256":hashlib.sha256(serialized).hexdigest(),
    "method":"human_written_fixed_scalar_grammar_generator",
    "patch_seen":False
},sort_keys=True))
