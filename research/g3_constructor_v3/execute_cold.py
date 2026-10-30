"""Execute one frozen constructor algorithm on exact source-pinned Go modules.

This runner never changes the type-planner or feedback bridge, admits no manual
adapters, records non-applicability as UNKNOWN, and separates post-hoc controls
from cold evidence. Executions happen only in an isolated CI job.
"""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
PLANNER = HERE.parents[0] / "g3_constructor_v2" / "constructor_planner.go"
BRIDGE = HERE / "native_feedback_bridge.py"


def checked(command, *, cwd=None, timeout=180):
    try:
        p = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                           timeout=timeout, check=False)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as exc:
        return 124, "", f"UNKNOWN_COMMAND_TIMEOUT {exc.cmd}"
    except OSError as exc:
        return 125, "", f"UNKNOWN_COMMAND_IO {exc}"


def execute_one(spec, output):
    repo = spec["repo"]
    sha = spec["sha"]
    rank = spec["rank"]
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
        raise ValueError("UNKNOWN_REPOSITORY_NAME")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("UNKNOWN_SOURCE_SHA")
    name = f"rank{rank}"
    result = {"rank": rank, "admission": spec["status"], "repository": repo,
              "source_sha": sha, "status": "UNKNOWN_NOT_RUN", "strict_g3": "UNKNOWN",
              "fair_b1": "NOT_TESTED"}

    def persist(stage, stdout, stderr):
        (output / f"{name}-{stage}.log").write_text(
            f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}\n")

    with tempfile.TemporaryDirectory(prefix=f"mg-g3-{name}-") as tmp:
        root = Path(tmp) / "source"
        rc, stdout, stderr = checked(
            ["git", "clone", "--quiet", "--no-checkout", f"https://github.com/{repo}.git", str(root)],
            timeout=160)
        persist("clone", stdout, stderr)
        if rc:
            result["status"] = "UNKNOWN_SOURCE_CLONE"
            return result
        rc, stdout, stderr = checked(["git", "-C", str(root), "checkout", "--quiet", "--detach", sha])
        persist("checkout", stdout, stderr)
        if rc:
            result["status"] = "UNKNOWN_SOURCE_PIN"
            return result
        rc, head, stderr = checked(["git", "-C", str(root), "rev-parse", "HEAD"])
        if rc or head.strip() != sha:
            result["status"] = "UNKNOWN_SOURCE_SHA_MISMATCH"
            return result
        result["source_sha_confirmed"] = True
        print(f"PINNED {name} {repo} {sha}", flush=True)

        plan_path = output / f"{name}-plan.json"
        rc, stdout, stderr = checked(
            ["go", "run", str(PLANNER), "--source", str(root), "--out", str(plan_path)],
            timeout=120)
        persist("planner", stdout, stderr)
        if rc or not plan_path.is_file():
            result["status"] = "UNKNOWN_PARSER_OR_PLANNER"
            return result
        plan = json.loads(plan_path.read_text())
        result["plan"] = {k:plan.get(k) for k in
                          ("status", "constructor", "call", "candidate_count", "uninhabitable_count")}
        print(f"PLAN {name} {json.dumps(result['plan'], sort_keys=True)}", flush=True)
        if plan.get("status") != "CANDIDATE_CONSTRUCTOR":
            result["status"] = plan["status"]
            return result

        go_mod = root / "go.mod"
        if not go_mod.is_file():
            result["status"] = "UNKNOWN_MODULE_ROOT"
            return result
        match = re.search(r"^module\s+([^\s]+)", go_mod.read_text(), re.M)
        if match is None:
            result["status"] = "UNKNOWN_MODULE_PATH"
            return result
        module = match.group(1)
        rc, stdout, stderr = checked(
            [sys.executable, str(BRIDGE), "--manifest", str(plan_path),
             "--source-dir", str(root), "--module", module, "--sha", sha])
        persist("bridge", stdout, stderr)
        if rc:
            result["status"] = "UNKNOWN_NATIVE_BRIDGE"
            return result

        rc, stdout, stderr = checked(["go", "run", "./cmd/mgconstructor"], cwd=root, timeout=240)
        persist("native", stdout, stderr)
        if rc:
            result["status"] = "UNKNOWN_NATIVE_CONSTRUCTION"
            result["native_exit"] = rc
            return result
        try:
            receipt = json.loads(stdout)
        except ValueError:
            result["status"] = "UNKNOWN_NATIVE_RECEIPT_PARSE"
            return result
        if receipt.get("source_sha") != sha or receipt.get("status") not in (
                "CONSTRUCTED_NONNIL", "CONSTRUCTED_NONNIL_WITH_HINT_REPAIRS"):
            result["status"] = "UNKNOWN_NATIVE_RECEIPT_MISMATCH"
            return result
        result["status"] = "WARRANTED_BOUNDED_NATIVE_CONSTRUCTION_ONLY"
        result["native"] = {"type": receipt.get("constructed_type"),
                            "status": receipt.get("status"),
                            "attempts": receipt.get("attempts", 1),
                            "repairs": receipt.get("repairs", [])}
        return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    target_manifest = json.loads(Path(args.targets).read_text())
    if target_manifest.get("schema") != "mathgraph.g3.feedback-sample.v3":
        raise ValueError("UNKNOWN_TARGET_MANIFEST_SCHEMA")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for target in target_manifest["targets"]:
        try:
            result = execute_one(target, output)
        except (KeyError, ValueError) as exc:
            result = {"rank": target.get("rank"), "repository": target.get("repo"),
                      "status": "UNKNOWN_MALFORMED_INPUT", "detail": str(exc),
                      "strict_g3": "UNKNOWN"}
        results.append(result)
        (output / f"rank{target['rank']}-status.json").write_text(json.dumps(result, indent=2)+"\n")
        print("RESULT", json.dumps(result, sort_keys=True), flush=True)
    (output / "summary.json").write_text(json.dumps(results, indent=2)+"\n")
    print("STRICT_G3=UNKNOWN", flush=True)
    print("FAIR_B1_MANUAL_BASELINE=NOT_TESTED", flush=True)


if __name__ == "__main__":
    main()
