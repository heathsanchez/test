"""Exact-source native cache trace with independent withdrawal/restoration.

This is a bounded Go cache API experiment. Even a successful receipt says
strict G3 UNKNOWN and fair equal-information baseline NOT_TESTED.
"""

import argparse
import json
import os
from pathlib import Path
from contextlib import ExitStack
import re
import shutil
import subprocess
import tempfile


HERE = Path(__file__).resolve().parent
PLANNER = HERE / "planner.go"
PROBE = HERE / "probe.go"
SOURCE_PATTERN = re.compile(r"^[0-9a-f]{40}$")
MODULE_PATTERN = re.compile(r"^[a-zA-Z0-9._~/+-]+$")
CALL_PATTERN = re.compile(r'pkg\.New(?:\[string(?:,string)*\])?\([A-Za-z0-9.," ]*\)')


def checked(argv, *, cwd=None, env=None, timeout=180):
    try:
        p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                           text=True, timeout=timeout, check=False)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as exc:
        return 124, "", f"UNKNOWN_TIMEOUT {exc.cmd}"
    except OSError as exc:
        return 125, "", f"UNKNOWN_COMMAND_IO {exc}"


def persist(output: Path, stage: str, stdout: str, stderr: str):
    (output / f"{stage}.log").write_text(
        f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}\n")


def run_target(repo_root: Path, sha: str, output: Path, *, repo_name: str = "") -> dict:
    """Operate only on a clean checkout at the exact requested Git SHA."""
    repo_root, output = Path(repo_root).resolve(), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "mathgraph.g3.typed-operational-receipt.v5",
        "source_sha": sha,
        "status": "UNKNOWN_NOT_RUN",
        "strict_g3": "UNKNOWN",
        "fair_b1": "NOT_TESTED",
    }
    if not SOURCE_PATTERN.fullmatch(sha):
        result["status"] = "UNKNOWN_INVALID_SOURCE_SHA"
        return result
    rc, stdout, stderr = checked(["git", "rev-parse", "HEAD"], cwd=repo_root)
    if rc != 0 or stdout.strip() != sha:
        result["status"] = "UNKNOWN_SOURCE_SHA_MISMATCH"
        return result
    rc, stdout, stderr = checked(["git", "status", "--porcelain"], cwd=repo_root)
    if rc != 0 or stdout.strip():
        result["status"] = "UNKNOWN_DIRTY_SOURCE"
        return result
    result["source_sha_confirmed"] = True

    modfile = repo_root / "go.mod"
    mod_text = modfile.read_text() if modfile.is_file() else ""
    match = re.search(r"(?m)^module\s+(\S+)", mod_text)
    if modfile.is_file() and (not match or not MODULE_PATTERN.fullmatch(match.group(1))):
        result["status"] = "UNKNOWN_MODULE_PATH"
        return result
    # No tracked source edit: legacy packages are staged under a temporary module
    # whose identity is derived solely from the protocol's declared repository.
    if not modfile.is_file() and not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo_name):
        result["status"] = "UNKNOWN_LEGACY_MODULE_IDENTITY"
        return result
    module = match.group(1) if match else ("github.com/" + repo_name)
    rc, stdout, stderr = checked(["go", "run", str(PLANNER), "--source", str(repo_root)],
                                 cwd=HERE, timeout=140)
    persist(output, "planner", stdout, stderr)
    if rc:
        result["status"] = "UNKNOWN_PARSER_OR_PLANNER"
        return result
    try:
        plan = json.loads(stdout)
    except ValueError:
        result["status"] = "UNKNOWN_PLAN_RECEIPT"
        return result
    result["plan"] = plan
    if plan.get("schema") != "mathgraph.g3.typed-operational.v5":
        result["status"] = "UNKNOWN_PLAN_SCHEMA"
        return result
    if plan.get("status") != "CANDIDATE_CONSTRUCTOR":
        result["status"] = plan.get("status", "UNKNOWN_PLAN_STATUS")
        return result
    call = plan.get("call", "")
    if not CALL_PATTERN.fullmatch(call):
        result["status"] = "UNKNOWN_UNSAFE_PLAN_EXPRESSION"
        return result

    with ExitStack() as ctx:
        run_root = repo_root
        if not modfile.is_file():
            run_root = Path(ctx.enter_context(tempfile.TemporaryDirectory(prefix="mg-v5-legacy-"))) / "source"
            shutil.copytree(repo_root, run_root, ignore=shutil.ignore_patterns(".git"))
            (run_root / "go.mod").write_text("module " + module + "\n\ngo 1.23\n")
            result["environment"] = "TEMPORARY_LEGACY_MODULE_OVERLAY"
        else:
            result["environment"] = "ORIGINAL_SOURCE_MODULE"
        def native(stage, expression, *, allow_build=True, disable_mutator=False):
            with tempfile.TemporaryDirectory(prefix="mg-g3-v5-native-") as td:
                tmp = Path(td)
                shutil.copyfile(PROBE, tmp / "probe.go")
                (tmp / "main.go").write_text(
                    "package main\n"
                    'import ("encoding/json";"os";pkg ' + json.dumps(module) + ')\n' +
                    ("func main(){ " +
                     ("object, err:=" + expression + "; if err!=nil { _=json.NewEncoder(os.Stdout).Encode(Outcome{Status:\"UNKNOWN_CONSTRUCTOR_ERROR\"}); return }; "
                      if plan.get("returns_error") is True else "object:=" + expression + "; ") +
                     " result:=probe(object,os.Getenv(\"MG_NO_BUILD\")!=\"1\");"
                     " _=json.NewEncoder(os.Stdout).Encode(result) }\n"))
                env = os.environ.copy()
                if not allow_build:
                    env["MG_NO_BUILD"] = "1"
                else:
                    env.pop("MG_NO_BUILD", None)
                if disable_mutator:
                    env["MG_NO_MUTATOR"] = "1"
                else:
                    env.pop("MG_NO_MUTATOR", None)
                rc, stdout, stderr = checked(
                    ["go", "run", str(tmp / "main.go"), str(tmp / "probe.go")],
                    cwd=run_root, env=env, timeout=240)
                persist(output, stage, stdout, stderr)
                if rc:
                    return {"status": "UNKNOWN_NATIVE_COMPILATION_OR_EXECUTION",
                            "exit": rc, "compiler_diagnostic": stderr.strip()[-500:]}
                try:
                    parsed = json.loads(stdout)
                except ValueError:
                    return {"status": "UNKNOWN_NATIVE_RECEIPT"}
                if not isinstance(parsed, dict) or not isinstance(parsed.get("status"), str):
                    return {"status": "UNKNOWN_NATIVE_RECEIPT"}
                return parsed

        full = native("native-full", call)
        result["native"] = full
        if full.get("status") != "NATIVE_CACHE_TRACE_PASS":
            result["status"] = "UNKNOWN_NATIVE_SEMANTIC_TRACE"
            return result

        if full.get("used_build") is True:
            withdrawal = native("native-withdraw-build", call, allow_build=False)
            result["withdrawal"] = withdrawal
            if withdrawal.get("status") != "UNKNOWN_NO_OPERATIONAL_REACHABILITY":
                result["status"] = "UNKNOWN_BUILD_WITHDRAWAL"
                return result
        elif plan.get("generic") is True:
            ablated_call = re.sub(r"\[string(?:,string)*\]", "", call, count=1)
            withdrawal = native("native-withdraw-generics", ablated_call)
            if (withdrawal.get("status") == "UNKNOWN_NATIVE_COMPILATION_OR_EXECUTION"
                    and "cannot infer" in withdrawal.get("compiler_diagnostic", "")):
                withdrawal = {"status": "EXPECTED_TYPE_ABLATION_COMPILE_FAILURE"}
            result["withdrawal"] = withdrawal
            if withdrawal.get("status") != "EXPECTED_TYPE_ABLATION_COMPILE_FAILURE":
                result["status"] = "UNKNOWN_GENERIC_WITHDRAWAL"
                return result
        else:
            withdrawal = native("native-withdraw-mutator", call, disable_mutator=True)
            result["withdrawal"] = {"status": "EXPECTED_MUTATOR_WITHDRAWAL"} if withdrawal.get("status") == "UNKNOWN_SET" else withdrawal
            result["withdrawal_scope"] = "OBSERVER_MUTATOR_DISABLED_NOT_LEARNED_OPERATOR_ABLATION"
            if result["withdrawal"].get("status") != "EXPECTED_MUTATOR_WITHDRAWAL":
                result["status"] = "UNKNOWN_MUTATOR_WITHDRAWAL"
                return result

        restored = native("native-restored", call)
        result["restoration"] = restored
        if restored.get("status") != "NATIVE_CACHE_TRACE_PASS":
            result["status"] = "UNKNOWN_RESTORATION"
            return result
        result["status"] = "WARRANTED_BOUNDED_NATIVE_CACHE_TRACE_ONLY"
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    protocol = json.loads(Path(args.targets).read_text())
    if protocol.get("schema") != "mathgraph.g3.v5.cold.v1":
        raise ValueError("UNKNOWN_TARGET_MANIFEST_SCHEMA")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for target in protocol["targets"]:
        name, sha = target["repo"], target["sha"]
        rank = target["rank"]
        item = {"rank": rank, "repository": name, "source_sha": sha,
                "status": "UNKNOWN_NOT_RUN", "strict_g3": "UNKNOWN",
                "fair_b1": "NOT_TESTED"}
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", name) or not SOURCE_PATTERN.fullmatch(sha):
            item["status"] = "UNKNOWN_TARGET_METADATA"
        else:
            with tempfile.TemporaryDirectory(prefix=f"mg-g3-v5-rank{rank}-") as td:
                source = Path(td) / "source"
                rc, stdout, stderr = checked(
                    ["git", "clone", "--quiet", "--no-checkout",
                     f"https://github.com/{name}.git", str(source)], timeout=180)
                persist(output, f"rank{rank}-clone", stdout, stderr)
                if rc:
                    item["status"] = "UNKNOWN_SOURCE_CLONE"
                else:
                    rc, stdout, stderr = checked(
                        ["git", "checkout", "--quiet", "--detach", sha], cwd=source)
                    persist(output, f"rank{rank}-checkout", stdout, stderr)
                    if rc:
                        item["status"] = "UNKNOWN_SOURCE_CHECKOUT"
                    else:
                        item = {"rank": rank, "repository": name,
                                **run_target(source, sha, output / f"rank{rank}", repo_name=name)}
        results.append(item)
        (output / f"rank{rank}-status.json").write_text(json.dumps(item, indent=2) + "\n")
        print("RESULT", json.dumps(item, sort_keys=True), flush=True)
    (output / "summary.json").write_text(json.dumps(results, indent=2) + "\n")
    print("STRICT_G3=UNKNOWN FAIR_B1=NOT_TESTED", flush=True)


if __name__ == "__main__":
    main()
