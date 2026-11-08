"""Inspect the immutable n7 export's actual Expr DAG; not a proof verifier.

The output is a read-only, source-bound obstruction inventory. No inferred
equality or ACCEPT is issued based on syntactic heads or hashes.
"""
import collections
import hashlib
import json
import pathlib
import sys

EXPECTED_SOURCE = "abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35"
ROOTS = (8796, 8799, 8835, 8837)
NAME_IDS = (146, 147, 169)

def parse(source: bytes):
    digest = hashlib.sha256(source).hexdigest()
    if digest != EXPECTED_SOURCE:
        raise ValueError(f"source hash drift: {digest}")
    names, exprs, declarations = {}, {}, []
    version = None
    for line in source.splitlines():
        rec = json.loads(line)
        if "meta" in rec:
            version = rec["meta"]["format"]["version"]
        if "in" in rec:
            tag = int(rec["in"])
            if tag in names: raise ValueError("duplicate name id")
            names[tag] = rec
        if "ie" in rec:
            tag = int(rec["ie"])
            if tag in exprs: raise ValueError("duplicate expression id")
            exprs[tag] = rec
        for k in ("def", "thm", "axiom", "opaque"):
            if k in rec:
                declarations.append((k, rec[k]))
    if version != "3.1.0":
        raise ValueError(f"format drift: {version!r}")
    if any(r not in exprs for r in ROOTS):
        raise ValueError("target expr absent")
    if any(r not in names for r in NAME_IDS):
        raise ValueError("target names absent")
    return names, exprs, declarations

def resolve_name(n, names):
    parts = []
    seen = set()
    while n != 0:
        if n in seen or n not in names:
            raise ValueError("invalid name prefix cycle")
        seen.add(n)
        rec = names[n]
        if "str" in rec:
            info = rec["str"]
            parts.append(str(info["str"]))
            n = int(info["pre"])
        elif "num" in rec:
            info = rec["num"]
            parts.append(str(info["i"]))
            n = int(info["pre"])
        else:
            raise ValueError("unsupported name")
    return ".".join(reversed(parts))

def node_info(exprs, eid):
    e = exprs[eid]
    for k in ("app", "forallE", "lam", "letE", "proj", "mdata", "const", "bvar", "sort", "natVal", "strVal"):
        if k in e:
            return k, e[k]
    raise ValueError("unsupported expression tag")

def dependencies(exprs, eid):
    kind, payload = node_info(exprs, eid)
    if kind == "app":
        return [int(payload["fn"]), int(payload["arg"])]
    if kind in ("forallE", "lam"):
        return [int(payload["type"]), int(payload["body"])]
    if kind == "letE":
        return [int(payload["type"]), int(payload["value"]), int(payload["body"])]
    if kind == "proj":
        return [int(payload["struct"])]
    if kind == "mdata":
        return [int(payload["expr"])]
    return []

def summarize(root, names, exprs):
    visited = set()
    stack = [root]
    kinds = collections.Counter()
    consts = collections.Counter()
    max_bvar = 0
    refs = 0
    while stack:
        eid = stack.pop()
        if eid in visited: continue
        if eid not in exprs: raise ValueError("dangling expression id")
        visited.add(eid)
        kind, payload = node_info(exprs, eid)
        kinds[kind] += 1
        if kind == "const":
            consts[resolve_name(int(payload["name"]), names)] += 1
        if kind == "bvar": max_bvar = max(max_bvar, int(payload))
        children = dependencies(exprs, eid)
        refs += len(children)
        stack.extend(children)
    # Flatten *only* the direct application spine, not an unproved conversion.
    spine = []
    here = root
    for _ in range(150):
        kind, info = node_info(exprs, here)
        if kind != "app": break
        spine.append(int(info["arg"]))
        here = int(info["fn"])
    kind, head = node_info(exprs, here)
    if kind == "const":
        head_repr = resolve_name(int(head["name"]), names)
    else:
        head_repr = f"{kind}:{head}"[:120]
    return {
        "root": root, "root_kind": node_info(exprs, root)[0],
        "dag_nodes": len(visited), "dag_edges": refs,
        "expr_kinds": dict(sorted(kinds.items())),
        "max_bvar": max_bvar, "head": head_repr,
        "direct_spine_length": len(spine),
        "direct_spine_arguments": list(reversed(spine))[:22],
        "named_consts": dict(sorted(consts.items(), key=lambda p: (-p[1], p[0]))[:60]),
        "subdag_sha256": hashlib.sha256(json.dumps(
            [(i, exprs[i]) for i in sorted(visited)], sort_keys=True,
            separators=(",",":")).encode()).hexdigest(),
    }

def report(source):
    names, exprs, declarations = parse(source)
    owners = [
        {"kind": k, "name": resolve_name(int(v["name"]), names),
         "type": int(v["type"]), "value": int(v.get("value",-1))}
        for k,v in declarations if resolve_name(int(v["name"]), names) == "countermodel"
    ]
    if len(owners) != 1:
        raise ValueError("countermodel declaration not uniquely identified")
    roots = {str(i): summarize(i, names, exprs) for i in ROOTS}
    return {
        "kind": "C65_SOURCE_INVENTORY_NOT_CERTIFICATE",
        "verification_reuse_authority": "NONE",
        "nucleus_standard_verdict": "UNKNOWN",
        "source_sha256": EXPECTED_SOURCE,
        "format_version": "3.1.0",
        "owner": owners[0],
        "names": {str(i):resolve_name(i,names) for i in NAME_IDS},
        "roots": roots,
        "total_expr_records": len(exprs),
        "total_name_records": len(names),
        "claim_soundness_or_speed": False,
    }

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: c65_source_inventory.py good/perf/magma-list-pair-n7.ndjson report.json")
    inp = pathlib.Path(sys.argv[1]).read_bytes()
    out = report(inp)
    pathlib.Path(sys.argv[2]).write_text(json.dumps(out, indent=2,sort_keys=True)+"\n")
    print("C65_OWNER="+json.dumps(out["owner"],sort_keys=True))
    print("C65_NAME_IDS="+json.dumps(out["names"],sort_keys=True))
    for r,v in out["roots"].items():
        print("C65_ROOT="+json.dumps({k:v[k] for k in ("root","dag_nodes","head","direct_spine_length","direct_spine_arguments","subdag_sha256")},sort_keys=True))
    print("C65_AUTOMATIC_ACCEPT_AUTHORITY=NONE")
