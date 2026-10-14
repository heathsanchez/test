#!/usr/bin/env python3
"""Generic source-native Go regression selector / causal base-head replay.

Only frozen repository and commit IDs are case-configured. All test files,
function names, backend-package labels and commands are derived from exact
Git diff and original contributor test sources. No repaired code is injected.
This does NOT prove cross-backend equality for shared runtime inputs.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE / "native_work"
EVIDENCE = HERE / "native_evidence"
ROOT.mkdir(parents=True, exist_ok=True)
EVIDENCE.mkdir(parents=True, exist_ok=True)

SOURCE_REPOSITORY = "howlcipher/howlframe"
BASE = "21efc6cb4742d7ae101288dfc67819bb549c1307"
HEAD = "151a033119a6f1acd3c7adce2524ce0768178be9"
GO_TEST_NAME = re.compile(r"(?m)^\s*func\s+(Test[A-Za-z0-9_]+)\s*\(\s*t\s+\*testing\.T\s*\)")
SHA = re.compile(r"^[a-f0-9]{40}$")
LOGS = []
CHECKS = {}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def blob(raw):
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()

def run(name, args, cwd=ROOT, timeout=320, valid=(0,)):
    started = time.monotonic()
    try:
        p = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, check=False, text=True,
                           errors="replace", timeout=timeout,
                           env={**os.environ, "GIT_TERMINAL_PROMPT": "0",
                                "GOTOOLCHAIN": "local"})
        code, output = p.returncode, p.stdout
    except subprocess.TimeoutExpired as e:
        code, output = 124, "PROCESS_TIMEOUT\n" + str(e)
    text = "$ " + " ".join(args) + "\n" + output
    (EVIDENCE / (name + ".log")).write_text(text)
    item = {"name": name, "argv": args, "exit_code": code, "valid_codes": list(valid),
            "elapsed_seconds": round(time.monotonic()-started, 3),
            "sha256": sha(text.encode())}
    LOGS.append(item)
    print("STEP", json.dumps(item, sort_keys=True), flush=True)
    if code not in valid:
        raise RuntimeError("COMMAND_FAILED_" + name + "_CODE_" + str(code))
    return code, output

def initialize():
    src = ROOT / "source"
    if not (src / ".git").exists():
        run("git_init", ["git", "init", str(src)])
        run("git_remote", ["git", "-C", str(src), "remote", "add", "origin",
                           "https://github.com/" + SOURCE_REPOSITORY + ".git"])
    for key, ref in [("base", BASE), ("head", HEAD)]:
        run("git_fetch_" + key,
            ["git", "-C", str(src), "fetch", "--no-tags", "--depth=1",
             "origin", ref + ":refs/cross_backend/" + key],
            timeout=270)
        run("git_worktree_" + key,
            ["git", "-C", str(src), "worktree", "add", "--force", "--detach",
             str(ROOT / key), "refs/cross_backend/" + key])
        _, commit = run("source_sha_" + key, ["git", "rev-parse", "HEAD"],
                        cwd=ROOT / key)
        expected = BASE if key == "base" else HEAD
        if commit.strip() != expected:
            raise RuntimeError("SOURCE_COMMIT_MISMATCH_" + key)
    return src

def source_discovery(src):
    _, raw = run("diff_source",
                 ["git", "-C", str(src), "diff", "--name-status", BASE, HEAD])
    changed = {}
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) == 2 and parts[0] in {"A", "M", "D"}:
            changed[parts[1]] = parts[0]
    tests = {path: kind for path, kind in changed.items()
             if path.endswith("_test.go") and kind in {"A", "M"}}
    if not tests:
        raise RuntimeError("NO_NEW_OR_MODIFIED_GO_NATIVE_TEST_SOURCES")
    out = {}
    for path, kind in sorted(tests.items()):
        if Path(path).is_absolute() or ".." in Path(path).parts:
            raise RuntimeError("INVALID_REPO_TEST_PATH")
        test_head = ROOT / "head" / path
        raw = test_head.read_bytes()
        encoded_name = path.replace("/", "_").replace(".", "_")
        _, tree_blob = run("source_blob_" + encoded_name,
                           ["git", "ls-tree", HEAD, path], cwd=src)
        match = re.search(r"\bblob\s+([0-9a-f]{40})\t", tree_blob)
        if match is None or match.group(1) != blob(raw):
            raise RuntimeError("TEST_TREE_BLOB_IDENTITY_MISMATCH")
        names = sorted(set(GO_TEST_NAME.findall(raw.decode("utf-8"))))
        if not names:
            raise RuntimeError("CHANGED_TEST_FILE_HAS_NO_GO_TESTS")
        package = "./" + str(Path(path).parent)
        out[path] = {"change": kind, "package": package, "source_blob": blob(raw),
                     "source_sha256": sha(raw), "test_names": names}
    return changed, out

def execute_package(label, dir_name, repo, names=None):
    # Only directories derived from actual source changes, not configured names.
    args = ["go", "test", "-count=1", "-timeout=120s", "-v"]
    if names:
        args += ["-run", "^(" + "|".join(re.escape(n) for n in names) + ")$"]
    args.append(dir_name)
    return run(label, args, cwd=repo, valid=(0, 1), timeout=225)

def main():
    state = {
        "schema": "mathgraph.source-native-go-consequence-replay.v1",
        "status": "UNKNOWN", "error": None,
        "source": {"repository": SOURCE_REPOSITORY,
                   "base": BASE, "contributor_head": HEAD},
        "toolchain": {}, "changes": None, "source_derived_tests": None,
        "package_results": {}, "ablation": {}, "steps": LOGS,
        "claim_boundaries": [
            "original contributor-authored tests and repairs; not MathGraph-generated",
            "mechanical source-derived test selection; not arbitrary Go grammar",
            "package failure is not by itself two-backend same-input disagreement",
            "source-disclosed defect is not blind discovery",
            "equal-information full reviewer baseline has original PR description",
            "no manual PR-context semantic glue; no L7 or new generator language",
            "no outside-org Check publish; no production claims"
        ],
    }
    try:
        for cmd in ["git", "go", "node"]:
            opt = "--version" if cmd != "go" else "version"
            _, version = run("tool_" + cmd, [cmd, opt])
            state["toolchain"][cmd] = version.strip()
        src = initialize()
        changed, tests = source_discovery(src)
        state["changes"] = changed
        state["source_derived_tests"] = tests
        by_package = {}
        for info in tests.values():
            by_package.setdefault(info["package"], set()).update(info["test_names"])
        old = ROOT / "base"
        newer = ROOT / "head"
        # Each package is tested *before* its authored new tests are transplanted,
        # with test name entrypoints discovered from source.
        for ix, (package, names) in enumerate(sorted(by_package.items())):
            short = "pkg_" + str(ix)
            old_code, old_out = execute_package(short + "_original_base", package, old)
            head_code, head_out = execute_package(short + "_author_head", package, newer, names)
            if old_code != 0:
                raise RuntimeError("ORIGINAL_BASE_PACKAGE_NOT_GREEN_" + short)
            if head_code != 0:
                raise RuntimeError("CONTRIBUTOR_HEAD_NATIVE_TEST_FAILED_" + short)
            state["package_results"][package] = {
                "names": sorted(names),
                "original_base_exit": old_code, "contributor_head_exit": head_code,
                "copied_original_source_tests": [],
                "source_test_injection_exit": None,
                "witness_test_failures": [],
                "causal_restoration_exit": None
            }
        # Transplant ONLY original contributor test-source changes to the old
        # implementation. No patched implementation or target-specific literals.
        for path, info in sorted(tests.items()):
            src_path = newer / path
            target = old / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if info["change"] == "A" and target.exists():
                raise RuntimeError("NEW_TEST_NOT_ABSENT_FROM_BASE")
            if info["change"] == "M" and not target.exists():
                raise RuntimeError("MODIFIED_TEST_MISSING_IN_BASE")
            shutil.copyfile(src_path, target)
            if blob(target.read_bytes()) != info["source_blob"]:
                raise RuntimeError("TEST_TRANSPLANT_CHANGED_BYTES")
            state["package_results"][info["package"]]["copied_original_source_tests"].append(path)
        detected = 0
        for ix, (package, names) in enumerate(sorted(by_package.items())):
            short = "pkg_" + str(ix)
            code, output = execute_package(short + "_base_with_original_new_tests",
                                           package, old, names)
            names_failed = sorted(set(
                re.findall(r"(?m)^\s*--- FAIL: (Test[A-Za-z0-9_]+)", output)))
            legitimate = sorted(set(names_failed) & set(names))
            record = state["package_results"][package]
            record["source_test_injection_exit"] = code
            record["witness_test_failures"] = legitimate
            # Fail closed on general infrastructure errors misread as a witness.
            if code == 1 and not legitimate:
                raise RuntimeError("UNATTRIBUTED_TEST_FAILURE_" + short)
            if code == 1:
                detected += 1
        if detected == 0:
            raise RuntimeError("NO_SOURCE_NATIVE_REGRESSION_DISCOVERED")
        # Reverse test-only change and rerun original base to check whether the
        # newly injected original tests caused the observed red.
        for path, info in sorted(tests.items()):
            target = old / path
            if info["change"] == "A":
                target.unlink()
            else:
                _, old_version = run(
                    "original_tree_recover_" + path.replace("/", "_").replace(".", "_"),
                    ["git", "show", BASE + ":" + path], cwd=src)
                target.write_bytes(old_version.encode("utf-8"))
        for ix, package in enumerate(sorted(by_package)):
            code, _ = execute_package("pkg_" + str(ix) + "_test_ablation_recovered",
                                      package, old)
            state["package_results"][package]["causal_restoration_exit"] = code
            if code != 0:
                raise RuntimeError("TEST_ABLATION_DID_NOT_RECOVER_BASE")
        # Claims are deliberately scoped to Go test entrypoint differential,
        # not end-to-end runtime equality of identical inputs across backends.
        state["status"] = "WARRANTED_BOUNDED_SOURCE_DERIVED_NATIVE_TEST_CONTRAST"
        state["source_novel_semantic_discovery"] = "NOT_ESTABLISHED"
        state["shared_input_backend_disagreement"] = "NOT_ESTABLISHED"
        state["actual_author_test_regression_packages"] = detected
        state["operator_generalizes_to_OPA"] = "NOT_ESTABLISHED"
    except Exception as error:
        state["error"] = str(error)
    finally:
        (EVIDENCE / "report.json").write_text(
            json.dumps(state, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print("FINAL", json.dumps({"status": state["status"],
                                  "error": state["error"],
                                  "packages": state["package_results"],
                                  "original_source": state["source"]},
                                  sort_keys=True), flush=True)
    return 0 if state["status"] == "WARRANTED_BOUNDED_SOURCE_DERIVED_NATIVE_TEST_CONTRAST" else 1

if __name__ == "__main__":
    sys.exit(main())
