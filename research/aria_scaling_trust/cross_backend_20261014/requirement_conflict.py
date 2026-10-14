#!/usr/bin/env python3
"""Source-derived protected-go-test conflict inspector across immutable PR trees.

No test names, runtime values, or backend-specific semantics are configured.
The original PR source diff nominates packages and touched test functions.
An unchanged old Go test failing on the author head is independently retained.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

import source_native_contrast as base

EVIDENCE = base.EVIDENCE
GO_FUNC = re.compile(r"(?m)^func\s+(Test[A-Za-z0-9_]+)\s*\(\s*t\s+\*testing\.T\s*\)")
HUNKS = re.compile(r"(?m)^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
SOURCE_SCOPE = "SOURCE_ORIGINAL_CONTRIBUTOR_TESTS"
STEPS = base.LOGS

def native_failures(output):
    return sorted(set(re.findall(r"(?m)^\s*--- FAIL: (Test[A-Za-z0-9_]+)", output)))

def individual_test_bodies(raw):
    """Extract entire top-level Test functions, including context up to next func."""
    lines = raw.decode("utf-8").splitlines(keepends=True)
    boundaries = [(i, m.group(1)) for i,line in enumerate(lines)
                  if (m := GO_FUNC.match(line))]
    # Other top-level func declarations limit the previous Test body.
    tops = [i for i,line in enumerate(lines)
            if re.match(r"^func\s+[A-Za-z_]", line)]
    output = {}
    for i, name in boundaries:
        nxt = next((x for x in tops if x>i),len(lines))
        output[name] = "".join(lines[i:nxt])
    return output

def hunk_selected_names(src, path, original):
    _, diff = base.run("hunks_" + path.replace("/","_").replace(".","_"),
                       ["git", "diff", "--unified=0", base.BASE,base.HEAD,"--",path],
                       cwd=src)
    lines = original.decode().splitlines()
    starts = [(i,m.group(1)) for i,line in enumerate(lines,1)
              if (m := GO_FUNC.match(line))]
    if not starts:
        raise RuntimeError("NO_GO_TEST_ENTRYPOINTS")
    found = set()
    for match in HUNKS.finditer(diff):
        new_line = int(match.group(1))
        # Map source edit to the closest enclosing existing Test declaration.
        nearest = [name for i,name in starts if i<=new_line]
        if nearest:
            found.add(nearest[-1])
    return sorted(found)

def main():
    evidence = {
        "schema":"mathgraph.source-native-protected-go-test-conflict.v1",
        "status":"UNKNOWN",
        "error":None,
        "source":{"repository":base.SOURCE_REPOSITORY,
                  "original_base":base.BASE,"contributor_head":base.HEAD},
        "selection":"all exact PR-added Go Test declarations and touched test declarations",
        "source_tests":{},
        "native_package_results":{},
        "unchanged_old_tests_failing_at_contributor_head":{},
        "steps":STEPS,
        "limitations":[
            "author tests and bug description public before this experiment",
            "no new code fix generated, no anonymous human reviewer study",
            "test output failure localizes source-invariant conflict, not all backend inputs",
            "source-mined Go test selector not yet portable to OPA C/YAML test language",
            "no proof of automatic generator grammar synthesis or general semantic parity",
            "no present-day main-branch bug asserted from historical PR-head test",
            "no outside organization installation or upstream code write"]
    }
    try:
        for exe, argv in [("git",["git","--version"]),
                          ("go",["go","version"]),("node",["node","--version"])]:
            base.run("check_" + exe,argv)
        src = base.initialize()
        changes,tests = base.source_discovery(src)
        old, newer=base.ROOT/"base",base.ROOT/"head"
        package_names = {}
        files_by_package = {}
        for path, meta in sorted(tests.items()):
            raw=(newer/path).read_bytes()
            if meta["change"]=="A":
                names=meta["test_names"]
            else:
                names=hunk_selected_names(src,path,raw)
            if not names:
                raise RuntimeError("TOUCHED_TEST_FUNCTION_NOT_DISCOVERED")
            evidence["source_tests"][path]={**meta,
                "selected_touched_tests":names}
            package_names.setdefault(meta["package"],set()).update(names)
            files_by_package.setdefault(meta["package"],[]).append(path)
        for ix,(pkg,names) in enumerate(sorted(package_names.items())):
            label="part_"+str(ix)
            old_code,old_out=base.execute_package(label+"_original_base_all",pkg,old)
            selected_code,selected_out=base.execute_package(
                label+"_head_touched",pkg,newer,names)
            full_code,full_out=base.execute_package(label+"_head_all",pkg,newer)
            rec={"package":pkg,"selected_tests":sorted(names),
                 "source_test_files":files_by_package[pkg],
                 "original_base_suite_exit":old_code,
                 "head_touched_tests_exit":selected_code,
                 "head_full_suite_exit":full_code,
                 "head_full_failed_tests":native_failures(full_out)}
            evidence["native_package_results"][pkg]=rec
            if old_code!=0:
                raise RuntimeError("ORIGINAL_BASE_NATIVE_PACKAGE_RED_"+label)
            if selected_code!=0:
                raise RuntimeError("CONTRIBUTOR_TOUCHED_TESTS_RED_"+label)
            if full_code and not rec["head_full_failed_tests"]:
                raise RuntimeError("HEAD_PACKAGE_INFRA_FAILURE_NOT_SEMANTIC_"+label)
            # Compare untouched historical tests that remained byte-identical
            # but became red under the contributor's changed implementation.
            conflicts=[]
            for failed in rec["head_full_failed_tests"]:
                for source_file in sorted((newer/Path(pkg[2:])).glob("*_test.go")):
                    original_file=old / source_file.relative_to(newer)
                    if not original_file.exists():
                        continue
                    old_tests=individual_test_bodies(original_file.read_bytes())
                    new_tests=individual_test_bodies(source_file.read_bytes())
                    if (failed in old_tests and failed in new_tests
                        and old_tests[failed] == new_tests[failed]
                        and failed not in names):
                        conflicts.append({
                            "test":failed,
                            "original_source":str(source_file.relative_to(newer)),
                            "exact_test_body_sha256":base.sha(old_tests[failed].encode()),
                            "original_test_body_unchanged":True,
                            "base_package": "PASS",
                            "contributor_head_package":"FAIL"
                        })
            if conflicts:
                evidence["unchanged_old_tests_failing_at_contributor_head"][pkg]=conflicts
        # Independent protected-future ablation: suppress ONLY unchanged
        # older test entrypoint in an ephemeral copy of the author head.
        # Retain and restore its exact original bytes. No implementation edit.
        for ix, (pkg, conflicts) in enumerate(sorted(
                evidence["unchanged_old_tests_failing_at_contributor_head"].items())):
            original_files = {}
            for entry in conflicts:
                rel = entry["original_source"]
                target = newer / rel
                if rel not in original_files:
                    original_files[rel] = target.read_bytes()
                current = target.read_bytes()
                functions = individual_test_bodies(current)
                test_name = entry["test"]
                if test_name not in functions:
                    raise RuntimeError("ABLATION_ORIGINAL_TEST_MISSING")
                body = functions[test_name].encode("utf-8")
                if base.sha(body) != entry["exact_test_body_sha256"] or current.count(body) != 1:
                    raise RuntimeError("ABLATION_PROTECTED_BODY_NOT_PINNED")
                stub = ("func " + test_name +
                        '(t *testing.T) { t.Skip("PROTECTED_TEST_ABLATED") }\\n').encode()
                target.write_bytes(current.replace(body, stub, 1))
            label = "protected_"+str(ix)
            ablated_code, ablated_output = base.execute_package(
                label+"_head_only_old_failing_test_ablated",pkg,newer)
            for rel, raw in original_files.items():
                (newer/rel).write_bytes(raw)
                if (newer/rel).read_bytes()!=raw:
                    raise RuntimeError("ABLATION_COULD_NOT_RESTORE_EXACT_HEAD_TEST")
            rec = evidence["native_package_results"][pkg]
            rec["head_with_only_conflicting_old_test_ablated_exit"]=ablated_code
            rec["head_ablation_scope"]=sorted(entry["test"] for entry in conflicts)
            if ablated_code:
                raise RuntimeError("REMOVING_ONLY_PROTECTED_TEST_DID_NOT_RECOVER_HEAD")
            if "PROTECTED_TEST_ABLATED" not in ablated_output:
                raise RuntimeError("ABLATED_TEST_NOT_OBSERVED_SKIPPED")
            restored_code, restored_output = base.execute_package(
                label+"_head_original_failing_test_restored",pkg,newer)
            rec["head_reinstated_old_test_exit"]=restored_code
            if (restored_code != 1 or
                not set(native_failures(restored_output)) >=
                  set(entry["test"] for entry in conflicts)):
                raise RuntimeError("RESTORING_PROTECTED_TEST_DID_NOT_REOPEN_CONFLICT")
        # Copy ONLY contributor Go test changes into ORIGINAL implementation.
        for path, meta in sorted(tests.items()):
            target=old/path
            if meta["change"]=="A" and target.exists():
                raise RuntimeError("NEW_TEST_ALREADY_PRESENT_IN_ORIGINAL")
            if meta["change"]=="M" and not target.exists():
                raise RuntimeError("MODIFIED_TEST_ABSENT_IN_ORIGINAL")
            shutil.copyfile(newer/path,target)
            if base.blob(target.read_bytes())!=meta["source_blob"]:
                raise RuntimeError("INJECTED_TEST_BYTES_NOT_ORIGINAL")
        introduced_regressions=0
        for ix,(pkg,names) in enumerate(sorted(package_names.items())):
            rec=evidence["native_package_results"][pkg]
            code,output=base.execute_package(
                "part_"+str(ix)+"_base_original_plus_head_tests",
                pkg,old,names)
            failing=native_failures(output)
            rec["base_with_head_touched_test_exit"]=code
            rec["base_newly_failing_original_tests"]=failing
            if code!=0 and not set(failing)&set(names):
                raise RuntimeError("BASE_TEST_REPLAY_NO_SCOPED_TEST_FAILURE_"+str(ix))
            if code!=0:
                introduced_regressions+=1
        # Exact plan-level test deletion ablation: restore original test files,
        # then require the unmodified old package to pass again.
        for path, meta in sorted(tests.items()):
            target=old/path
            if meta["change"]=="A":
                target.unlink()
            else:
                original=base.run(
                    "restore_test_"+path.replace("/","_").replace(".","_"),
                    ["git","show",base.BASE+":"+path],cwd=src)[1]
                target.write_text(original)
                git_blob=base.run(
                    "original_blob_"+path.replace("/","_").replace(".","_"),
                    ["git","ls-tree",base.BASE,path],cwd=src)[1]
                if base.blob(target.read_bytes()) not in git_blob:
                    raise RuntimeError("ORIGINAL_TEST_RESTORE_IDENTITY_FAIL")
        for ix,pkg in enumerate(sorted(package_names)):
            restored,output=base.execute_package(
                "part_"+str(ix)+"_old_restored_after_ablation",pkg,old)
            evidence["native_package_results"][pkg]["ablation_recovered_exit"]=restored
            if restored:
                raise RuntimeError("TEST_DELETION_ABLATION_DID_NOT_RECOVER_"+str(ix))
        evidence["changed_native_packages_with_new_failing_test"]=introduced_regressions
        conflicts=evidence["unchanged_old_tests_failing_at_contributor_head"]
        if not conflicts:
            evidence["status"]="WARRANTED_BOUNDED_TEST_REPLAY_WITH_NO_PROTECTED_CONFLICT"
        elif introduced_regressions:
            evidence["status"]="WARRANTED_BOUNDED_ORIGINAL_TEST_CONTRACT_CONFLICT"
        else:
            raise RuntimeError("HEAD_OLD_TEST_REGRESSION_WITHOUT_SOURCE_CAUSAL_COUNTERFACTUAL")
        evidence["general_cross_runtime_same_input_witness"]="NOT_ESTABLISHED"
        evidence["reviewer_advantage_vs_equal_information_baseline"]="NOT_MEASURED"
    except Exception as exc:
        evidence["error"]=str(exc)
    finally:
        (EVIDENCE/"protected_conflict_report.json").write_text(
            json.dumps(evidence,indent=2,sort_keys=True)+"\n")
        print("PROTECTED_FINAL",json.dumps({
            "status":evidence["status"],"error":evidence["error"],
            "conflicts":evidence["unchanged_old_tests_failing_at_contributor_head"],
            "packages":evidence["native_package_results"]},sort_keys=True),flush=True)
    return 0 if evidence["status"].startswith("WARRANTED_BOUNDED_") else 1

if __name__=="__main__":
    sys.exit(main())
