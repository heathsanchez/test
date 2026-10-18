#!/usr/bin/env python3
"""V2 of the Packaging-trained strict-whole-input syntax observation.

Prospective extension is committed and training-qualified BEFORE any schedule
source/test/native outcome is read. It adds inline regex call sites and bounded
composition to the original byte-frozen V1 generator, without project hints.
"""
from __future__ import annotations

import ast
import hashlib
import itertools

from research.unified_consequence_runtime import g2_packaging_boundary_genesis_v1 as parent

CAP = 32
MODE = "STRICT_WHOLE_INPUT_REGEX_V2_SYNTAX_CLOSURE"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def anchored(node: ast.AST, names: dict[str, str]) -> bool:
    text = node.value if isinstance(node,ast.Constant) and isinstance(node.value,str) else (
        names.get(node.id,"") if isinstance(node,ast.Name) else "")
    return bool(text) and text.endswith("$")

def module_patterns(root: ast.Module) -> dict[str,str]:
    names: dict[str,str] = {}
    for statement in root.body:
        if not isinstance(statement,(ast.Assign,ast.AnnAssign)):
            continue
        targets = statement.targets if isinstance(statement,ast.Assign) else [statement.target]
        if len(targets)!=1 or not isinstance(targets[0],ast.Name):
            continue
        value=statement.value
        if value is None: continue
        if isinstance(value,ast.Constant) and isinstance(value.value,str):
            names[targets[0].id]=value.value
        elif (isinstance(value,ast.Call) and isinstance(value.func,ast.Attribute)
              and isinstance(value.func.value,ast.Name)
              and value.func.value.id=="re" and value.func.attr=="compile"
              and value.args):
            inner=value.args[0]
            names[targets[0].id]=(inner.value if isinstance(inner,ast.Constant)
                                   and isinstance(inner.value,str) else names.get(
                                       inner.id,"") if isinstance(inner,ast.Name) else "")
    return names

def inline_edits(raw: bytes) -> list[dict]:
    root=ast.parse(raw.decode("utf-8"))
    names=module_patterns(root)
    entries=[]
    for n in ast.walk(root):
        if not (isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
                and n.func.attr in ("match","search")
                and isinstance(n.func.value,ast.Name) and n.func.value.id=="re"
                and n.args and anchored(n.args[0],names)):
            continue
        begin,end=parent.span(raw,n.func)
        before=raw[begin:end]
        suffix=("."+n.func.attr).encode("ascii")
        if not before.endswith(suffix):continue
        after=before[:-len(n.func.attr)] + b"fullmatch"
        if after==before:continue
        entries.append(dict(start=begin,end=end,source_line=n.lineno,
                            original=before,replacement=after,
                            family="inline_regex_fullmatch"))
    return sorted(entries,key=lambda e:(e["start"],e["end"]))

def apply(raw: bytes, edits: list[dict]) -> bytes:
    ordered=sorted(edits,key=lambda e:e["start"],reverse=True)
    previous=len(raw)+1
    out=raw
    for e in ordered:
        a,b=e["start"],e["end"]
        if not (a<b<=previous and raw[a:b]==e["original"]):
            raise ValueError("REJECTED_OVERLAPPING_OR_CHANGED_EDIT")
        out=out[:a]+e["replacement"]+out[b:]
        previous=a
    ast.parse(out.decode("utf-8"))
    return out

def enumerate_candidates(source: str | bytes) -> list[dict]:
    raw=source.encode("utf-8") if isinstance(source,str) else source
    ast.parse(raw.decode("utf-8"))
    candidates=list(parent.enumerate_candidates(raw))
    edits=inline_edits(raw)
    # Fixed finite closure: all one-site edits, then 2,3,4-site combinations,
    # and an all-sites simultaneous edit if >4 sites. No outcome-based tuning.
    combinations=[]
    for count in range(1,min(4,len(edits))+1):
        combinations.extend(itertools.combinations(edits,count))
        if len(combinations)>120:break
    if len(edits)>4 and len(edits)<=16:
        combinations.append(tuple(edits))
    for selection in combinations[:160]:
        try:
            changed=apply(raw,list(selection))
        except (SyntaxError,ValueError):
            continue
        if changed==raw:continue
        candidates.append({
            "family":"inline_regex_fullmatch_composed" if len(selection)>1 else
                     "inline_regex_fullmatch",
            "line":min(e["source_line"] for e in selection),
            "source_sha256":sha(changed),
            "delta_bytes":abs(len(changed)-len(raw)),
            "site_count":len(selection),
            "source":changed
        })
    distinct={}
    for x in candidates:
        distinct.setdefault(x["source_sha256"],x)
    return sorted(distinct.values(),key=lambda c:(
        c["delta_bytes"],c["line"],c["family"],c["source_sha256"]))[:CAP]

def controls() -> dict:
    # Constructed inputs, not source/test from any heldout repo.
    test=r'''import re
A = r"^k[a-z]+$"
B = r"^v[0-9]+$"
def valid_a(value):
    return re.match(A,value) is not None
def valid_b(value):
    return re.search(B,value) is not None
'''
    options=enumerate_candidates(test)
    assert len(options)>=3, ("INSUFFICIENT_OPTIONS",len(options))
    winner=[]
    for c in options:
        ns={}
        exec(compile(c["source"],"<constructed-regex-test>","exec"),ns)
        if (ns["valid_a"]("kabc") and ns["valid_b"]("v12")
            and not ns["valid_a"]("kabc\n")
            and not ns["valid_b"]("v12\n")):
            winner.append(c)
    assert any(x.get("site_count")==2 for x in winner), "TWO_SITE_CLOSURE_ABSENT"
    assert not enumerate_candidates(b'def validator(x): return x in (1,2)\n')
    return {"constructed_candidates":len(options),"two_site_correct":True,
            "source_neutral":True,"max_candidates":CAP}
