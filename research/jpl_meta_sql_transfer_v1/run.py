#!/usr/bin/env python3
"""JPL meta-correspondence transfer to an unmodified external SQL optimizer.

Scope: finite observed SQL query/database universe, NOT universal SQL equivalence.
Source transformer: pinned upstream SQLGlot (no per-query expected outputs).
Independent native oracle: CPython sqlite3; first counterexamples preserved.
Reclosure: byte-identical FLASH V13 code at the pinned prior source revision.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import os
import random
import sqlite3
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = Path(os.environ.get("GITHUB_WORKSPACE", Path.cwd()))
SOURCE = WORKSPACE / "jpl-target-sqlglot"
FLASH = WORKSPACE / "flash-v13-source" / "research" / "flash_v13"

def dump(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def hash_obj(x):
    return hashlib.sha256(dump(x).encode()).hexdigest()

def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()

def check_pin(protocol):
    target = protocol["external_source"]
    assert git(SOURCE, "rev-parse", "HEAD") == target["commit"], "UPSTREAM_SOURCE_CHANGED"
    assert not git(SOURCE, "status", "--porcelain"), "UPSTREAM_WORKTREE_DIRTY"
    assert git(FLASH.parents[1], "rev-parse", "HEAD") == protocol["flash_source"]["commit"], "FLASH_SOURCE_CHANGED"
    assert not git(FLASH.parents[1], "status", "--porcelain"), "FLASH_WORKTREE_DIRTY"
    import_hash = git(SOURCE, "hash-object", "sqlglot/optimizer/optimizer.py")
    assert import_hash == "fb8d216967c68d8e65db4455bdca0c8419cd9efc", "SOURCE_BLOB_CHANGED"
    return import_hash

def worlds_of(protocol):
    rows = [tuple(r) for r in protocol["basis_rows"]]
    urows = [(), *((r,) for r in rows)]
    worlds = []
    for n in range(3):
        for t in itertools.product(rows, repeat=n):
            for u in urows:
                worlds.append({"t": [list(x) for x in t], "u": [list(x) for x in u]})
    rng = random.Random(protocol["random_seed"])
    domain = protocol["row_domain"]
    for _ in range(protocol["random_worlds"]):
        sample = {}
        for table in ("t", "u"):
            sample[table] = [
                [rng.choice(domain) for _ in ("a", "b", "c")]
                for _ in range(rng.randint(0, protocol["random_max_rows"]))
            ]
        worlds.append(sample)
    assert len(worlds) == 1301, "SOURCE_WORLD_SIZE_CHANGED"
    return worlds

def connection():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE t (a INTEGER,b INTEGER,c INTEGER)")
    db.execute("CREATE TABLE u (a INTEGER,b INTEGER,c INTEGER)")
    return db

def load_world(db, world):
    db.execute("DELETE FROM t")
    db.execute("DELETE FROM u")
    for table in ("t", "u"):
        db.executemany("INSERT INTO " + table + " (a,b,c) VALUES (?,?,?)", world[table])

def observe(db, query, ordered):
    try:
        cur = db.execute(query)
        if cur.description is None:
            return {"state": "UNSUPPORTED_NO_COLUMNS"}
        columns = [column[0] for column in cur.description]
        rows = [list(row) for row in cur.fetchall()]
        if not ordered:
            rows.sort(key=dump)
        return {"state": "NATIVE_OBSERVED", "columns": columns, "rows": rows}
    except sqlite3.Error as exc:
        return {"state": "UNSUPPORTED_SQLITE", "type": type(exc).__name__,
                "reason": str(exc)[:200]}

def optimizer_output(sql, schema):
    from sqlglot.optimizer import optimize
    return optimize(sql, schema=schema, dialect="sqlite").sql(dialect="sqlite")

def classify_case(db, sql, optimized, worlds):
    ordered = "ORDER BY" in sql.upper()
    signatures = []
    unsupported = None
    witness = None
    for i, world in enumerate(worlds):
        load_world(db, world)
        left = observe(db, sql, ordered)
        right = observe(db, optimized, ordered)
        signatures.append(hash_obj(left))
        if left["state"] != "NATIVE_OBSERVED" or right["state"] != "NATIVE_OBSERVED":
            if unsupported is None:
                unsupported = {"world_index": i, "original": left, "transformed": right}
        elif left != right and witness is None:
            witness = {"world_index": i, "database": world, "original": left, "transformed": right}
    status = ("UNKNOWN_UNSUPPORTED" if unsupported is not None else
              "REFUTED_FINITE_WITNESS" if witness is not None else
              "WARRANTED_BOUNDED_FINITE_EQUIVALENCE")
    return {"status": status, "first_witness": witness, "first_unsupported": unsupported,
            "original_observation_hashes": signatures, "native_pair_executions": len(worlds) * 2}

def world_projection(world, keys):
    projected = []
    for table in ("t", "u"):
        cols = [j for j, k in enumerate(("a", "b", "c")) if table + "." + k in keys]
        projected.append([list(row[j] for j in cols) for row in world[table]])
    return projected

def minimal_sufficient_basis(worlds, observations):
    """Exhaustively choose a finite-universe minimum observable input projection.

    Two input worlds with the same projected rows must have identical FULL
    column-header and ordered/bag-output signatures. Only the frozen 1301
    worlds are quantified over, not arbitrary SQLite database states.
    """
    keys = [t + "." + k for t in ("t", "u") for k in ("a", "b", "c")]
    qualifying = []
    for size in range(len(keys) + 1):
        for candidate in itertools.combinations(keys, size):
            by_projection = {}
            possible = True
            for world, signature in zip(worlds, observations):
                k = hash_obj(world_projection(world, set(candidate)))
                previous = by_projection.setdefault(k, signature)
                if previous != signature:
                    possible = False
                    break
            if possible:
                qualifying.append(candidate)
        if qualifying:
            break
    assert qualifying, "FULL_SOURCE_PROJECTION_MUST_SUFFICE"
    basis = list(qualifying[0])
    # Independently check the chosen basis; all proper one-deletion subsets must fail.
    def sufficient(c):
        classes = defaultdict(set)
        for world, signature in zip(worlds, observations):
            classes[hash_obj(world_projection(world, set(c)))].add(signature)
        return all(len(v) == 1 for v in classes.values())
    assert sufficient(basis)
    for i in range(len(basis)):
        assert not sufficient(basis[:i] + basis[i+1:]), "NONMINIMAL_REPRESENTATION"
    return {"columns": basis, "cardinality": len(basis),
            "tied_minimal_bases": len(qualifying), "worlds": len(worlds)}

def mutant_cases(queries):
    q = {x["id"]: x["sql"] for x in queries}
    mutations = [
        ("predicate", q["q07"], q["q07"].replace("a = 1", "a = 0", 1)),
        ("null_handling", q["q11"], q["q11"].replace("IS NULL", "IS NOT NULL", 1)),
        ("bag_distinct", q["q08"], q["q08"].replace("SELECT DISTINCT", "SELECT", 1)),
        ("output_header", q["q01"], q["q01"].replace("AS result", "AS changed", 1)),
        ("sort_direction", q["q10"], q["q10"].replace("b ASC", "b DESC", 1)),
        ("left_join", q["q03"], q["q03"].replace("LEFT JOIN", "INNER JOIN", 1))
    ]
    for name, base, bad in mutations:
        assert base != bad, "INEFFECTIVE_NEGATIVE_MUTATION:" + name
    return mutations

def test_mutants(db, worlds, frozen):
    outcomes = []
    for name, sql, mutation in mutant_cases(frozen["query_cases"]):
        matched = True
        first = None
        for i, world in enumerate(worlds):
            load_world(db, world)
            ordered = "ORDER BY" in sql.upper()
            a, b = observe(db, sql, ordered), observe(db, mutation, ordered)
            assert a["state"] == b["state"] == "NATIVE_OBSERVED", (name, a, b)
            if a != b:
                matched = False
                first = {"world_index": i, "database": world, "actual": a, "mutant": b}
                break
        outcomes.append({"kind": name, "caught": not matched, "counterexample": first})
    assert len(outcomes) == len(frozen["controls"]["mutations"]) == 6
    assert all(x["caught"] for x in outcomes), "MUTANT_NOT_DETECTED"
    return outcomes

def authenticated_local_intake(record, frozen, world_digest):
    # A source identity binding, not a cryptographic publisher authentication.
    if record["upstream_sha"] != frozen["external_source"]["commit"]:
        return "UNKNOWN_SOURCE_REVISION"
    if record["finite_world_sha256"] != world_digest:
        return "UNKNOWN_WORLD_SCOPE"
    if record["authority"] != "NATIVE_SQLITE_EVALUATION":
        return "UNKNOWN_UNQUALIFIED_EVIDENCE"
    if record["status"] not in ("WARRANTED_BOUNDED_FINITE_EQUIVALENCE",
                                "REFUTED_FINITE_WITNESS"):
        return "UNKNOWN_UNSUPPORTED_OR_INCOMPLETE"
    return "ACCEPT_SCOPED_OBSERVATION"

def reclose(records, frozen, world_digest):
    """Integrate actual native evidence with UNCHANGED prior FLASH engine."""
    sys.path.insert(0, str(FLASH))
    from flash_engine import RecloseEngine, EventRejected
    from reference_oracle import FullReference
    accepted = [r for r in records if authenticated_local_intake(r, frozen, world_digest) ==
                "ACCEPT_SCOPED_OBSERVATION"]
    source = "source:sqlglot"
    world = "worlds:finite"
    env = "runtime:sqlite"
    facts = ["native:" + r["id"] for r in accepted]
    rules = []
    frontiers = []
    for r in records:
        fact = "native:" + r["id"]
        conclusion = "warrant:" + r["id"] if r["status"].startswith("WARRANTED") else (
                     "refuted:" + r["id"] if r["status"].startswith("REFUTED") else None)
        if conclusion:
            rules.append({"id": "derived_" + r["id"], "when": [source, world, env, fact],
                          "then": conclusion})
        frontiers.append({"id": "review_" + r["id"], "budget": 10, "options": [
            {"id": "recheck", "when": [], "unless": [],
             "cost": 9},
            {"id": "use_bounded_warrant", "when": ["warrant:" + r["id"]],
             "unless": [], "cost": 1},
            {"id": "inspect_finite_witness", "when": ["refuted:" + r["id"]],
             "unless": [], "cost": 0}
        ]})
    fixture = {"version": "flash-v13-20261012",
               "scope": "source_native_sqlite_1301_worlds_only",
               "base_facts": [source, world, env],
               "source_authorities": {"sqlglot": frozen["external_source"]["commit"],
                                      "world_sha256": world_digest},
               "allowed_events": {"promote": facts, "revoke": facts},
               "rules": rules, "frontiers": frontiers,
               "events": [], "restart_after_event_index": 0, "adversarial_tests": []}
    engine, baseline = RecloseEngine(fixture), FullReference(fixture)
    assert engine.state() == baseline.current
    for fact in facts:
        ev = {"kind": "promote", "fact": fact, "authority": "synthetic_event"}
        engine.apply(ev)
        baseline.apply(ev)
        assert engine.state() == baseline.current, fact
    initial = engine.state()
    assert all(("warrant:" + r["id"] in engine.active) ==
               (r["status"] == "WARRANTED_BOUNDED_FINITE_EQUIVALENCE") for r in records)
    assert all(("refuted:" + r["id"] in engine.active) ==
               (r["status"] == "REFUTED_FINITE_WITNESS") for r in records)
    assert "native:" + records[0]["id"] in engine.base
    target = "native:" + records[0]["id"]
    before = set(engine.active)
    revoke = {"kind": "revoke", "fact": target, "authority": "synthetic_revoker"}
    outcome = engine.apply(revoke)
    baseline.apply(revoke)
    assert engine.state() == baseline.current
    assert target not in engine.base
    if "warrant:" + records[0]["id"] in before:
        assert "warrant:" + records[0]["id"] not in engine.active
    for other in records[1:]:
        derived = "warrant:" + other["id"] if other["status"].startswith("WARRANTED") else "refuted:" + other["id"]
        if other["status"].startswith(("WARRANTED", "REFUTED")):
            assert (derived in engine.active) == (derived in before)
    snap = engine.snapshot()
    restored = RecloseEngine.restore(fixture, json.loads(dump(snap)))
    assert restored.state() == baseline.current
    corrupted = json.loads(dump(snap))
    corrupted["state"]["base"].append("FORGED_WARRANT")
    try:
        RecloseEngine.restore(fixture, corrupted)
        raise AssertionError("CORRUPTED_RESTART_ACCEPTED")
    except EventRejected:
        pass
    for bad in [
        {"kind": "promote", "fact": target, "authority": "forged-source"},
        {"kind": "promote", "fact": "native:unseen", "authority": "synthetic_event"}
    ]:
        before_bad = restored.snapshot()
        try:
            restored.apply(bad)
            raise AssertionError("FORGED_EVENT_ACCEPTED")
        except EventRejected:
            pass
        assert restored.snapshot() == before_bad
    promote = {"kind": "promote", "fact": target, "authority": "synthetic_event"}
    restored.apply(promote)
    baseline.apply(promote)
    assert restored.state() == baseline.current == initial
    wrong = dict(accepted[0], upstream_sha="0" * 40)
    forged = dict(accepted[0], authority="SELF_ASSERTED")
    assert authenticated_local_intake(wrong, frozen, world_digest) == "UNKNOWN_SOURCE_REVISION"
    assert authenticated_local_intake(forged, frozen, world_digest) == "UNKNOWN_UNQUALIFIED_EVIDENCE"
    return {"status": "PASS_NATIVE_SOURCE_TO_FLASH_RECLOSURE",
            "accepted_native_receipts": len(accepted),
            "source_evidence_ids": [r["id"] for r in accepted],
            "evented_reclose_equals_independent_batch": True,
            "selective_retraction": {"fact": target, "dirty": outcome["dirty_facts"],
                                     "changed": outcome["changed_facts"],
                                     "unrelated_conclusions_unchanged": True},
            "tampered_restart_rejected": True, "forged_event_rejected": True,
            "wrong_source_and_fake_evidence_rejected": True,
            "restarted_and_restored": True, "incremental_rule_evaluations": restored.metrics["rule_evaluations"],
            "full_batch_rule_evaluations": baseline.checks,
            "FLASH_original_source_sha": frozen["flash_source"]["commit"],
            "epistemic_limit": "FLASH V13 uses a simulated event authority; controlled local revocation only. The native SQL evidence is original GitHub Actions source-pinned output."}

def main():
    start = time.perf_counter()
    frozen = json.loads((HERE / "FROZEN_PROTOCOL.json").read_text())
    protocol_sha = hashlib.sha256((HERE / "FROZEN_PROTOCOL.json").read_bytes()).hexdigest()
    upstream_blob = check_pin(frozen)
    sys.path.insert(0, str(SOURCE))
    import sqlglot
    db = connection()
    worlds = worlds_of(frozen)
    world_digest = hash_obj(worlds)
    results = []
    schema = frozen["sqlite_schema"]
    for target in frozen["query_cases"]:
        sql = target["sql"]
        try:
            optimized = optimizer_output(sql, schema)
            assessment = classify_case(db, sql, optimized, worlds)
        except Exception as exc:
            optimized = None
            assessment = {"status": "UNKNOWN_OPTIMIZER_OR_HOST_FAILURE", "error": repr(exc),
                          "first_witness": None, "first_unsupported": None,
                          "original_observation_hashes": [], "native_pair_executions": 0}
        basis = (minimal_sufficient_basis(worlds, assessment["original_observation_hashes"])
                 if assessment["original_observation_hashes"] and
                 assessment["first_unsupported"] is None else None)
        results.append({"id": target["id"], "original_sql": sql, "optimized_sql": optimized,
                        "optimized_changed": optimized is not None and sql != optimized,
                        "upstream_sha": frozen["external_source"]["commit"],
                        "source_blob_sha": upstream_blob,
                        "finite_world_sha256": world_digest,
                        "authority": "NATIVE_SQLITE_EVALUATION",
                        "status": assessment["status"],
                        "counterexample": assessment["first_witness"],
                        "unsupported": assessment["first_unsupported"],
                        "minimal_observation_input": basis,
                        "native_pair_executions": assessment["native_pair_executions"]})
    # Identical-information native direct evaluation is a strong comparator.
    # It sees the same query pair and native database worlds and ties semantics.
    controls = test_mutants(db, worlds, frozen)
    graph = reclose(results, frozen, world_digest)
    counts = {state: sum(r["status"] == state for r in results)
              for state in sorted(set(r["status"] for r in results))}
    # Syntactic diff is intentionally a weak baseline and not the competitive one.
    changed_count = sum(bool(r["optimized_changed"]) for r in results)
    report = {
        "status": "PASS_BOUNDED_NATIVE_META_TRANSFER" if counts.get("WARRANTED_BOUNDED_FINITE_EQUIVALENCE", 0) >= 1
                  else "UNKNOWN_NO_QUALIFIED_NATIVE_TRANSFORM",
        "protocol_sha256": protocol_sha,
        "external_original_git_sha": frozen["external_source"]["commit"],
        "optimizer_source_git_blob": upstream_blob,
        "sqlglot_import_path": str(Path(sqlglot.__file__).resolve()),
        "sqlite_version": sqlite3.sqlite_version,
        "finite_worlds": len(worlds),
        "finite_world_sha256": world_digest,
        "source_query_cases": len(results),
        "state_counts": counts,
        "text_changed_count": changed_count,
        "native_pair_executions": sum(r["native_pair_executions"] for r in results),
        "mutants": [{"kind": r["kind"], "caught": r["caught"],
                     "first_world_index": r["counterexample"]["world_index"] if r["counterexample"] else None}
                    for r in controls],
        "native_strong_baseline": "TIE_BY_CONSTRUCTION: independent SQLite same inputs/outputs; no superiority established",
        "graph": graph,
        "wall_seconds": round(time.perf_counter() - start, 3),
        "epistemic": {"warranted": "Finite-source/native observations in frozen database-world set, scope-local minimum input projections and controlled FLASH reclosure.",
                      "not_warranted": "Universal SQL equivalence, lossless optimizer semantics on other inputs, arbitrary source-to-requirement binding, independently authored new verifier grammar, industrial economics, end-user decision superiority, outside-user adoption.",
                      "source_domain_adapter": "One predeclared SQLite dialect/native execution adapter; no handwritten expected optimizer results or per-query semantic correspondence.",
                      "source_freshness": "Fixed immutable commit; no live latest-head assurance.",
                      "action_authorization": "NONE"}
    }
    dest = HERE / "out"
    dest.mkdir(exist_ok=True)
    (dest / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (dest / "records.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    (dest / "negative_controls.json").write_text(json.dumps(controls, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "finite_worlds": len(worlds),
                      "native_pair_executions": report["native_pair_executions"],
                      "states": counts, "mutants_caught": sum(x["caught"] for x in controls),
                      "flash_status": graph["status"],
                      "wall_seconds": report["wall_seconds"]}, indent=2))
    assert all(x["caught"] for x in controls)
    assert report["native_pair_executions"] > 0
    assert graph["evented_reclose_equals_independent_batch"]
    assert report["status"] == "PASS_BOUNDED_NATIVE_META_TRANSFER"

if __name__ == "__main__":
    main()
