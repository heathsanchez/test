#!/usr/bin/env python3
"""Independent equal-information single-guard-ablation source-search baseline V1.

Can read exactly the same source and native failures as the acquired operator.
Its predefined operation is delete ONE conjunct guarding a relative f-string
return. It never imports or calls the acquired context-absence operation.
Not a strong coding-agent or exhaustive search baseline.
"""
import ast
import hashlib

MAX_CANDIDATES = 12

def generate(source: bytes):
    text = source.decode("utf8")
    lines = text.splitlines(keepends=True)
    prefixes = [0]
    for x in lines:
        prefixes.append(prefixes[-1] + len(x))
    tree = ast.parse(text)
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or not isinstance(node.test, ast.BoolOp) or not isinstance(node.test.op, ast.And):
            continue
        relative = any(
            isinstance(r, ast.Return) and isinstance(r.value, ast.JoinedStr)
            and "/" in "".join(v.value for v in r.value.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
            for r in node.body)
        if not relative or len(node.test.values) < 2:
            continue
        for j in range(len(node.test.values)):
            rem = [v for k,v in enumerate(node.test.values) if k != j]
            edited = ast.BoolOp(op=ast.And(), values=rem) if len(rem) > 1 else rem[0]
            try:
                replacement = ast.unparse(edited)
                start = prefixes[node.test.lineno-1] + node.test.col_offset
                end = prefixes[node.test.end_lineno-1] + node.test.end_col_offset
                changed = (text[:start] + replacement + text[end:]).encode("utf8")
                ast.parse(changed)
            except (SyntaxError, ValueError):
                continue
            if changed != source:
                found.append({"method": "single-conjunct-ablation", "line": node.lineno,
                              "dropped": j, "source": changed,
                              "sha256": hashlib.sha256(changed).hexdigest()})
    found.sort(key=lambda c:(c["line"],c["dropped"],c["sha256"]))
    uniq=[];seen=set()
    for item in found:
        if item["sha256"] not in seen:
            uniq.append(item);seen.add(item["sha256"])
    return uniq[:MAX_CANDIDATES]

def self_test():
    raw = b'''def render(a,b,c):\n    if a and b and c:\n        return f"/{1}"\n    return "absolute"\n'''
    arr=generate(raw)
    assert len(arr)==3
    assert all(ast.parse(x["source"]) for x in arr)
    return True
if __name__=="__main__":
    print("EQUAL_INFO_GUARD_ABLATION_PREFLIGHT",self_test())
