#!/usr/bin/env python3
"""Equal-information regex API edit baseline, frozen before future opening.

Enumerates one-site .match -> .fullmatch changes for any receiver of a
source-owned re.compile binding, independent of future issue names or tests.
This can tie the acquired method. It is NOT a strong coding-agent comparator.
"""
import ast
import hashlib

def generate(original:bytes):
    text=original.decode("utf8")
    lines=text.splitlines(keepends=True)
    off=lambda ln,col:sum(map(len,lines[:ln-1]))+col
    tree=ast.parse(text)
    compiled=set()
    for x in ast.walk(tree):
        if isinstance(x,ast.Assign) and len(x.targets)==1 and isinstance(x.targets[0],ast.Name):
            c=x.value
            if (isinstance(c,ast.Call) and isinstance(c.func,ast.Attribute)
                and isinstance(c.func.value,ast.Name) and c.func.value.id=="re"
                and c.func.attr=="compile"):
                compiled.add(x.targets[0].id)
    results=[]
    for x in ast.walk(tree):
        if (isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute)
            and x.func.attr=="match" and isinstance(x.func.value,ast.Name)
            and x.func.value.id in compiled):
            pos=off(x.func.end_lineno,x.func.end_col_offset)
            if text[pos-5:pos]!="match":continue
            changed=(text[:pos-5]+"fullmatch"+text[pos:]).encode()
            try:ast.parse(changed)
            except SyntaxError:continue
            results.append({"mechanism":"independent_compiled_regex_fullmatch",
                            "source":changed,
                            "patched_sha256":hashlib.sha256(changed).hexdigest(),
                            "line":x.lineno})
    results.sort(key=lambda x:(x["line"],x["patched_sha256"]))
    return results[:12]

def self_test():
    src=b'''import re
P=re.compile(r"^x$")
def valid(s): return bool(P.match(s))
'''
    assert len(generate(src))==1
    return True
if __name__=="__main__":
    print("EQUAL_INFO_REGEX_BASELINE_PREFLIGHT",self_test())
