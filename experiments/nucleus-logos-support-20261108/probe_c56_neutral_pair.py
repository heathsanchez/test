"""C56: read-only native qualified-recursor pair and rigid mismatch census."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from probe_c52_six_loss_census import CASES, parse_downstream
from probe_c54_first_failure_roots import first_failed_value_root
from probe_c55_app_failure_shape import parse_app_observation

PAIR = re.compile(r"^NUCLEUS_C56_PAIR:seq=(\d+):depth=(\d+):context_depth=(\d+):budget=(\d+):left=(.+):right=(.+)$")
RIGID = re.compile(r"^NUCLEUS_C56_RIGID:seq=(\d+):source_expr=ExprId\((\d+)\):source_env=(\d+):context_depth=(\d+):remaining=(\d+):exposed=(.+):other=(.+)$")
NAME_ID = re.compile(r"NameId\((\d+)\)")


def source_names(source: bytes) -> dict[int, str]:
    names = {0: ""}
    for line in source.splitlines():
        record = json.loads(line)
        if "in" not in record:
            continue
        part = record.get("str", record.get("num"))
        if part is None or part["pre"] not in names or record["in"] in names:
            raise ValueError("invalid native name chain")
        names[record["in"]] = (names[part["pre"]] + "." + str(part.get("str", part.get("i")))).removeprefix(".")
    return names


def parse_neutral_observation(stderr: bytes, names: dict[int, str]) -> dict:
    pairs, rigid = [], []
    for line in stderr.decode(errors="replace").splitlines():
        if line.startswith("NUCLEUS_C56_PAIR:"):
            match = PAIR.fullmatch(line)
            if not match:
                raise ValueError("malformed qualified neutral-pair observation")
            seq, depth, context, budget, left, right = match.groups()
            ids = sorted({int(x) for x in NAME_ID.findall(left + right)})
            if any(i not in names for i in ids):
                raise ValueError("neutral pair references absent original source name")
            pairs.append({"seq": int(seq), "depth": int(depth),
                          "context_depth": int(context), "budget": int(budget),
                          "left": left, "right": right,
                          "native_names": {str(i): names[i] for i in ids}})
        if line.startswith("NUCLEUS_C56_RIGID:"):
            match = RIGID.fullmatch(line)
            if not match:
                raise ValueError("malformed rigid type mismatch observation")
            seq, expr, env, depth, remaining, exposed, other = match.groups()
            rigid.append({"seq": int(seq), "source_expr": int(expr),
                          "source_env": int(env), "context_depth": int(depth),
                          "remaining": int(remaining), "exposed": exposed, "other": other})
    for group in (pairs, rigid):
        if any(b["seq"] <= a["seq"] for a,b in zip(group,group[1:])):
            raise ValueError("non-monotone diagnostic event sequence")
    return {"neutral_pair_samples": pairs[:64], "rigid_type_samples": rigid[:64],
            "qualified_pair_events_logged": len(pairs), "rigid_events_logged": len(rigid),
            "sampled_not_full_census": True, "partial_values_are_proofs": False}


def run_census(binary: Path, arena: Path, flags_path: Path, c55_path: Path,
               log_dir: Path, timeout: int) -> dict:
    flags = json.loads(flags_path.read_text())
    if len(flags) != 24 or set(flags.values()) != {"1"}:
        raise ValueError("selected source-qualified 24 flags required")
    parent = json.loads(c55_path.read_text())
    if not parent.get("all_six_unknown") or not parent.get("all_six_root_classified"):
        raise ValueError("C55 complete first-root receipt required")
    previous = {item["case"]: item for item in parent["cases"]}
    if set(previous) != set(CASES):
        raise ValueError("original six not preserved")
    log_dir.mkdir(parents=True, exist_ok=True)
    result = {"diagnostic": "C56 source-qualified neutral pair snapshot",
              "steps_per_case": 262144, "original_artifact_id": 13276400289,
              "proof_rules_changed": False, "partial_values_are_proofs": False,
              "cases": []}
    for case in CASES:
        source = (arena / "good" / "perf" / (case + ".ndjson")).read_bytes()
        prior = previous[case]
        if hashlib.sha256(source).hexdigest() != prior["source_sha256"]:
            raise ValueError("original source checksum changed")
        _, root = first_failed_value_root(source, prior)
        if root != prior["first_failed_root"]:
            raise ValueError("C55 root inconsistent with native declarations")
        env = {k: v for k,v in os.environ.items() if not k.startswith("NUCLEUS_")}
        env.update(flags)
        env.update({"NUCLEUS_DIAGNOSTIC_C38_EARLY_TYPED_SPINE": "1",
                    "NUCLEUS_DIAGNOSTIC_C47_PROFILE_EXPR": str(root),
                    "NUCLEUS_DIAGNOSTIC_C55_APP_SHAPE": "1",
                    "NUCLEUS_DIAGNOSTIC_C56_NEUTRAL_PAIR": "1",
                    "NUCLEUS_TRACE_DOWNSTREAM": "1"})
        entry = {"case": case, "source_sha256": prior["source_sha256"],
                 "first_failed_root": root, "first_failed_boundary": prior["first_failed_boundary"]}
        try:
            run = subprocess.run([str(binary.resolve()), "262144"], input=source,
                                 capture_output=True, env=env, timeout=timeout)
        except subprocess.TimeoutExpired:
            entry["verdict"] = "TIMEOUT_NOT_CHECKER_VERDICT"
            result["cases"].append(entry)
            continue
        log_dir.joinpath(case + ".stderr").write_bytes(run.stderr)
        if run.returncode != 2 or run.stdout or parse_downstream(run.stderr) != prior["first_failed_boundary"]:
            raise ValueError("C56 checker verdict or failing source boundary changed")
        parse_app_observation(run.stderr, root)
        entry.update({"verdict": "UNKNOWN", "observations": parse_neutral_observation(run.stderr,source_names(source))})
        result["cases"].append(entry)
    result["all_six_unknown"] = all(x["verdict"] == "UNKNOWN" for x in result["cases"])
    result["all_six_profiled"] = all("observations" in x for x in result["cases"])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--arena", required=True, type=Path)
    parser.add_argument("--flags", required=True, type=Path)
    parser.add_argument("--c55", required=True, type=Path)
    parser.add_argument("--logs", required=True, type=Path)
    parser.add_argument("--timeout", default=180, type=int)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 600:
        raise ValueError("bounded per-case timeout required")
    r = run_census(args.binary,args.arena,args.flags,args.c55,args.logs,args.timeout)
    print(json.dumps(r, indent=2))
    if not r["all_six_unknown"] or not r["all_six_profiled"]:
        raise SystemExit("C56 incomplete: retain UNKNOWN, never assume evidence")


if __name__ == "__main__":
    main()
