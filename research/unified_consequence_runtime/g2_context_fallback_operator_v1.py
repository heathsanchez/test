#!/usr/bin/env python3
"""Bounded source-neutral environment-context fallback generator, V1.

Candidate generation depends on original AST structure and failing native
output class, not upstream repaired code, project/test names, or future source.
A guarded relative-return can be extended only when an existing environmental
OR dependency is wholly absent; its existing external-force negation persists.
"""
from __future__ import annotations
import ast
import hashlib
import re
from urllib.parse import urlsplit

MAX_CANDIDATES = 12

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def observation(native_stdout: str) -> dict:
    # A source-neutral runtime observation; no test name / project identifier.
    # pytest's assertion diff formats are heuristic, hence observed_class is
    # merely a feature and NEVER a native success oracle.
    urls = sorted(set(re.findall(r"https?://[^\s'\"<>]+", native_stdout)))
    relative_literals = sorted(set(re.findall(r"""['"](/[^'"\s]*)['"]""", native_stdout)))
    return {"absolute_urls": urls[:8], "relative_literals": relative_literals[:8],
            "class": "ABSOLUTE_VS_RELATIVE" if urls and relative_literals
                     else "UNKNOWN_FAILURE_SHAPE"}

def _offset(lines: list[str], lineno: int, column: int) -> int:
    return sum(len(x) for x in lines[:lineno - 1]) + column

def _is_relative_return(stmt: ast.stmt) -> bool:
    if not isinstance(stmt, ast.Return) or not isinstance(stmt.value, ast.JoinedStr):
        return False
    chunks = "".join(x.value for x in stmt.value.values if isinstance(x, ast.Constant) and isinstance(x.value, str))
    return "/" in chunks and "://" not in chunks and "//" not in chunks

def generate(original: bytes) -> list[dict]:
    text = original.decode("utf8")
    lines = text.splitlines(keepends=True)
    tree = ast.parse(text)
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.If) or not isinstance(n.test, ast.BoolOp) or not isinstance(n.test.op, ast.And):
            continue
        if not any(_is_relative_return(s) for s in n.body):
            continue
        prefixes = [v for v in n.test.values if isinstance(v, ast.UnaryOp) and isinstance(v.op, ast.Not)]
        contexts = [v for v in n.test.values if isinstance(v, ast.BoolOp) and isinstance(v.op, ast.Or)]
        for prefix in prefixes:
            for context in contexts:
                # Positive disjunction of source-owned environmental flags, not
                # inferred from patched contributor code.
                if not all(isinstance(x, (ast.Attribute, ast.Name)) for x in context.values):
                    continue
                old_expr = ast.get_source_segment(text, n.test)
                if not old_expr:
                    continue
                candidate_expr = ("(" + old_expr + ") or (("
                                  + ast.unparse(prefix) + ") and not ("
                                  + ast.unparse(context) + "))")
                start = _offset(lines, n.test.lineno, n.test.col_offset)
                end = _offset(lines, n.test.end_lineno, n.test.end_col_offset)
                candidate = (text[:start] + candidate_expr + text[end:]).encode("utf8")
                try:
                    ast.parse(candidate)
                except SyntaxError:
                    continue
                if candidate == original:
                    continue
                out.append({"method": "unguarded-context-fallback", "line": n.lineno,
                            "context": ast.unparse(context),
                            "prefix": ast.unparse(prefix),
                            "original_sha256": digest(original),
                            "patched_sha256": digest(candidate),
                            "source": candidate})
    out.sort(key=lambda c: (len(c["source"]) - len(original), c["line"], c["context"]))
    unique, seen = [], set()
    for c in out:
        if c["patched_sha256"] not in seen:
            unique.append(c)
            seen.add(c["patched_sha256"])
    return unique[:MAX_CANDIDATES]

def self_test():
    s = b'''def render(relative=False, external=False, a=False, b=False):
    if (
        not external
        and (a or b)
        and (relative or a)
    ):
        return f"/{1}"
    return f"https://example.test/{1}"
'''
    c = generate(s)
    assert len(c) == 2, (len(c), c)
    scope = {}
    exec(c[0]["source"], scope)
    # Without either environmental bit, generated fallback must be relative;
    # explicit external preference must remain binding.
    assert scope["render"]() == "/1"
    assert scope["render"](external=True) == "https://example.test/1"
    assert scope["render"](a=True) == "/1"
    assert scope["render"](b=True) == "https://example.test/1"
    return len(c)

if __name__ == "__main__":
    print({"synthetic_candidate_count": self_test(),
           "status": "BOUNDED_GENERATOR_PREFLIGHT_ONLY"})
