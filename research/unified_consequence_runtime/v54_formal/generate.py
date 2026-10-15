#!/usr/bin/env python3
"""Bind actual V54 native traces to a concrete, bounded original-VDN instance.

The complete original cold enumeration is reconstructed from the retained
double-broken source, independently of the producer's survivor list. Missing
observations, inconsistent observations, native errors, or a cold pass refuse
generation. This checks evidence; it is not a Python-to-Lean refinement proof.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
import keyword
import os
from pathlib import Path
import sys
import tokenize

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent / "archaeology/semantics/source/triskelion/v54/experiments/METALOGIC_TWO_GENERATION_COMPOUNDING_V54.py"
ORIGINAL_SHA256 = "13c05aea8d6c1ce2db6d3d4b85c566ee3dbd2f3fcc1c3c8c14c1c2dece7f05ba"
ORIGINAL_COMMIT = "2dd5f41b6c7cec1004b8deaee4f976dd2a9ed21c"
REQUESTS_COMMIT = "8068356288978c4f54661ae6f95afe0e0831885e"
TARGET_FILE = "src/requests/utils.py"
NATIVE_COMMAND = "timeout 7s pytest -q tests/test_utils.py -k test_iter_slices"
EXCLUDED = {":", "(", ")", ".", ","}
OUTCOMES = {"pass": "passed", "native_failure": "failed", "timeout": "timedOut"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def artifact(path: Path, base: Path | None = None) -> dict:
    name = os.path.relpath(path.resolve(), base.resolve()) if base else str(path.resolve())
    return {"path": name, "sha256": sha(path.read_bytes())}


def snapshot(path: Path) -> dict:
    item = json.loads(path.read_text())
    if not isinstance(item, dict):
        raise ValueError(f"Snapshot must be a JSON object: {path}")
    if not isinstance(item.get("source_text"), str):
        raise ValueError(f"Snapshot lacks retained source_text: {path}")
    if item.get("source_sha256") != sha(item["source_text"].encode()):
        raise ValueError(f"Snapshot source SHA256 mismatch: {path}")
    line_no = item.get("line_no")
    if type(line_no) is not int or not 1 <= line_no <= len(item["source_text"].splitlines()):
        raise ValueError(f"Snapshot target line missing: {path}")
    if item.get("scope", {}).get("relative_path", TARGET_FILE) != TARGET_FILE:
        raise ValueError(f"Unexpected snapshot target file: {path}")
    return item


def enumerate_rewrites(state: dict, destinations: list[str]) -> list[dict]:
    """Original one_rewrite_discovery loop, including its punctuation exclusions."""
    rows = state["source_text"].splitlines(True)
    line_no = state["line_no"]
    line = state["source_text"].splitlines()[line_no - 1]
    tokens = [t for t in tokenize.generate_tokens(io.StringIO(line + "\n").readline)
              if t.type in (tokenize.NAME, tokenize.OP)]
    candidates = []
    for token in tokens:
        if token.string in EXCLUDED:
            continue
        for destination in destinations:
            if destination == token.string:
                continue
            c0, c1 = token.start[1], token.end[1]
            current = rows[line_no - 1]
            if c1 > len(current) or current[c0:c1] != token.string:
                continue
            altered = rows.copy()
            altered[line_no - 1] = current[:c0] + destination + current[c1:]
            candidates.append({"index": len(candidates), "src": token.string,
                               "dst": destination, "col": c0, "end_col": c1,
                               "line_no": line_no,
                               "source_sha256": sha("".join(altered).encode())})
    return candidates


def normalize_call(call: dict) -> str:
    status = call.get("status")
    if status not in OUTCOMES:
        raise ValueError(f"Missing/unknown/error native observation at call {call.get('id')}: {status}")
    if type(call.get("passed")) is not bool or call["passed"] != (status == "pass"):
        raise ValueError(f"Inconsistent native pass/status at call {call.get('id')}")
    if status == "pass" and call.get("returncode") != 0:
        raise ValueError(f"Native pass lacks exit zero at call {call.get('id')}")
    if status == "native_failure" and (type(call.get("returncode")) is not int or call["returncode"] == 0):
        raise ValueError(f"Native failure lacks a nonzero exit at call {call.get('id')}")
    # Original Requests uses `timeout 7s ...`; the shell's 124 is a timeout
    # even when the outer process wrapper labels its nonzero exit a failure.
    if status == "timeout" or call.get("returncode") == 124:
        return "timedOut"
    return OUTCOMES[status]


def lean_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render(data: dict) -> str:
    rows = [f"    ⟨{lean_string(c['source_sha256'])}, .{c['outcome']}⟩" for c in data["cold"]]
    return """import BoundedV54

-- Generated from actual native evidence. The manifest authenticates that evidence.
set_option maxRecDepth 100000
set_option maxHeartbeats 0

namespace ActualV54
open VerifiedDevelopmentalNavigation

def snapshot : V54.Snapshot where
""" + f"""  start := {lean_string(data['start']['source_sha256'])}
  warm := {lean_string(data['warm']['source_sha256'])}
  target := {lean_string(data['final']['source_sha256'])}
  startOutcome := .{data['start']['outcome']}
  warmOutcome := .{data['warm']['outcome']}
  targetOutcome := .{data['final']['outcome']}
  cold := [
""" + ",\n".join(rows) + """
  ]

theorem startDiffers : snapshot.start ≠ snapshot.target := by decide

theorem coldExcludesTarget :
    ∀ c ∈ snapshot.cold, c.sourceSha256 ≠ snapshot.target :=
  V54.coldExcludesTarget_of_check snapshot (by decide)

theorem coldTableNonpassing :
    ∀ c ∈ snapshot.cold, c.outcome ≠ V54.NativeOutcome.passed :=
  V54.coldNonpassing_of_check snapshot (by decide)

def phaseChangeCertificate : CapabilityPhaseChangeCertificate
    (V54.oldWorld snapshot) (V54.newWorld snapshot) snapshot.start snapshot.target :=
  V54.certificate snapshot startDiffers coldExcludesTarget

theorem certifiedPhaseChange :
    (¬ (V54.oldWorld snapshot).ReachableWithin
        (V54.oldBoundary snapshot) snapshot.start snapshot.target) ∧
      (V54.newWorld snapshot).Reachable snapshot.start snapshot.target :=
  phaseChangeCertificate.phase_change

theorem everyOldCapabilityRetained {x y : String}
    (h : (V54.oldWorld snapshot).Reachable x y) :
    (V54.newWorld snapshot).Reachable x y :=
  phaseChangeCertificate.retains_old_capability h

theorem oldBoundaryHasNoRecordedPass :
    ∀ trace, V54.oldBoundary snapshot trace → ∀ x,
      (V54.oldWorld snapshot).run trace snapshot.start = some x →
      (V54.oldWorld snapshot).observe () x ≠ V54.NativeOutcome.passed :=
  V54.oldBoundary_no_recorded_pass snapshot startDiffers coldExcludesTarget
    (by decide) (by decide) coldTableNonpassing

theorem finalHasRecordedPass :
    (V54.newWorld snapshot).observe () snapshot.target = V54.NativeOutcome.passed := by
  decide

end ActualV54

#print axioms ActualV54.certifiedPhaseChange
#print axioms ActualV54.everyOldCapabilityRetained
#print axioms ActualV54.oldBoundaryHasNoRecordedPass
#print axioms ActualV54.finalHasRecordedPass
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-calls", required=True, type=Path)
    parser.add_argument("--broken", required=True, type=Path)
    parser.add_argument("--warm", required=True, type=Path)
    parser.add_argument("--final", required=True, type=Path)
    parser.add_argument("--input", type=Path, help="Optional complete root acquisition artifact to bind")
    parser.add_argument("--provenance", type=Path,
                        help="Original source/world provenance (default: beside native calls)")
    parser.add_argument("--output-dir", type=Path, default=HERE)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": "v54-formal-evidence-v1", "status": "UNKNOWN",
                "scope": "Frozen native source-hash table; old action traces of length <= 1.",
                "artifacts": {}}
    manifest_path = out / "evidence-manifest.json"
    # Invalidate previous evidence before doing work, including interrupted runs.
    for name in ("GeneratedV54.lean", "transition-table.json", "lean-verification.json"):
        (out / name).unlink(missing_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    try:
        if sha(ORIGINAL.read_bytes()) != ORIGINAL_SHA256:
            raise ValueError("Pinned original V54 source changed")
        paths = {"original": ORIGINAL, "native_calls": args.native_calls,
                 "broken": args.broken, "warm": args.warm, "final": args.final,
                 "provenance": args.provenance or args.native_calls.parent / "source-provenance.json"}
        if args.input:
            paths["acquisition"] = args.input
        # Native qualification may continue appending restoration observations.
        # Freeze the exact admitted prefix and source snapshots for portable replay.
        frozen = out / "evidence"
        frozen.mkdir(parents=True, exist_ok=True)
        origins = {}
        for key, path in list(paths.items()):
            if key == "original":
                continue
            destination = frozen / {"native_calls": "native-calls.jsonl", "broken": "state-double-broken.json",
                                    "warm": "state-warm-after-O1.json", "final": "state-final.json",
                                    "provenance": "source-provenance.json",
                                    "acquisition": "acquisition.json"}[key]
            content = path.read_bytes()
            destination.write_bytes(content)
            origins[key] = str(path.resolve())
            paths[key] = destination
        manifest["artifacts"] = {key: artifact(value, out) for key, value in paths.items()}
        manifest["frozen_from"] = origins
        provenance = json.loads(paths["provenance"].read_text())
        if (not isinstance(provenance, dict) or provenance.get("commit") != ORIGINAL_COMMIT
                or provenance.get("sha256") != ORIGINAL_SHA256
                or provenance.get("world_pins", {}).get("requests") != REQUESTS_COMMIT):
            raise ValueError("Native source/world provenance differs from original pins")
        expected_cwd = provenance.get("relocated_paths", {}).get("requests")
        if not isinstance(expected_cwd, str):
            raise ValueError("Requests native world path is absent from provenance")
        broken, warm, final = [snapshot(paths[key]) for key in ("broken", "warm", "final")]
        for state in (broken, warm, final):
            if state.get("path") != str(Path(expected_cwd) / TARGET_FILE):
                raise ValueError("Retained source snapshot is outside the pinned Requests world path")
        if len({s["line_no"] for s in (broken, warm, final)}) != 1:
            raise ValueError("Snapshots disagree on the target line")
        if len({s["source_sha256"] for s in (broken, warm, final)}) != 3:
            raise ValueError("Broken/warm/final must be distinct actual sources")
        destinations = sorted(set([s for s in tokenize.EXACT_TOKEN_TYPES if 1 <= len(s) <= 2] + keyword.kwlist))
        candidates = enumerate_rewrites(broken, destinations)
        calls = [json.loads(line) for line in paths["native_calls"].read_text().splitlines() if line.strip()]
        if any(not isinstance(call, dict) for call in calls):
            raise ValueError("Native calls must be JSON objects")
        cold = [call for call in calls if call.get("phase") == "cold"]
        expected = [c["source_sha256"] for c in candidates]
        observed = [c.get("candidate_source_sha256", {}).get(TARGET_FILE) for c in cold]
        if expected != observed:
            raise ValueError(f"Incomplete or reordered original cold enumeration: expected {len(expected)}, observed {len(observed)}; multiset_equal={Counter(expected) == Counter(observed)}")
        if not candidates:
            raise ValueError("Cold candidate language is empty")
        normalized = {}
        for call in calls:
            digest = call.get("candidate_source_sha256", {}).get(TARGET_FILE)
            if digest is None:
                continue
            if call.get("cwd") != expected_cwd:
                raise ValueError(f"Requests observation uses another native world at call {call.get('id')}")
            if call.get("command") != NATIVE_COMMAND:
                raise ValueError(f"Requests observation uses a different native command at call {call.get('id')}")
            if not isinstance(call.get("timeout_seconds"), (int, float)) or call["timeout_seconds"] < 7:
                raise ValueError(f"Requests observation truncates the original seven-second horizon at call {call.get('id')}")
            value = normalize_call(call)
            if digest in normalized and normalized[digest] != value:
                raise ValueError(f"Nondeterministic outcome table at source {digest}")
            normalized[digest] = value
        for candidate, call in zip(candidates, cold):
            candidate.update(outcome=normalize_call(call), native_call_id=call.get("id"),
                             native_status=call["status"], returncode=call.get("returncode"),
                             timeout_seconds=call.get("timeout_seconds"))
            if candidate["outcome"] == "passed":
                raise ValueError("A cold one-rewrite candidate passed; claimed obstruction is false")
            if candidate["source_sha256"] == final["source_sha256"]:
                raise ValueError("Final accepted source appears in the cold one-rewrite language")
        states = {}
        for name, state in (("start", broken), ("warm", warm), ("final", final)):
            digest = state["source_sha256"]
            if digest not in normalized:
                raise ValueError(f"No native observation for actual {name} source {digest}")
            states[name] = {"source_sha256": digest, "outcome": normalized[digest]}
            required_phase = "warm_assert" if name == "warm" else "execute_native"
            direct = [call for call in calls if call.get("phase") == required_phase
                      and call.get("candidate_source_sha256", {}).get(TARGET_FILE) == digest]
            if not direct:
                raise ValueError(f"No direct {required_phase} observation for actual {name} source")
            states[name]["direct_native_call_ids"] = [call.get("id") for call in direct]
        if states["start"]["outcome"] == "passed" or states["warm"]["outcome"] == "passed":
            raise ValueError("Broken or O1-only source passed")
        if states["final"]["outcome"] != "passed":
            raise ValueError("Actual final source lacks native acceptance")
        edges = []
        for name, before, after in (("O1", broken, warm), ("O2", warm, final)):
            matches = [c for c in enumerate_rewrites(before, destinations)
                       if c["source_sha256"] == after["source_sha256"]]
            if len(matches) != 1:
                raise ValueError(f"{name} edge is not exactly one actual source token rewrite")
            edge = dict(matches[0], operator=name, from_sha256=before["source_sha256"],
                        to_sha256=after["source_sha256"])
            edges.append(edge)
        if args.input:
            qualification = json.loads(paths["acquisition"].read_text())
            learned = {"O1": qualification["O1_acquisition"]["operator"],
                       "O2": qualification["warm"]["construction"]["operator"]}
            for edge in edges:
                expected_operator = {"kind": "TOKEN_REWRITE", "src": edge["src"], "dst": edge["dst"]}
                if learned[edge["operator"]] != expected_operator:
                    raise ValueError(f"{edge['operator']} source edge differs from acquired executable operator")
            manifest["acquired_operator_identity_checked"] = True
        else:
            manifest["acquired_operator_identity_checked"] = False
        data = {**states, "cold": candidates}
        generated = out / "GeneratedV54.lean"
        generated.write_text(render(data))
        manifest.update(status="EVIDENCE_COMPLETE_AWAITING_LEAN", python_version=sys.version,
                        destinations=destinations, excluded_tokens=sorted(EXCLUDED),
                        line_no=broken["line_no"], candidate_count=len(candidates),
                        old_cover_count=1 + len(candidates),
                        native_command=NATIVE_COMMAND, native_shell_timeout_seconds=7,
                        cold_outcome_counts=dict(Counter(c["outcome"] for c in candidates)),
                        cold_native_status_counts=dict(Counter(c["native_status"] for c in candidates)),
                        states=states, acquired_edges=edges,
                        generated=artifact(generated, out))
        (out / "transition-table.json").write_text(json.dumps(data, indent=2) + "\n")
        manifest["transition_table"] = artifact(out / "transition-table.json", out)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, SyntaxError, tokenize.TokenError) as exc:
        manifest["reason"] = str(exc)
        # Never leave a stale concrete certificate beside an UNKNOWN manifest.
        for name in ("GeneratedV54.lean", "transition-table.json"):
            (out / name).unlink(missing_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"status": manifest["status"], "manifest": str(manifest_path),
                      "reason": manifest.get("reason")}, indent=2))
    return 0 if manifest["status"] == "EVIDENCE_COMPLETE_AWAITING_LEAN" else 1


if __name__ == "__main__":
    sys.exit(main())
