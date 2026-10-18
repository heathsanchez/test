#!/usr/bin/env python3
"""Prospectively frozen same-information AST deletion baseline for G2 V1.

Same eligible branch patterns, candidate count, protected test oracle and
selection budget as acquired guard-fallback method. It may not use training
outcomes, author fixes, source-specific names, or the learned fallback rewrite.
"""
import ast
import hashlib

MAX_CANDIDATES=16
BASELINE_ID="drop_context_guard_v1"

def enumerate_candidates(source: str) -> list[dict]:
    syntax=ast.parse(source)
    lines=source.splitlines(keepends=True)
    def offset(row,col):
        return sum(len(v) for v in lines[:row-1])+col
    out=[]
    for node in ast.walk(syntax):
        if not isinstance(node,ast.If) or not isinstance(node.test,ast.BoolOp):
            continue
        if not isinstance(node.test.op,ast.And) or len(node.test.values)<3:
            continue
        if not any(isinstance(x,ast.Return) for x in node.body):
            continue
        terms=node.test.values
        for i in range(1,len(terms)-1):
            guard=terms[i]
            if not isinstance(guard,ast.BoolOp) or not isinstance(guard.op,ast.Or):
                continue
            new=ast.BoolOp(op=ast.And(),values=terms[:i]+terms[i+1:])
            ast.fix_missing_locations(new)
            start=offset(node.test.lineno,node.test.col_offset)
            end=offset(node.test.end_lineno,node.test.end_col_offset)
            old=source[start:end]
            edited=source[:start]+ast.unparse(new)+source[end:]
            if edited==source:continue
            try:
                ast.parse(edited)
                compile(edited,"<baseline-candidate>","exec")
            except (SyntaxError,ValueError):continue
            out.append({
                "tag":BASELINE_ID,"if_line":node.lineno,"guard_term_index":i,
                "candidate_source_sha256":hashlib.sha256(edited.encode()).hexdigest(),
                "bytes_added":len(edited.encode())-len(source.encode()),
                "_edited":edited
            })
    out.sort(key=lambda x:(abs(x["bytes_added"]),x["if_line"],x["guard_term_index"]))
    return out[:MAX_CANDIDATES]
