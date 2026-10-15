"""Bounded native SQLite observation and control induction.

Research-only, disposable in-memory worlds. This is not arbitrary SQL synthesis,
production DB migration, model training or a verified external-agent harness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


VALID_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def ident(name: str) -> str:
    if not VALID_ID.fullmatch(name):
        raise ValueError("unsafe SQL identifier")
    return '"' + name + '"'


def sha_json(obj: object) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True)
class Schema:
    parent: str
    child: str
    parent_key: str
    child_fk: str
    extra: str
    key_type: str = "INTEGER"
    extra_type: str = "TEXT"

    def ddl(self) -> tuple[str, str]:
        if self.key_type not in {"INTEGER", "TEXT"} or self.extra_type not in {"INTEGER", "TEXT"}:
            raise ValueError("unsupported schema")
        p, c, pk, fk, ex = (ident(v) for v in (
            self.parent, self.child, self.parent_key, self.child_fk, self.extra
        ))
        parent = f"CREATE TABLE {p} ({pk} {self.key_type} PRIMARY KEY)"
        child = (f"CREATE TABLE {c} (rid INTEGER PRIMARY KEY, {fk} {self.key_type} "
                 f"NOT NULL REFERENCES {p}({pk}), {ex} {self.extra_type} NOT NULL)")
        return parent, child


DEV = Schema("inventory", "lineitem", "id", "inventory_id", "memo")


def future_schema(seed: str, index: int) -> Schema:
    digest = hashlib.sha256(f"{seed}:{index}:WORLD_COMPILER".encode()).hexdigest()
    tag = digest[:10]
    return Schema(f"p_{tag}", f"c_{tag}", f"pk_{tag}",
                  f"ref_{tag}", f"extra_{tag}",
                  "INTEGER" if index % 2 == 0 else "TEXT",
                  "TEXT" if (index // 2) % 2 == 0 else "INTEGER")


def world(schema: Schema, enabled: bool) -> sqlite3.Connection:
    db = sqlite3.connect(":memory:", isolation_level=None)
    for stmt in schema.ddl():
        db.execute(stmt)
    # SETUP AUTHORITY ONLY: learner gets a connection, never enabled.
    db.execute("PRAGMA foreign_keys=" + ("ON" if enabled else "OFF"))
    return db


def passive(db: sqlite3.Connection) -> dict:
    """The old observation interface excludes runtime mode properties."""
    schemas = db.execute(
        "SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    tables = {}
    for table, _ in schemas:
        t = ident(table)
        tables[table] = {
            "rows": db.execute(f"SELECT * FROM {t} ORDER BY rowid").fetchall(),
            "columns": db.execute(f"PRAGMA table_info({t})").fetchall(),
            "foreign_key_schema": db.execute(f"PRAGMA foreign_key_list({t})").fetchall(),
        }
    return {"schema": schemas, "tables": tables}


@dataclass(frozen=True)
class Probe:
    sql: str
    values: tuple[object, ...]
    table: str
    source: str


def candidate_probes(db: sqlite3.Connection) -> list[Probe]:
    """Derive a missing-parent insert from common native schema metadata.

    Scope: one-column FK, empty tables, one rollback-only insert, type-based
    values. No winning property name or hidden initial mode is passed in.
    """
    probes = []
    names = [r[0] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )]
    for table in names:
        fks = db.execute(f"PRAGMA foreign_key_list({ident(table)})").fetchall()
        columns = db.execute(f"PRAGMA table_info({ident(table)})").fetchall()
        for fk in fks:
            if fk[1] != 0 or sum(x[0] == fk[0] for x in fks) != 1:
                continue
            from_field = fk[3]
            from_def = next((col for col in columns if col[1] == from_field), None)
            if from_def is None:
                continue
            missing = ("world_compiler_nonexistent_parent" if "TEXT" in from_def[2].upper()
                       else 2147483647)
            supplied = []
            for cid, field, dtype, required, default, primary_key in columns:
                if field == from_field:
                    supplied.append((field, missing))
                elif primary_key and "INTEGER" in dtype.upper():
                    continue
                elif required and default is None:
                    supplied.append((field, "safe" if "TEXT" in dtype.upper() else 1))
            if not supplied:
                continue
            column_sql = ", ".join(ident(k) for k, _ in supplied)
            placeholders = ", ".join("?" for _ in supplied)
            sql = f"INSERT INTO {ident(table)} ({column_sql}) VALUES ({placeholders})"
            probes.append(Probe(sql, tuple(v for _, v in supplied), table,
                                "native sqlite foreign_key_list + table_info"))
    return probes


def observe(db: sqlite3.Connection, probe: Probe) -> bool:
    """True only for an IntegrityError, with exact rollback of trial insert."""
    if db.in_transaction:
        raise ValueError("probe requires transaction-free connection")
    before = passive(db)
    db.execute("SAVEPOINT world_compiler_probe")
    try:
        try:
            db.execute(probe.sql, probe.values)
            outcome = False
        except sqlite3.IntegrityError:
            outcome = True
        # OperationalError is not proof of enforcement (e.g. query_only).
    finally:
        db.execute("ROLLBACK TO world_compiler_probe")
        db.execute("RELEASE world_compiler_probe")
    if passive(db) != before:
        raise AssertionError("active observation mutated protected state")
    return outcome


def verify_native(db: sqlite3.Connection, schema: Schema) -> bool:
    """Separate SQLite oracle: valid insert works and invalid one fails.

    Never delegates verdict to the learner's candidate probe or its output.
    """
    if db.in_transaction:
        return False
    p, c, pk, fk, ex = (ident(v) for v in (
        schema.parent, schema.child, schema.parent_key,
        schema.child_fk, schema.extra))
    real_id = "exists" if schema.key_type == "TEXT" else 23
    nonexistent = "absent" if schema.key_type == "TEXT" else 34567
    extra_value = "ok" if schema.extra_type == "TEXT" else 7
    old = passive(db)
    try:
        db.execute("SAVEPOINT independent_verifier")
        db.execute(f"INSERT INTO {p}({pk}) VALUES (?)", (real_id,))
        db.execute(f"INSERT INTO {c}({fk},{ex}) VALUES (?,?)", (real_id, extra_value))
        rejected = False
        try:
            db.execute(f"INSERT INTO {c}({fk},{ex}) VALUES (?,?)", (nonexistent, extra_value))
        except sqlite3.IntegrityError:
            rejected = True
        return rejected
    except sqlite3.Error:
        return False
    finally:
        if db.in_transaction:
            db.execute("ROLLBACK TO independent_verifier")
            db.execute("RELEASE independent_verifier")
        assert passive(db) == old


def discover_probe(schema: Schema) -> tuple[Probe, dict]:
    a, b = world(schema, False), world(schema, True)
    try:
        if passive(a) != passive(b):
            raise AssertionError("old observations distinguish modes")
        candidates = candidate_probes(a)
        outcomes = [(c, observe(a, c), observe(b, c)) for c in candidates]
        winners = [p for p, u, s in outcomes if not u and s]
        if not winners:
            raise RuntimeError("UNKNOWN_NO_CONSEQUENTIAL_OBSERVATION")
        chosen = min(winners, key=lambda x: (len(x.sql), x.sql))
        return chosen, {
            "passive_indistinguishable": True,
            "probe_candidates": len(candidates),
            "winning_probes": len(winners),
            "unsafe_protected": observe(a, chosen),
            "safe_protected": observe(b, chosen),
            "rollback_exact": True,
        }
    finally:
        a.close()
        b.close()


def discover_intervention(schema: Schema, probe: Probe, max_candidates: int = 250) -> dict:
    source = world(schema, False)
    try:
        names = sorted({row[0] for row in source.execute("PRAGMA pragma_list")
                        if VALID_ID.fullmatch(row[0])})
    finally:
        source.close()
    programs = [f"PRAGMA {name}={switch}" for name in names
                for switch in ("OFF", "ON")]
    if len(programs) > max_candidates:
        raise RuntimeError("UNKNOWN_PRAGMA_ENUMERATION_EXCEEDS_FROZEN_BUDGET")
    if not programs:
        raise RuntimeError("UNKNOWN_NO_PERMITTED_INTERVENTION")
    winners = []
    attempted = 0
    for program in ["IDENTITY"] + programs:
        db = world(schema, False)
        try:
            attempted += 1
            try:
                if program != "IDENTITY":
                    db.execute(program)
                valid = observe(db, probe) and verify_native(db, schema)
            except (sqlite3.Error, ValueError, AssertionError):
                valid = False  # disposable candidate world; failed closed
            if valid:
                winners.append(program)
        finally:
            db.close()
    if not winners:
        raise RuntimeError("UNKNOWN_NO_ADMISSIBLE_INTERVENTION")
    best = min(winners, key=lambda p: (len(p), p))
    return {
        "program": best,
        "candidate_count": len(programs) + 1,
        "actual_tested": attempted,
        "valid_programs": winners,
        "selected_by": "native positive and negative consequence tests",
        "all_candidates_evaluated": True,
    }


def engine_identity() -> dict:
    import _sqlite3
    module = Path(_sqlite3.__file__)
    return {
        "sqlite_version": sqlite3.sqlite_version,
        "python_version": sys.version,
        "native_extension_sha256": hashlib.sha256(module.read_bytes()).hexdigest(),
        "extension_filename": module.name,
    }


def compile_method(probe: Probe, program: str) -> dict:
    if not program.startswith("PRAGMA ") or program == "IDENTITY":
        raise ValueError("invalid qualifying intervention")
    data = {
        "type": "sqlite-fk-guard-v1",
        "probe": asdict(probe),
        "intervention": program,
        "runtime": engine_identity(),
        "scope": "fresh sqlite native connection, empty schema, one simple FK",
        "verifier": "separate native SQLite parent-positive + orphan-negative rollback checker",
    }
    return {**data, "manifest_digest": sha_json(data)}


def qualify_capability(manifest: dict) -> None:
    body = {k: v for k, v in manifest.items() if k != "manifest_digest"}
    if sha_json(body) != manifest.get("manifest_digest"):
        raise PermissionError("INVALID_STALE_CAPABILITY_RECORD")
    if manifest.get("type") != "sqlite-fk-guard-v1" or manifest.get("runtime") != engine_identity():
        raise PermissionError("INVALID_CAPABILITY_SCOPE_OR_RUNTIME")
    program = manifest.get("intervention", "")
    if not re.fullmatch(r"PRAGMA [A-Za-z][A-Za-z0-9_]*=(ON|OFF)", program):
        raise PermissionError("INVALID_EXECUTABLE_BODY")


def apply_capability(db: sqlite3.Connection, manifest: dict) -> dict:
    qualify_capability(manifest)
    if db.in_transaction:
        return {"status": "UNKNOWN_ACTIVE_TRANSACTION", "changes": 0}
    probes = candidate_probes(db)
    if len(probes) != 1:
        return {"status": "UNKNOWN_INTERFACE_NOT_UNIQUE", "changes": 0}
    # Reconstruct probe from the CURRENT database rather than target-name replay.
    current = probes[0]
    if observe(db, current):
        return {"status": "VERIFIED_ALREADY_SAFE", "changes": 0}
    db.execute(manifest["intervention"])
    if not observe(db, current):
        return {"status": "UNKNOWN_INTERVENTION_DID_NOT_REPAIR", "changes": 1}
    return {"status": "VERIFIED_NATIVE_INTERVENTION", "changes": 1}


def sample_schemas(seed: str, count: int = 12) -> list[Schema]:
    return [future_schema(seed, i) for i in range(count)]


def fully_informed_baseline(seed: str) -> dict:
    """Run, don't merely speculate about, the stronger conventional baseline."""
    successes = reads = changes = 0
    for schema in sample_schemas(seed):
        for enabled in (False, True):
            db = world(schema, enabled)
            try:
                reading = db.execute("PRAGMA foreign_keys").fetchone()
                reads += 1
                if reading is None:
                    raise AssertionError("baseline lacks direct status observation")
                if not bool(reading[0]):
                    db.execute("PRAGMA foreign_keys=ON")
                    changes += 1
                if verify_native(db, schema):
                    successes += 1
            finally:
                db.close()
    return {
        "method": "direct SQLite PRAGMA foreign_keys read + conditional ON",
        "native_successes": successes,
        "direct_observation_reads": reads,
        "configuration_changes": changes,
        "model_comparator": "NOT_RUN",
        "relative_economics": "EQUAL_PROTECTED_SUCCESS; BASELINE_HAS_NO_133_CANDIDATE_ACQUISITION",
    }


def run(out: Path, seed: str) -> dict:
    initial_off, initial_on = world(DEV, False), world(DEV, True)
    try:
        assert passive(initial_off) == passive(initial_on)
        assert not verify_native(initial_off, DEV)
        assert verify_native(initial_on, DEV)
    finally:
        initial_off.close()
        initial_on.close()
    probe, diagnosis = discover_probe(DEV)
    selection = discover_intervention(DEV, probe)
    method = compile_method(probe, selection["program"])
    tampered = json.loads(json.dumps(method))
    tampered["intervention"] = "PRAGMA foreign_keys=OFF"
    tamper_denied = False
    try:
        qualify_capability(tampered)
    except PermissionError:
        tamper_denied = True
    assert tamper_denied
    cases = []
    for idx, schema in enumerate(sample_schemas(seed)):
        for enabled in (False, True):
            db = world(schema, enabled)
            try:
                earlier = passive(db)
                before = verify_native(db, schema)
                application = apply_capability(db, method)
                after = verify_native(db, schema)
                assert passive(db) == earlier
                expected_changes = 0 if enabled else 1
                assert before == enabled and after and application["changes"] == expected_changes
                assert application["status"].startswith("VERIFIED_")
                cases.append({
                    "index": idx, "schema_hash": sha_json(asdict(schema)),
                    "initially_enabled": enabled, "before": before,
                    "after": after, **application,
                })
            finally:
                db.close()
    ablated = world(sample_schemas(seed)[0], False)
    unaffected = world(sample_schemas(seed)[0], True)
    try:
        ablation_unsafe = verify_native(ablated, sample_schemas(seed)[0])
        ablation_safe = verify_native(unaffected, sample_schemas(seed)[0])
    finally:
        ablated.close()
        unaffected.close()
    assert (ablation_unsafe, ablation_safe) == (False, True)
    baseline = fully_informed_baseline(seed)
    assert baseline["native_successes"] == len(cases)
    receipt = {
        "status": "PASS_NATIVE_BOUNDED_OBSERVATION_AND_INTERVENTION",
        "identity": engine_identity(),
        "seed": seed,
        "protocol": "FROZEN_PROTOCOL.json",
        "diagnosis": diagnosis,
        "probe": {"sql": probe.sql, "values": probe.values},
        "intervention_selection": selection,
        "compiled_capability": method,
        "future_cases": cases,
        "future_cases_pass": len(cases),
        "ablation": {
            "unsafe_without_capability": ablation_unsafe,
            "safe_without_capability": ablation_safe,
        },
        "stale_manifest_denied": tamper_denied,
        "comparative_verdict": "FULL_INFORMATION_BASELINE_TIES_OUTCOMES; LOWER_ACQUISITION_COST",
        "baselines": baseline,
        "claims_not_earned": [
            "new primitive language", "new SQLite law", "unseen codebase",
            "LLM comparative advantage", "commercial speedup", "physical actuator",
        ],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    return receipt


def replay(path: Path, seed: str) -> dict:
    receipt = json.loads(path.read_text())
    manifest = receipt["compiled_capability"]
    qualify_capability(manifest)
    results = []
    for idx, schema in enumerate(sample_schemas(seed)):
        db = world(schema, idx % 2 == 0)
        try:
            result = apply_capability(db, manifest)
            if not verify_native(db, schema):
                raise RuntimeError(f"replay independent verifier rejected {idx}")
            results.append(result["status"])
        finally:
            db.close()
    return {"status": "PASS_COLD_PROCESS_REPLAY", "count": len(results), "results": results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="qualification/world_compiler.sqlite.json")
    parser.add_argument("--seed", default="local-dev-world-compiler")
    parser.add_argument("--replay")
    args = parser.parse_args()
    result = replay(Path(args.replay), args.seed) if args.replay else run(Path(args.out), args.seed)
    print(json.dumps({
        "status": result["status"],
        "cases": result.get("future_cases_pass", result.get("count")),
        "program": result.get("intervention_selection", {}).get("program"),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
