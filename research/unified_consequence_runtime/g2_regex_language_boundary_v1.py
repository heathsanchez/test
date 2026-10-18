#!/usr/bin/env python3
"""Source-neutral regular-language boundary observation and repair generator V1.

For an anchored compiled regular expression, accepts a candidate iff changing
.match to .fullmatch OR Python's '$' to a genuine end-of-string anchor
has a byte-exact one-site AST-enumerated edit. No test names, source identities,
patch knowledge, or future-outcome feedback are inputs to candidate generation.
"""
from __future__ import annotations
import ast
import hashlib
import re

MAX_CANDIDATES=12

def sha(data):return hashlib.sha256(data).hexdigest()

def off(lines,ln,col):
    return sum(len(x) for x in lines[:ln-1])+col

def replace_span(text, lines, start, end, replacement):
    a=off(lines,start[0],start[1]);b=off(lines,end[0],end[1])
    result=text[:a]+replacement+text[b:]
    try:ast.parse(result)
    except SyntaxError:return None
    return result.encode("utf8")

def generate(original:bytes):
    text=original.decode("utf8")
    lines=text.splitlines(keepends=True)
    tree=ast.parse(text)
    regex_defs={}
    definitions={}
    for n in ast.walk(tree):
        if not isinstance(n,ast.Assign) or len(n.targets)!=1 or not isinstance(n.targets[0],ast.Name):
            continue
        value=n.value
        if not (isinstance(value,ast.Call) and isinstance(value.func,ast.Attribute)
                and isinstance(value.func.value,ast.Name) and value.func.value.id=="re"
                and value.func.attr=="compile" and value.args):
            continue
        literal=value.args[0]
        if not isinstance(literal,ast.Constant) or not isinstance(literal.value,str):
            continue
        try:re.compile(literal.value)
        except re.error:continue
        if literal.value.startswith("^") and literal.value.endswith("$"):
            regex_defs[n.targets[0].id]=literal.value
            definitions[n.targets[0].id]=literal
    out=[]
    for call in ast.walk(tree):
        if not (isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute)
                and call.func.attr=="match" and isinstance(call.func.value,ast.Name)
                and call.func.value.id in regex_defs):
            continue
        ident=call.func.value.id
        # AST attr ends with ".match"; source-site verification prevents retargeting.
        pos=off(lines,call.func.end_lineno,call.func.end_col_offset)
        if text[pos-5:pos]!="match":
            continue
        candidate=(text[:pos-5]+"fullmatch"+text[pos:]).encode("utf8")
        ast.parse(candidate)
        out.append({"mechanism":"require_complete_match",
                    "bounded_observation":"anchored-pattern-with-prefix-matcher",
                    "source":candidate,"original_sha256":sha(original),
                    "patched_sha256":sha(candidate),"line":call.lineno})
        literal=definitions[ident]
        source_literal=ast.get_source_segment(text,literal)
        if not source_literal or not source_literal.endswith(("$'",'$"')):
            continue
        # Change exactly the terminal '$' within a compiled anchored pattern.
        # A raw literal is preferred; Python nonraw escaped backslash would
        # introduce an unrecognized-escape warning and is therefore refused.
        if not source_literal.startswith(('r"', "r'", 'R"', "R'")):
            continue
        start=(literal.lineno,literal.col_offset)
        end=(literal.end_lineno,literal.end_col_offset)
        changed=replace_span(text,lines,start,end,source_literal[:-2]+r"\Z"+source_literal[-1])
        if changed is not None:
            out.append({"mechanism":"absolute_end_anchor",
                        "bounded_observation":"dollar-accepts-final-newline",
                        "source":changed,"original_sha256":sha(original),
                        "patched_sha256":sha(changed),"line":literal.lineno})
    # Before outcomes, prefer source-small and test-independent changes.
    out.sort(key=lambda x:(len(x["source"])-len(original), x["line"], x["mechanism"]))
    unique,seen=[],set()
    for item in out:
        if item["patched_sha256"] not in seen:
            unique.append(item);seen.add(item["patched_sha256"])
    return unique[:MAX_CANDIDATES]

def self_test():
    src=b'''import re
RULE = re.compile(r"^one[.]txt$")
def accepts(text):
    return bool(RULE.match(text))
'''
    d={}
    exec(src,d)
    assert d["accepts"]("one.txt\n") is True
    c=generate(src)
    assert len(c)==2,[(x["mechanism"],x["line"]) for x in c]
    for x in c:
        q={}
        exec(x["source"],q)
        assert q["accepts"]("one.txt")
        assert not q["accepts"]("one.txt\n")
    return len(c)

if __name__=="__main__":
    print("REGEX_BOUNDARY_GENERATOR_PREFLIGHT",self_test())
