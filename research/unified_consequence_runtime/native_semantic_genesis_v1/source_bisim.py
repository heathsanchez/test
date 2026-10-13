#!/usr/bin/env python3
"""Discover finite-support bisimulation from genuine upstream CSLib source syntax.

This source-to-native proof compiler operates on a specified category of Lean
inductive LTS transitions over Nat states; no source-specific proof script
is embedded. It returns UNKNOWN rather than interpreting unsupported grammar.
The corpus, exact source identities and scientific claim limits are separately
frozen before this source file was written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path


def canonical(obj):
    return json.dumps(obj, sort_keys=True, indent=2) + "\n"


def checked_source(repo, spec, upstream):
    if subprocess.check_output(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
    ).strip() != upstream["commit"]:
        raise ValueError("CSLIB_UPSTREAM_COMMIT_MISMATCH")
    path = repo / spec["file"]
    sha = subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()
    if sha != spec["blob_sha"]:
        raise ValueError("EXACT_SOURCE_BLOB_MISMATCH:" + spec["file"])
    return path.read_text(encoding="utf-8")


def extract_edges(source_text, spec):
    name = spec["transition"]
    expr = (
        r"^\s*(?:private\s+)?inductive\s+" + re.escape(name)
        + r"\s*:\s*ℕ\s*→\s*(ℕ|Char)\s*→\s*ℕ\s*→\s*Prop\s+where\s*$"
    )
    matches = [(i, re.fullmatch(expr, line)) for i, line
               in enumerate(source_text.splitlines())]
    found = [(i, hit) for i, hit in matches if hit]
    if len(found) != 1:
        raise ValueError("UNKNOWN_UNSUPPORTED_SOURCE_FORM:" + name)
    line_number, header = found[0]
    if header.group(1) != ("ℕ" if spec["source_label"] == "Nat" else "Char"):
        raise ValueError("NATIVE_LABEL_TYPE_MISMATCH")
    edge_re = re.compile(
        r"^\s*\|\s*(\w+)\s*:\s*" + re.escape(name)
        + r"\s+(\d+)\s+(\d+|'[^']+')\s+(\d+)\s*$"
    )
    edges = []
    for line in source_text.splitlines()[line_number + 1:]:
        if not line.strip() or line.strip().startswith("--"):
            continue
        m = edge_re.fullmatch(line)
        if m:
            cname, a, label, b = m.groups()
            if spec["source_label"] == "Nat" and not label.isdigit():
                raise ValueError("NATIVE_LABEL_VALUE_MISMATCH")
            if spec["source_label"] == "Char" and not (
                len(label) >= 3 and label[0] == label[-1] == "'"):
                raise ValueError("NATIVE_LABEL_VALUE_MISMATCH")
            edges.append((int(a), label, int(b), cname))
            continue
        break
    if len(edges) < 2:
        raise ValueError("UNKNOWN_NONFINITE_OR_UNSUPPORTED_TRANSITION_GRAMMAR")
    if len({c for *_, c in edges}) != len(edges):
        raise ValueError("DUPLICATE_CONSTRUCTOR_ID")
    return edges


def pair_fixed_point(states, edges):
    """Reference A: greatest forward-and-backward simulation relation."""
    links = defaultdict(set)
    for a, lbl, b, _ in edges:
        links[a, lbl].add(b)
    labels = sorted(set(l for _, l, _, _ in edges))
    pairs = {(a, b) for a in states for b in states}
    histories = []
    while True:
        nxt = set()
        for a, b in pairs:
            if all(
                all(any((x, y) in pairs for y in links[b, l]) for x in links[a, l])
                and all(any((x, y) in pairs for x in links[a, l]) for y in links[b, l])
                for l in labels
            ):
                nxt.add((a, b))
        histories.append(len(nxt))
        if nxt == pairs:
            return nxt, histories
        pairs = nxt


def partition_reference(states, edges):
    """Reference B: partition refine by sets of successor blocks; no pair table."""
    labels = tuple(sorted({label for _, label, _, _ in edges}))
    successor = defaultdict(set)
    for a, label, b, _ in edges:
        successor[a, label].add(b)
    classes = [frozenset(states)]
    while True:
        block_of = {v: k for k, block in enumerate(classes) for v in block}
        groups = defaultdict(set)
        for v in states:
            signature = tuple(
                tuple(sorted({block_of[u] for u in successor[v, label]}))
                for label in labels
            )
            groups[signature].add(v)
        refined = sorted((frozenset(v) for v in groups.values()),
                         key=lambda group: tuple(sorted(group)))
        if sorted(classes, key=lambda g: tuple(sorted(g))) == refined:
            return {(u, v) for block in refined for u in block for v in block}, refined
        classes = refined


def witness_candidates(a, b, edges, relation):
    """A complete pair-specific branch plan, derived from source only."""
    result = []
    for src, label, after, _ in edges:
        if src != a:
            continue
        matches = sorted(
            (other, f"p_{after}_{other}")
            for start, ll, other, _ in edges
            if start == b and ll == label and (after, other) in relation
        )
        if not matches:
            raise AssertionError("SOURCE_FIXED_POINT_WITNESS_MISSING")
        result.append((src, label, after, matches[0][0], matches[0][1]))
    return result


def emit_bisimulation(spec, edges, relation):
    """One syntax-driven proof generator for both upstream transition grammars."""
    sid = spec["label"].replace("-", "_")
    relname = f"DerivedRel_{sid}"
    statement = f"DerivedBisim_{sid}"
    lines = [
        f"import {spec['import']}",
        "",
        "namespace SourceDerived",
        "open Cslib",
        "",
        f"private inductive {relname} : ℕ → ℕ → Prop where"
    ]
    for a, b in sorted(relation):
        lines.append(f"  | p_{a}_{b} : {relname} {a} {b}")
    lines += [
        "",
        f"theorem {statement} :",
        f"    Cslib.LTS.IsBisimulation {spec['system']} {spec['system']} {relname} := by",
        "  intro s₁ s₂ hrel μ",
        "  cases hrel with",
    ]
    for a, b in sorted(relation):
        lines.extend([f"  | p_{a}_{b} =>", "    constructor"])
        for side in (0, 1):
            left, right = (a, b) if side == 0 else (b, a)
            lines.extend([
                "    · intro destination ht",
                f"      dsimp [{spec['system']}] at ht",
                "      cases ht"
            ])
            candidates = witness_candidates(left, right, edges, relation)
            if candidates:
                lines.append("      all_goals first")
                for _, _, after, match, _ in candidates:
                    related = f"{relname}.p_{after}_{match}" if side == 0 else (
                        f"{relname}.p_{match}_{after}")
                    lines.append(
                        f"        | exact ⟨({match} : ℕ), by constructor, {related}⟩")
    first = next(((a, b) for a, b in sorted(relation) if a != b), None)
    if first is None:
        raise ValueError("NO_NONTRIVIAL_NATIVE_OBSERVATION")
    a, b = first
    lines += [
        "",
        f"theorem DerivedWitness_{sid} : {relname} {a} {b} := by",
        f"  exact {relname}.p_{a}_{b}",
    ]
    active = {x for e in edges for x in (e[0], e[2])}
    inert = next(x for x in range(max(active) + 2) if x not in active)
    src, label, dst, _ = next(e for e in edges if e[0] in active)
    lines += [
        "",
        f"theorem DerivedRefutation_{sid} :",
        f"    ¬ Cslib.LTS.IsBisimulation {spec['system']} {spec['system']}",
        f"        (fun s t : ℕ => s = {src} ∧ t = {inert}) := by",
        "  intro h",
        f"  have source_step : ({spec['system']}).Tr {src} {label} {dst} := by",
        "    constructor",
        f"  obtain ⟨u, target_step, _⟩ := (h (by exact ⟨rfl, rfl⟩) {label}).1 {dst} source_step",
        f"  dsimp [{spec['system']}] at target_step",
        "  cases target_step",
        "",
        "end SourceDerived",
        "",
    ]
    return "\n".join(lines), {
        "selected_pair": [a, b],
        "refuted_pair": [src, inert],
        "relation_pairs": len(relation),
        "active_states": len(active),
        "input_constructor_count": len(edges),
        "labels": len({label for _, label, _, _ in edges}),
        "native_lean": "PENDING",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cslib", type=Path, required=True)
    ap.add_argument("--protocol", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    protocol = json.loads(args.protocol.read_text())
    if protocol["schema"] != "metalogic.native-source-induced-bisimulation-protocol.v1":
        raise ValueError("UNKNOWN_PROTOCOL")
    args.out.mkdir(parents=True, exist_ok=True)
    outputs = []
    for spec in protocol["sources"]:
        native = checked_source(args.cslib, spec, protocol["upstream"])
        edges = extract_edges(native, spec)
        states = sorted({s for a, _, b, _ in edges for s in (a, b)})
        bisim, rounds = pair_fixed_point(states, edges)
        independent, blocks = partition_reference(states, edges)
        if bisim != independent:
            raise AssertionError("INDEPENDENT_SOURCE_BISIMULATION_ORACLE_MISMATCH")
        assert bisim
        lean, metadata = emit_bisimulation(spec, edges, bisim)
        file = args.out / (spec["label"] + ".lean")
        file.write_text(lean, encoding="utf-8")
        outputs.append({
            "source": spec["file"],
            "source_blob_sha": spec["blob_sha"],
            "symbol": spec["transition"],
            "label": spec["label"],
            "native_file": file.name,
            "native_sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
            "reference": "INDEPENDENT_FIXED_POINT_AND_PARTITION_AGREE",
            "steps": rounds,
            "block_count": len(blocks),
            "native_proof": metadata,
        })
    for negative in protocol["unsupported"]:
        text = (args.cslib / negative["file"]).read_text()
        if negative["definition"] not in text:
            raise ValueError("UNSUPPORTED_NEGATIVE_SOURCE_DISAPPEARED")
        if "inductive " + negative["definition"] in text:
            raise ValueError("UNSUPPORTED_SOURCE_BECAME_CONSTRUCTOR_ENUM")
    report = {
        "schema": "metalogic.native-source-induced-bisimulation-report.v1",
        "source_commit": protocol["upstream"]["commit"],
        "exact_protocol_sha256": hashlib.sha256(args.protocol.read_bytes()).hexdigest(),
        "sources": outputs,
        "negative_infinite_support": "UNKNOWN_INFINITE_SUPPORT",
        "self_generated_general_method": "UNKNOWN",
        "source_distinct_new_open_theorem": "UNKNOWN",
        "scientific_L7": "UNKNOWN",
        "cost_advantage": "NOT_ESTABLISHED",
        "scope": "two real original CSLib inductive source grammars with finite active support",
    }
    (args.out / "report.json").write_text(canonical(report))
    print("EXTERNAL_SOURCE_METHOD_CANDIDATES=" + str(len(outputs)))
    for output in outputs:
        print(output["label"], output["native_proof"])


if __name__ == "__main__":
    main()
