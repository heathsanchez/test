#!/usr/bin/env python3
"""Pinned Nat.succ_le_succ reproducibility and false-index negative."""
import copy, hashlib, json, pathlib, sys

def extract(raw):
    names = {0: ""}
    rows = []
    for line in raw.splitlines(keepends=True):
        j = json.loads(line)
        rows.append(line)
        if "in" in j:
            n = j.get("str", j.get("num"))
            parent = names.get(n["pre"], "")
            names[j["in"]] = parent + ("." if parent else "") + str(n.get("str", n.get("i")))
        if "thm" in j and names.get(j["thm"]["name"]) == "Nat.succ_le_succ":
            return b"".join(rows)
    raise ValueError("theorem not in export")

def false_index(prefix):
    rows = prefix.splitlines(keepends=True)
    theorem = json.loads(rows[-1])
    assert theorem["thm"]["type"] == 4174
    assert theorem["thm"]["value"] == 4241
    e = {}
    for row in rows:
        j = json.loads(row)
        if "ie" in j:
            e[j["ie"]] = {k:v for k,v in j.items() if k != "ie"}
    assert e[8] == {"bvar":2}
    new = [(4242, {"app":{"fn":4170,"arg":8}})]
    for n,old,body in [(4243,4172,4242),(4244,4173,4243),(4245,4174,4244)]:
        node = copy.deepcopy(e[old])
        node["forallE"]["body"] = body
        new.append((n,node))
    theorem["thm"]["type"] = 4245
    additions = [(json.dumps({"ie":n}|node,separators=(",",":"))+"\n").encode() for n,node in new]
    additions.append((json.dumps(theorem,separators=(",",":"))+"\n").encode())
    return b"".join(rows[:-1]+additions)

if __name__ == "__main__":
    inp = pathlib.Path(sys.argv[1])
    out = pathlib.Path(sys.argv[2])
    kind = sys.argv[3]
    prefix = extract(inp.read_bytes())
    if kind == "negative":
        result = false_index(prefix)
        assert hashlib.sha256(result).hexdigest() == "2a090edfcfa2a16191f17a433617aaf045fc9b11cd0e2a93405b705d8a899688"
    else:
        result = prefix
        assert hashlib.sha256(result).hexdigest() == "5a4964190480cea9be1e17bc5f611394fcea1c523fb52fdf205ff0d8c220400b"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_bytes(result)
    print(json.dumps({"kind":kind,"sha256":hashlib.sha256(result).hexdigest(),"bytes":len(result)}))
