#!/usr/bin/env python3
"""Officially rescore preserved blind Hard evidence; never rerun site mutations."""
from __future__ import annotations

import argparse
import collections
import json
import math
import re
from pathlib import Path

from webarena_verified.api import WebArenaVerified
from webarena_verified.types.config import WebArenaVerifiedConfig
from webarena_verified.types.tracing import NetworkTrace

UPSTREAM = "6473f72db5dcefc97b5725b59e734504edc28a21"


class EvidenceError(RuntimeError):
    """Declared completed execution has incomplete or contradictory evidence."""


def validate_identity(tasks, manifest):
    """Cardinality alone cannot establish that 258 distinct tasks were scored."""
    if not isinstance(tasks, list) or not isinstance(manifest, dict):
        raise RuntimeError("Hard-258 task/manifest identity schema invalid")
    if len(tasks) != 258 or len(manifest) != 258:
        raise RuntimeError("Hard-258 evidence incomplete")
    ids = []
    for task in tasks:
        ident = task.get("task_id") if isinstance(task, dict) else None
        if not isinstance(ident, int) or isinstance(ident, bool):
            raise RuntimeError("Hard-258 task identity must be an integer")
        ids.append(str(ident))
    if len(set(ids)) != 258:
        raise RuntimeError("Hard-258 requires 258 unique task identities")
    if set(ids) != set(manifest):
        raise RuntimeError("Hard-258 task and manifest identity sets differ")
    slots = []
    for entry in manifest.values():
        slot = entry.get("opaque_slot") if isinstance(entry, dict) else None
        if not isinstance(slot, str) or not re.fullmatch(r"[0-9a-f]{32}", slot):
            raise RuntimeError("invalid opaque output slot")
        slots.append(slot)
    if len(set(slots)) != len(slots):
        raise RuntimeError("opaque output slots must be unique")


def score(root: Path, output: Path):
    tasks = json.loads((root / "hard.json").read_text())
    manifest = json.loads((root / "execution_manifest.json").read_text())
    validate_identity(tasks, manifest)
    wa = WebArenaVerified(config=WebArenaVerifiedConfig.from_file(root / "config.json"))
    empty = NetworkTrace.model_construct(
        is_playwright=False,
        src_file=Path("<no-network-events-captured>"),
        events=(),
    )
    results = {}
    failed = collections.Counter()
    success_by_site = collections.Counter()
    completed_by_site = collections.Counter()
    for task_record in tasks:
        ident = int(task_record["task_id"])
        key = str(ident)
        record = manifest[key]
        output_dir = root / "output" / record["opaque_slot"]
        if not output_dir.resolve().is_relative_to((root / "output").resolve()):
            raise RuntimeError("opaque output slot resolves outside evidence root")
        site = "+".join(task_record.get("sites") or [])
        completed = (
            record["execution_class"] == "agent_executed"
            and (output_dir / "agent_response.json").is_file()
        )
        entry = {
            "score": 0.0,
            "site": site,
            "agent_completed": completed,
            "execution_class": record["execution_class"],
        }
        if completed:
            completed_by_site[site] += 1
        try:
            if record["execution_class"] == "agent_executed":
                if not completed:
                    raise EvidenceError("completed execution is missing agent_response.json")
                if record.get("agent_exit_code") != 0:
                    raise EvidenceError("completed execution has a nonzero or missing exit code")
            official = wa.get_task(ident)
            protected = any(
                criterion.evaluator == "NetworkEventEvaluator"
                for criterion in official.eval
            )
            trace_path = output_dir / "network.har"
            if protected and completed and not trace_path.is_file():
                raise EvidenceError("completed network-protected task is missing network.har")
            trace = (
                NetworkTrace.from_har(trace_path)
                if protected and completed and trace_path.is_file()
                else empty
            )
            evaluation = wa.evaluate_task(
                task_id=ident,
                agent_response=output_dir / "agent_response.json",
                network_trace=trace,
            )
            value = float(evaluation.score)
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise RuntimeError("official evaluator returned an invalid numeric score")
            entry["official_score"] = value
            entry["official_status"] = evaluation.status.value
            if completed and entry["official_score"] == 1.0 and entry["official_status"] == "success":
                entry["score"] = 1.0
                success_by_site[site] += 1
            else:
                failed[record["execution_class"]] += 1
        except EvidenceError as exc:
            entry["score"] = None
            entry["evidence_error"] = str(exc)
            failed["evidence_error"] += 1
        except Exception as exc:
            # A verifier malfunction is UNKNOWN, not an observed task failure.
            entry["score"] = None
            entry["evaluation_error"] = repr(exc)
            failed["official_evaluation_error"] += 1
        results[key] = entry

    wins = sum(row["score"] == 1.0 for row in results.values())
    unknown = sum(row["score"] is None for row in results.values())
    metric_valid = len(results) == 258 and unknown == 0
    report = {
        "epistemic_state": (
            "WARRANTED_BOUNDED_RETAINED_BLIND_DIAGNOSTIC" if metric_valid else "UNKNOWN"
        ),
        "metric_valid": metric_valid,
        "official_evaluation_error_count": failed["official_evaluation_error"],
        "evidence_error_count": failed["evidence_error"],
        "unknown_count": unknown,
        "known_unsuccessful_count": sum(row["score"] == 0.0 for row in results.values()),
        "boundary": "Rescore of unchanged 258-task Hard agent outputs; four site environments only, shared state, no Map/Wikipedia servers",
        "upstream_commit": UPSTREAM,
        "original_action_run": 37891173089,
        "original_artifact": 11599635564,
        "total": 258,
        "presented": len(manifest),
        "agent_completed": sum(row["agent_completed"] for row in results.values()),
        "official_success_count": int(wins),
        "score_fraction": wins / 258 if metric_valid else None,
        "success_fraction_lower_bound": wins / 258,
        "by_site": dict(success_by_site),
        "agent_completed_by_site": dict(completed_by_site),
        "failed_by_class": dict(failed),
        "results": results,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "qualification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: val for key, val in report.items() if key != "results"}, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = score(Path(args.input), Path(args.output))
    if not report["metric_valid"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
