"""Export-level dependent projection controls, checked by two independent kernels.

Build small source telescopes using named binders, then encode de Bruijn
indices. This generator never imports Nucleus's reconstruction or typing
code. Gruszka must decide every fixture. Nucleus must accept the positives,
reject proven out-of-range indices, and never accept an invalid fixture.
All exact input bytes and both diagnostics are retained for replay.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
from renovation_gruszka_bridge_20261125 import bridge


def var(n): return ("var", n)
def sort(n): return ("sort", n)
def const(n): return ("const", n)
def app(f, *args):
    for a in args:
        f = ("app", f, a)
    return f
def bind(tag, ds, body):
    for n, d in reversed(ds):
        body = (tag, n, d, body)
    return body
def proj(i, s): return ("proj", i, s)


class Export:
    def __init__(self, label):
        self.rows = [{"meta": {"exporter": {"name": "independent-projection-controls", "version": "1"},
                               "format": {"version": "3.2.0"}}}]
        self.names = {}
        self.levels = {0: 0}
        self.exprs = {}
        self.family = self.name(label)
        self.ctor = self.name("mk", self.family)
        self.rec = self.name("rec", self.family)
        self.u = self.name("u")
        self.result = self.name("getDependent", self.family)
        self.constants = {"I": self.family, "mk": self.ctor}

    def name(self, s, pre=0):
        key = (pre, s)
        if key not in self.names:
            idx = len(self.names) + 1
            self.rows.append({"in": idx, "str": {"pre": pre, "str": s}})
            self.names[key] = idx
        return self.names[key]

    def level(self, n):
        if n not in self.levels:
            body = {"param": self.u} if n == "u" else {"succ": self.level(n - 1)}
            idx = len(self.levels)
            self.levels[n] = idx
            self.rows.append({"il": idx, **body})
        return self.levels[n]

    def expr(self, t, ctx=()):
        tag, *args = t
        if tag == "var":
            body = {"bvar": ctx[::-1].index(args[0])}
        elif tag == "sort":
            body = {"sort": self.level(args[0])}
        elif tag == "const":
            body = {"const": {"name": self.constants[args[0]], "us": []}}
        elif tag == "app":
            body = {"app": {"fn": self.expr(args[0], ctx), "arg": self.expr(args[1], ctx)}}
        elif tag in ("forallE", "lam"):
            n, d, b = args
            body = {tag: {"name": 0, "binderInfo": "default",
                          "type": self.expr(d, ctx), "body": self.expr(b, ctx + (n,))}}
        elif tag == "proj":
            body = {"proj": {"typeName": self.family, "idx": args[0], "struct": self.expr(args[1], ctx)}}
        else:
            raise ValueError(tag)
        key = json.dumps(body, sort_keys=True)
        if key not in self.exprs:
            idx = len(self.exprs)
            self.exprs[key] = idx
            self.rows.append({"ie": idx, **body})
        return self.exprs[key]

    def block(self, params, fields, level):
        i = app(const("I"), *(var(n) for n, _ in params))
        ctor = app(const("mk"), *(var(n) for n, _ in params + fields))
        common = params + [("motive", bind("forallE", [("major", i)], sort("u"))),
                           ("minor", bind("forallE", fields, app(var("motive"), ctor)))]
        it = self.expr(bind("forallE", params, sort(level)))
        ct = self.expr(bind("forallE", params + fields, i))
        rt = self.expr(bind("forallE", common + [("major", i)], app(var("motive"), var("major"))))
        rhs = self.expr(bind("lam", common + fields, app(var("minor"), *(var(n) for n, _ in fields))))
        self.rows.append({"inductive": {
            "types": [{"name": self.family, "type": it, "levelParams": [], "all": [self.family],
                       "ctors": [self.ctor], "numParams": len(params), "numIndices": 0, "numNested": 0,
                       "isRec": False, "isUnsafe": False, "isImpredicative": False, "isK": False,
                       "hasProjections": True, "hasEta": True, "hasLargeElim": True}],
            "ctors": [{"name": self.ctor, "type": ct, "levelParams": [], "induct": self.family,
                       "cidx": 0, "numParams": len(params), "numFields": len(fields), "isUnsafe": False}],
            "recs": [{"name": self.rec, "type": rt, "levelParams": [self.u], "all": [self.family],
                      "numParams": len(params), "numIndices": 0, "numMinors": 1, "numMotives": 1,
                      "k": False, "isUnsafe": False,
                      "rules": [{"ctor": self.ctor, "nfields": len(fields), "rhs": rhs}]}]}})
        return i

    def declaration(self, binders, target, value):
        ty = self.expr(bind("forallE", binders, target))
        val = self.expr(bind("lam", binders, value))
        self.rows.append({"def": {"name": self.result, "levelParams": [], "type": ty, "value": val,
                                  "all": [self.result], "hints": "opaque", "safety": "safe"}})
        return self.rows


def fixture(kind, wrong=None, renamed=False):
    label = ("UnseenDependent_" if renamed else "Dependent_") + kind
    e = Export(label)
    if kind == "proof_field":
        params = [("alpha", sort(1)), ("pred", bind("forallE", [("x", var("alpha"))], sort(0)))]
        fields = [("x", var("alpha")), ("hx", app(var("pred"), var("x")))]
        family = e.block(params, fields, 1)
        binders = params + [("s", family)]
        target = app(var("pred"), proj(0, var("s")))
        value = proj(1, var("s"))
        if wrong == "scrutinee":
            binders += [("t", family)]
            target = app(var("pred"), proj(0, var("t")))
        elif wrong == "parameter":
            binders += [("q", bind("forallE", [("x", var("alpha"))], sort(0)))]
            target = app(var("q"), proj(0, var("s")))
    elif kind == "type_field":
        family = e.block([], [("alpha", sort(1)), ("x", var("alpha"))], 2)
        binders = [("s", family)]
        target = proj(0, var("s"))
        value = proj(1, var("s"))
        if wrong == "scrutinee":
            binders += [("t", family)]
            target = proj(0, var("t"))
        elif wrong == "field":
            value = proj(0, var("s"))
    else:
        raise ValueError(kind)
    return e.declaration(binders, target, value)


def controls():
    for kind in ("proof_field", "type_field"):
        for renamed in (False, True):
            yield kind + (":renamed" if renamed else ""), fixture(kind, renamed=renamed), 0, True
        for wrong in (("scrutinee", "parameter") if kind == "proof_field" else ("scrutinee", "field")):
            yield kind + ":wrong-" + wrong, fixture(kind, wrong=wrong), 1, False
        bad = copy.deepcopy(fixture(kind))
        for row in bad:
            if "proj" in row and row["proj"]["idx"] == 1:
                row["proj"]["idx"] = 999
        yield kind + ":out-of-range", bad, 1, True


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checker", type=Path, required=True)
    p.add_argument("--comparator-runner", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    inputs = a.out / "dependent-inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith("NUCLEUS_")}
    rows = []
    for name, source, expected, required in controls():
        raw = b"".join((json.dumps(r, separators=(",", ":")) + "\n").encode() for r in source)
        file = inputs / (name.replace(":", "-") + ".ndjson")
        file.write_bytes(raw)
        n = subprocess.run([str(a.checker)], input=raw, capture_output=True, timeout=60, env=env)
        derived, receipt = bridge(raw)
        comparator_file = file.with_suffix(".gruszka.ndjson")
        comparator_file.write_bytes(derived)
        g = subprocess.run(["sh", str(a.comparator_runner), str(comparator_file), "1"], capture_output=True, timeout=60)
        row = {"case": name, "sha256": hashlib.sha256(raw).hexdigest(), "expected": expected,
               "required": required, "nucleus": n.returncode, "gruszka": g.returncode,
               "comparator_adapter": receipt,
               "nucleus_diagnostic": n.stderr.decode(errors="replace"),
               "gruszka_diagnostic": (g.stdout + g.stderr).decode(errors="replace")}
        rows.append(row)
        (a.out / "dependent-projection-controls.json").write_text(json.dumps(rows, indent=2) + "\n")
        print("DEPENDENT_PROJECTION", json.dumps(row), flush=True)
        assert g.returncode == expected, row
        assert n.returncode in (0, 1, 2), row
        assert n.returncode == expected or (n.returncode == 2 and not required), row
    assert len(rows) == 10


if __name__ == "__main__":
    main()
