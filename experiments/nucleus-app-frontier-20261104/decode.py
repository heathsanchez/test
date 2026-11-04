"""Read-only decoder for the official-export expression DAG at the first UNKNOWN."""

import json
from pathlib import Path
import sys


source = Path(sys.argv[1])
names = {0: "_"}
exprs = {}
decls = []
for raw in source.read_text().splitlines():
    obj = json.loads(raw)
    if "in" in obj:
        idx = obj["in"]
        payload = obj.get("str") or obj.get("num")
        if "str" in obj:
            prefix = names.get(payload["pre"], f"Name{payload['pre']}")
            names[idx] = ((prefix + ".") if prefix != "_" else "") + payload["str"]
        else:
            prefix = names.get(payload["pre"], f"Name{payload['pre']}")
            names[idx] = ((prefix + ".") if prefix != "_" else "") + str(payload["i"])
    if "ie" in obj:
        exprs[obj["ie"]] = obj
    for kind in ("thm", "def", "opaque", "axiom"):
        if kind in obj:
            decls.append((kind, obj[kind]))


def unfold(idx, max_depth=16):
    """Follow only application spines to their source head; keep actual args."""
    args = []
    seen = set()
    cur = idx
    while cur in exprs and cur not in seen and len(args) < max_depth:
        seen.add(cur)
        obj = exprs[cur]
        if "app" not in obj:
            break
        args.append(obj["app"]["arg"])
        cur = obj["app"]["fn"]
    obj = exprs.get(cur, {})
    if "const" in obj:
        head = names.get(obj["const"]["name"], str(obj["const"]["name"]))
    else:
        head = str(obj)
    return f"Expr{idx}: head={head}({cur}), args={list(reversed(args))}"


def children(idx, depth=0, maximum=2):
    if depth > maximum:
        return
    print("  " * depth + unfold(idx))
    obj = exprs.get(idx, {})
    if "app" in obj:
        children(obj["app"]["arg"], depth + 1, maximum)


for query in map(int, sys.argv[2:]):
    print("TARGET", query)
    children(query, maximum=1)

print("BLOCKED NEUTRAL HEAD IDENTITIES", [(key, names.get(key)) for key in (431, 2005)])

print("REFERENCED DECLARATIONS")
roots = (87624, 18627, 55137, 86154)
for kind, decl in decls:
    if decl.get("name") not in [exprs[expr]["const"]["name"] for expr in roots if "const" in exprs.get(expr, {})]:
        continue
    print(kind, names.get(decl["name"]), "type", decl.get("type"), "value", decl.get("value"))
    children(decl["type"], maximum=0)
    current = decl["type"]
    for binder_index in range(10):
        expression = exprs.get(current, {})
        binder = expression.get("forallE")
        if binder is None:
            print("  final", unfold(current))
            break
        print("  binder", binder_index, names.get(binder["name"]),
              binder["binderInfo"], "domain", unfold(binder["type"]))
        current = binder["body"]
