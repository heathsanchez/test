#!/usr/bin/env python3
"""Restricted literal receipt replay, never eval or exec upstream source assertions."""
import json,sys
from h11._headers import normalize_and_validate
data=json.load(open(sys.argv[1],encoding="utf-8"))
def decode(item):
    return bytes.fromhex(item["hex"]) if item["encoding"]=="bytes" else item["hex"]
matches=0
fail=[]
for row in data:
    actual_input=[tuple(decode(item) for item in pair) for pair in row["input"]]
    expect=[tuple(decode(item) for item in pair) for pair in row["expected"]]
    try:
        got=list(normalize_and_validate(actual_input))
        ok=got==expect
    except Exception as exc:
        ok=False
        got=type(exc).__name__
    matches+=int(ok)
    if not ok:fail.append({"line":row["line"],"actual":repr(got)[:300]})
print(json.dumps({"total":len(data),"matches":matches,"failures":fail[:10]},sort_keys=True))
