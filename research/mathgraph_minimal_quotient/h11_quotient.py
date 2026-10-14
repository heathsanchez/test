#!/usr/bin/env python3
"""JPL-inspired finite observational quotient for exact pinned native h11.

One source-independent input grammar, parser-interface observer and exhaustive
finite-horizon distinguishing basis across all selected PRs. This is NOT a
complete parser specification or a source-to-behaviour proof.
"""
from __future__ import annotations

import ast
import hashlib
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import collections

SOURCES = {
    "base": "62c5068c971579d61fa1b55373390e12f25fd856",
    "206": "05972a8b34faeb91c22b9a6283da84e45e7f0781",
    "198": "46a076d96fbf9b18868c45ddfd2dcc0e2077f2a5",
    "207": "ec2e2dbbdc61587911dda3dd5f868f14ab0733f4",
}
SCHEDULES = ("whole", "cut1", "half", "bytewise")
SUFFIXES = (
    b"\r\n", b"\r\n\r\n", b"X: z\r\n\r\n",
    b" \tmore\r\n\r\n", b"Host: h\r\n\r\n",
    b"x\r\n\r\n",
)
CAPS = (24, 48, 96, 128, 256)
LENGTHS = (0, 1, 8, 24, 48, 96, 160)
SAMPLE_PREFIXES = 34


def digest(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def build_cases():
    wires = {}
    for version in (b"1.0", b"1.1"):
        start = b"GET / HTTP/" + version + b"\r\n"
        host = b"Host: h\r\n" if version == b"1.1" else b""
        for length in LENGTHS:
            value = b"a" * length
            forms = {
                "ordinary": b"X: " + value + b"\r\n",
                "fold-space": b"X: before " + value + b"\r\n more\r\n",
                "fold-tab": b"X: before \t" + value + b"\r\n\tmore\r\n",
                "fold-double": b"X: before \t" + value + b"\r\n \tmore \t\r\n\tend\r\n",
                "content-length": b"Content-Length: " + str(length).encode() + b"\r\n",
                "duplicate-length": b"Content-Length: 0\r\nContent-Length: 0\r\n",
                "transfer": b"Transfer-Encoding: chunked\r\n",
                "invalid": b"Bad Header: " + value + b"\r\n",
            }
            for kind, extra in forms.items():
                wire = start + host + extra + b"\r\n"
                wires[(version.decode(), kind, length)] = wire
        wires[(version.decode(), "control-no-extra", 0)] = start + host + b"\r\n"
    cases = []
    for (version, kind, size), wire in sorted(wires.items()):
        for cap in CAPS:
            cases.append(dict(id=f"{version}:{kind}:{size}:cap{cap}",
                              version=version, kind=kind, size=size,
                              cap=cap, wire_hex=wire.hex(), nbytes=len(wire)))
    # A small, predeclared prefix bank and suffix test-language. Prefixes
    # are not chosen after reading PR diffs or native results.
    small = sorted(cases, key=lambda c: (c["nbytes"], c["id"]))
    picks = []
    seen = set()
    for c in small:
        if c["cap"] not in (48, 96, 128) or c["kind"] not in (
                "ordinary", "fold-space", "fold-double", "content-length",
                "invalid", "control-no-extra"):
            continue
        wire = bytes.fromhex(c["wire_hex"])
        points = [max(1, len(wire) // 2),
                  wire.find(b"\r\n") + 2,
                  max(1, len(wire) - 4)]
        for cut in points:
            if not 0 < cut < len(wire):
                continue
            ident = (wire[:cut], c["cap"])
            if ident not in seen:
                seen.add(ident)
                picks.append({"prefix_hex": wire[:cut].hex(), "cap": c["cap"],
                              "parent": c["id"], "cut": cut})
            if len(picks) >= SAMPLE_PREFIXES:
                break
        if len(picks) >= SAMPLE_PREFIXES:
            break
    return {"cases": cases, "prefix_cases": picks,
            "suffixes": [s.hex() for s in SUFFIXES]}


def categorise_event(h11, event):
    if event is h11.NEED_DATA:
        return {"disposition": "INCOMPLETE"}
    if event is h11.PAUSED:
        return {"disposition": "PAUSED"}
    if isinstance(event, (h11.Request, h11.Response, h11.InformationalResponse)):
        headers = [(a.decode("latin-1"), b.decode("latin-1"))
                   for a, b in event.headers]
        try:
            raw_headers = [(a.decode("latin-1"), b.decode("latin-1"))
                           for a, b in event.headers.raw_items()]
        except AttributeError:
            raw_headers = headers
        d = {"disposition": "ACCEPT", "event": type(event).__name__,
             "headers": headers, "raw_headers": raw_headers}
        for field in ("method", "target", "http_version", "status_code"):
            attr = getattr(event, field, None)
            if isinstance(attr, bytes):
                attr = attr.decode("latin-1")
            if attr is not None:
                d[field] = attr
        return d
    return {"disposition": "OTHER", "event": type(event).__name__}


def run_wire(h11, wire, cap, schedule):
    if schedule == "whole":
        chunks = (wire,)
    elif schedule == "cut1":
        chunks = (wire[:1], wire[1:])
    elif schedule == "half":
        m = len(wire) // 2
        chunks = (wire[:m], wire[m:])
    elif schedule == "bytewise":
        chunks = tuple(wire[i:i+1] for i in range(len(wire)))
    else:
        raise AssertionError(schedule)
    conn = h11.Connection(h11.SERVER, max_incomplete_event_size=cap)
    result = {"disposition": "INCOMPLETE"}
    for chunk in chunks:
        if not chunk:
            continue
        try:
            conn.receive_data(chunk)
            event = conn.next_event()
            result = categorise_event(h11, event)
            if result["disposition"] != "INCOMPLETE":
                return result
        except Exception as exc:
            return {"disposition": "REJECT", "exception": type(exc).__name__,
                    "error_status_hint": getattr(exc, "error_status_hint", None)}
    return result


def future(h11, prefix, suffix, cap):
    conn = h11.Connection(h11.SERVER, max_incomplete_event_size=cap)
    try:
        if prefix:
            conn.receive_data(prefix)
            before = categorise_event(h11, conn.next_event())
            if before["disposition"] != "INCOMPLETE":
                return before
        if suffix:
            conn.receive_data(suffix)
        return categorise_event(h11, conn.next_event())
    except Exception as exc:
        return {"disposition": "REJECT", "exception": type(exc).__name__,
                "error_status_hint": getattr(exc, "error_status_hint", None)}


def native_worker(root):
    root = Path(root).resolve()
    sys.path.insert(0, str(root))
    import h11
    hpath = Path(h11.__file__).resolve()
    if root not in hpath.parents:
        raise RuntimeError("UNPINNED_H11_MODULE_IMPORT:" + str(hpath))
    inputs = json.load(sys.stdin)
    outputs = []
    for c in inputs["cases"]:
        wire = bytes.fromhex(c["wire_hex"])
        outputs.append([run_wire(h11, wire, c["cap"], schedule)
                        for schedule in SCHEDULES])
    future_output = []
    for c in inputs["prefix_cases"]:
        prefix = bytes.fromhex(c["prefix_hex"])
        future_output.append([future(h11, prefix, bytes.fromhex(s), c["cap"])
                              for s in inputs["suffixes"]])
    print(json.dumps({"source": str(hpath),
                      "cases": outputs, "future": future_output},
                     separators=(",", ":")))


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def native_from_source(root, inputs, sha, outfile):
    subprocess.run(["git", "-C", str(root), "checkout", "--quiet", "--detach", sha],
                   check=True)
    actual = git(root, "rev-parse", "HEAD")
    if actual != sha:
        raise RuntimeError("SOURCE_REVISION_MISMATCH")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(root).resolve())
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--native-worker",
         str(Path(root).resolve())], input=json.dumps(inputs),
        text=True, capture_output=True, env=env, timeout=120)
    if result.returncode != 0:
        raise RuntimeError("NATIVE_EXECUTION_FAILED_" + sha[:10] +
                           " STDOUT=" + result.stdout[-1500:] +
                           " STDERR=" + result.stderr[-1500:])
    output = json.loads(result.stdout)
    if len(output["cases"]) != len(inputs["cases"]) or \
            len(output["future"]) != len(inputs["prefix_cases"]):
        raise RuntimeError("NATIVE_OUTPUT_INCOMPLETE")
    Path(outfile).write_text(json.dumps(output, sort_keys=True))
    return output


def stable(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"))


def minimal_basis(vectors, labels):
    # Exhaustively search all subsets, not greedy: small fixed finite language.
    full = list(dict.fromkeys(tuple(v) for v in vectors))
    n = len(labels)
    for k in range(n+1):
        for subset in itertools.combinations(range(n), k):
            projection = {tuple(v[i] for i in subset) for v in full}
            if len(projection) == len(full):
                return {"names": [labels[i] for i in subset],
                        "size": len(subset), "classes": len(full),
                        "total": len(vectors)}
    raise AssertionError("BASIS_NOT_FOUND")


def quotient(results, mode):
    vectors = [[stable(v) for v in row] for row in results]
    labels = list(SCHEDULES if mode == "transport" else range(len(SUFFIXES)))
    if mode != "transport":
        labels = [f"suffix:{s.hex()}" for s in SUFFIXES]
    counts = collections.Counter(tuple(v) for v in vectors)
    basis = minimal_basis(vectors, labels)
    basis["max_group"] = max(counts.values(), default=0)
    basis["erased_representations"] = len(vectors) - basis["classes"]
    return basis


def field_atoms(test):
    attrs = set()
    for node in ast.walk(test):
        if isinstance(node, ast.Attribute):
            try:
                value = ast.unparse(node)
                attrs.add(value)
            except Exception:
                pass
        elif isinstance(node, ast.Name):
            attrs.add(node.id)
    return sorted(attrs)[:30]


def source_guard_projection(root, before, after):
    before_head = git(root, "rev-parse", "HEAD")
    changed = git(root, "diff", "--name-only", before, after).splitlines()
    changed = [p for p in changed if p.startswith("h11/") and p.endswith(".py")
               and "/tests/" not in p]
    info = []
    for path in changed:
        def index(rev):
            text = subprocess.check_output(
                ["git", "-C", str(root), "show", rev+":"+path], text=True)
            tree = ast.parse(text, filename=path)
            functions = {}
            def visit(n, name=""):
                for child in ast.iter_child_nodes(n):
                    if isinstance(child, (ast.ClassDef, ast.FunctionDef,
                                          ast.AsyncFunctionDef)):
                        fullname = name+"."+child.name if name else child.name
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            functions[fullname] = child
                        visit(child, fullname)
            visit(tree)
            return text, functions
        try:
            oldsrc, old = index(before)
            newsrc, new = index(after)
        except (subprocess.CalledProcessError, SyntaxError):
            continue
        for symbol, node in new.items():
            older = old.get(symbol)
            if older is not None and ast.dump(node, include_attributes=False) == \
                    ast.dump(older, include_attributes=False):
                continue
            guards = []
            for expr in ast.walk(node):
                if isinstance(expr, (ast.If, ast.While, ast.IfExp, ast.Assert)):
                    condition = expr.test if hasattr(expr, "test") else None
                    if condition is not None:
                        guards.append({"line": getattr(expr, "lineno", 0),
                                       "expr": ast.unparse(condition)[:250],
                                       "read_atoms": field_atoms(condition)})
            info.append({
                "file": path, "symbol": symbol,
                "source_sha256_head": digest(newsrc),
                "source_sha256_base": digest(oldsrc),
                "guards": guards[:35]
            })
    return {"files": changed, "changed_functions": info,
            "boundary": "AST_GUARD_CANDIDATES_NOT_SEMANTIC_COMPLETENESS"}


def run_experiment(root, output_dir):
    root = Path(root).resolve()
    target = Path(output_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)
    inputs = build_cases()
    (target/"finite_observation_grammar.json").write_text(
        json.dumps(inputs, indent=2))
    results = {}
    for label, sha in SOURCES.items():
        # Fetch was already pinned during the GitHub Actions workflow.
        results[label] = native_from_source(root, inputs, sha,
                                            target/f"native_{label}.json")
    base = results["base"]
    witnesses = {}
    source_stats = {}
    for label in ("206", "198", "207"):
        other = results[label]
        deviations = []
        semantic_deviations = []
        for i, c in enumerate(inputs["cases"]):
            for j, schedule in enumerate(SCHEDULES):
                before = base["cases"][i][j]
                after = other["cases"][i][j]
                if stable(before) != stable(after):
                    deviations.append((c["nbytes"], c["id"], j, i))
                    if before["disposition"] != after["disposition"]:
                        semantic_deviations.append((c["nbytes"], c["id"], j, i))
        deviations.sort()
        semantic_deviations.sort()
        choice = (semantic_deviations or deviations)
        if choice:
            _, _, j, i = choice[0]
            c = inputs["cases"][i]
            witness = {"input": c, "schedule": SCHEDULES[j],
                       "base": base["cases"][i][j],
                       "head": other["cases"][i][j],
                       "minimization": "minimum byte count within frozen finite grammar",
                       "source_pin_base": SOURCES["base"],
                       "source_pin_head": SOURCES[label]}
            # Re-run this witness independently, with both source heads.
            tiny = {"cases": [c], "prefix_cases": [],
                    "suffixes": inputs["suffixes"]}
            old_again = native_from_source(root, tiny, SOURCES["base"],
                                           target/f"witness_{label}_base.json")
            new_again = native_from_source(root, tiny, SOURCES[label],
                                           target/f"witness_{label}_head.json")
            if old_again["cases"][0][j] != witness["base"] or \
                    new_again["cases"][0][j] != witness["head"]:
                raise RuntimeError("WITNESS_INDEPENDENT_REPLAY_MISMATCH")
        else:
            witness = None
        witnesses[label] = {
            "exact_event_differences": len(deviations),
            "disposition_differences": len(semantic_deviations),
            "witness": witness,
            "status": ("BOUNDED_NATIVE_SEPARATOR" if witness is not None
                       else "NO_SEPARATOR_IN_FROZEN_GRAMMAR")
        }
        source_stats[label] = source_guard_projection(root, SOURCES["base"],
                                                       SOURCES[label])
        # Two invariance controls that must remain true in baseline and both
        # source variants: changing transport fragmentation cannot change the
        # parsed event for ordinary small traffic, when no cap is crossed.
    controls = []
    for label, native in results.items():
        valid = [i for i, c in enumerate(inputs["cases"]) if
                 c["kind"] == "ordinary" and c["size"] in (0, 1) and
                 c["cap"] == 256]
        for i in valid:
            row = native["cases"][i]
            if not all(stable(v) == stable(row[0]) for v in row):
                raise RuntimeError("SMALL_MESSAGE_TRANSPORT_INVARIANCE_FAIL_"+label)
            if row[0]["disposition"] != "ACCEPT":
                raise RuntimeError("SMALL_MESSAGE_WAS_NOT_ACCEPTED_"+label)
        controls.append({"rev": label, "ordinary_inputs": len(valid),
                         "chunk_invariance": "PASS"})
    # Observational state quotient and mathematically minimum distinguishing
    # probe basis relative to declared finite grammar and fixed suffixes.
    quotients = {}
    for label, native in results.items():
        quotients[label] = {
            "transport": quotient(native["cases"], "transport"),
            "future_prefix": quotient(native["future"], "future")
        }
    # Existing PR authors described expected behavior in titles/bodies before
    # freezing: don't manufacture blind discovery or human superiority.
    summary = {
        "schema": "metalogic.mathgraph.jpl-consequence-quotient.h11.v1",
        "experiment": "JPL-style consequence preserving observational compression",
        "sources": SOURCES, "target_repository": "python-hyper/h11",
        "frozen_protocol": "research/mathgraph_minimal_quotient/FROZEN_PROTOCOL.md",
        "inputs": {"wire_cap_pairs": len(inputs["cases"]),
                   "transport_schedules": list(SCHEDULES),
                   "prefix_states_sampled": len(inputs["prefix_cases"]),
                   "suffix_experiments": len(SUFFIXES)},
        "source_guard_projection": source_stats,
        "quotients": quotients, "witnesses": witnesses,
        "controls": controls,
        "authority": "ADVISORY_ONLY",
        "capability": "FINITE_NATIVE_SOURCE_BOUND_OBSERVATIONAL_QUOTIENT",
        "not_claimed": [
            "complete HTTP specification or all possible wire input semantics",
            "automatic derivation of source model from arbitrary code",
            "autonomous invention of probe grammar or proof-to-code bridge",
            "first discovery of PR author-described issues",
            "better decision than equally informed expert human baseline",
            "production MathGraph Check generalization or external adoption"
        ]
    }
    (target/"summary.json").write_text(json.dumps(summary, indent=2))
    narrative = [
        "# Exact h11 native observational quotient",
        "",
        "Protocol committed before patch inspection. All witnesses against",
        "the original source revisions, no upstream code modification.",
        "",
        f"Total finite (wire,cap) pairs: {len(inputs['cases'])}.",
        f"Chunk schedules: {len(SCHEDULES)}. Sampled prefix states: "
        f"{len(inputs['prefix_cases'])}.",
        "",
    ]
    for label in ("206", "198", "207"):
        w = witnesses[label]
        q = quotients[label]
        narrative += [
            f"## Upstream PR #{label}",
            f"- Exact output differences: {w['exact_event_differences']}",
            f"- Decision differences: {w['disposition_differences']}",
            f"- Status: {w['status']}",
            f"- Observable future prefix classes: {q['future_prefix']['classes']} "
            f"of {q['future_prefix']['total']} source prefixes",
            f"- Minimum separating suffixes within frozen language: "
            f"{q['future_prefix']['names']}",
        ]
        if w["witness"]:
            v = w["witness"]
            narrative += [
                f"- Minimum witness in grammar: {v['input']['id']} "
                f"({v['input']['nbytes']} bytes), schedule={v['schedule']}",
                f"- Before: {stable(v['base'])}",
                f"- After: {stable(v['head'])}",
                "- Independently replayed on both exact source SHAs."
            ]
        narrative += [""]
    narrative += [
        "## Limit",
        "Finite-horizon observational equivalence, not full program-state",
        "bisimulation or global semantic correctness. Candidate Python AST",
        "guard fields are not a proved complete source abstraction.",
        "The PR authors' descriptions already reveal their proposed issues.",
        "No measured human reviewer superiority or new-method genesis."
    ]
    (target/"REPORT.md").write_text("\n".join(narrative)+"\n")
    assert witnesses["206"]["disposition_differences"] > 0, \
        "PRIMARY_NATIVE_SEMANTIC_SEPARATOR_NOT_ESTABLISHED"
    assert witnesses["198"]["exact_event_differences"] > 0, \
        "TRANSFER_A_NATIVE_EVENT_SEPARATOR_NOT_ESTABLISHED"
    print("MATHGRAPH_CONSEQUENCE_QUOTIENT_BOUNDARY " +
          json.dumps({"counts": summary["inputs"],
                      "findings": {k: {z: v[z] for z in ("exact_event_differences",
                                                        "disposition_differences",
                                                        "status")}
                                   for k, v in witnesses.items()},
                      "future_classes": {k: quotients[k]["future_prefix"]["classes"]
                                         for k in quotients}}))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--native-worker":
        native_worker(sys.argv[2])
    elif len(sys.argv) == 3:
        run_experiment(sys.argv[1], sys.argv[2])
    else:
        raise SystemExit("usage: h11_quotient.py [root outputdir | --native-worker root]")
