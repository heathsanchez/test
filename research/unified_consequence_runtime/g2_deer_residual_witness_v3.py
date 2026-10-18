#!/usr/bin/env python3
"""Retrospective source-neutral selection by ORIGINAL protected failure witness.

Never changes original admitted methods: only filters syntax-eligible edits
using their own original compiled pattern, the native-failing literal test
case and a directly observed .match() call in authenticated source. No
candidate-native outcomes are consulted. Deer-flow is EXPOSED, not new G2.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from . import g2_deer_import_composition_v2 as parent

ROOT=Path(__file__).resolve().parents[2]
U="research/unified_consequence_runtime/"
PREQUERY=U+"G2_DEER_RESIDUAL_WITNESS_V3_PRE_NATIVE.json"
PREQUERY_COMMIT="8668a7621533254e9ae939ba6266438bf1ba4057"
V2_HEAD="45f5b07cde363d9716a76e94c2fdcdb50f8c094e"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def frozen():
    original=subprocess.check_output(["git","-C",str(ROOT),"show",
                           PREQUERY_COMMIT+":"+PREQUERY],timeout=45)
    if (ROOT/PREQUERY).read_bytes()!=original:
        raise ValueError("UNKNOWN_CHANGED_PRENATIVE_RESIDUAL_DISCRIMINATOR")
    protocol=json.loads(original)
    if (protocol["schema"]!="G2_EXPOSED_SOURCE_NEUTRAL_RESIDUAL_WITNESS_SELECTOR_V3"
            or protocol["parent_v2_run"]!=39166845563
            or protocol["status"]!="FROZEN_BEFORE_ANY_NEW_CANDIDATE_NATIVE_RUN"
            or protocol["parent_v2_original_proof_commit"]!=V2_HEAD):
        raise ValueError("UNKNOWN_RESIDUAL_FREEZE_SCOPE")
    path=U+"g2_deer_import_composition_v2.py"
    if (ROOT/path).read_bytes()!=subprocess.check_output(
            ["git","-C",str(ROOT),"show",V2_HEAD+":"+path],timeout=50):
        raise ValueError("UNKNOWN_ORIGINAL_V2_METHOD_BYTES_CHANGED")
    return protocol


def _test_node(tree,selector):
    _,classes,func=parent._parts(selector)
    nodes=tree.body
    for cl in classes:
        found=[x for x in nodes if isinstance(x,ast.ClassDef) and x.name==cl]
        if len(found)!=1:return None
        nodes=found[0].body
    matches=[x for x in nodes if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name==func]
    return matches[0] if len(matches)==1 else None


def _literal_param_values(fn):
    pairs=[]
    for d in fn.decorator_list:
        if (not isinstance(d,ast.Call) or not isinstance(d.func,ast.Attribute)
                or d.func.attr!="parametrize" or len(d.args)<2):
            continue
        try:
            names=ast.literal_eval(d.args[0])
        except (ValueError,TypeError,MemoryError):
            continue
        if not isinstance(names,str) or "," in names or " " in names.strip():
            continue
        try:
            values=ast.literal_eval(d.args[1])
        except (ValueError,TypeError,MemoryError):
            continue
        if isinstance(values,(list,tuple)) and values and all(isinstance(v,str) for v in values):
            pairs.extend(values)
    return sorted(set(pairs))


def source_neutral_residuals(head_test,selectors,original_native):
    """Join exact original author literal param values to original failing JUnit case."""
    if not isinstance(head_test,bytes) or not original_native:
        raise ValueError("UNKNOWN_NO_AUTHENTIC_ORIGINAL_PARAM_RESIDUAL")
    tree=ast.parse(head_test)
    if not any(x=="FAIL" for x in original_native.values()):
        raise ValueError("UNKNOWN_NO_ACTUAL_PROTECTED_NATIVE_FAILURE")
    found=set();used=set()
    for selector in selectors:
        node=_test_node(tree,selector)
        if node is None:raise ValueError("UNKNOWN_DECLARED_ORIGINAL_TEST_AST_NODE")
        module,classes,name=parent._parts(selector)
        expected=module+("."+".".join(classes) if classes else "")+"::"+name
        literals=_literal_param_values(node)
        actual=[(k,v) for k,v in original_native.items()
                if k.startswith(expected+"[") and k.endswith("]")]
        for key,state in actual:
            if state!="FAIL":continue
            suffix=key[len(expected)+1:-1]
            matching=[v for v in literals if repr(v)[1:-1]==suffix]
            if len(matching)!=1:
                raise ValueError("UNKNOWN_PROTECTED_JUNIT_CASE_LITERAL_NOT_SOURCE_BOUND")
            found.add(matching[0]);used.add(key)
    if len(used)!=sum(x=="FAIL" for x in original_native.values()) or not found:
        raise ValueError("UNKNOWN_INCOMPLETE_ORIGINAL_FAILURE_OBSERVATION")
    return sorted(found)


def _pattern_uses_match(tree,raw_candidate):
    """Return True only if a named original re.compile literal drives .match()."""
    for assign in ast.walk(tree):
        if not isinstance(assign,(ast.Assign,ast.AnnAssign)):continue
        call=assign.value
        if not (isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute)
                and isinstance(call.func.value,ast.Name)
                and call.func.value.id=="re" and call.func.attr=="compile"
                and call.args and isinstance(call.args[0],ast.Constant)
                and call.args[0].lineno==raw_candidate["line"]):
            continue
        literal=ast.get_source_segment(raw_candidate["_original_source"],call.args[0])
        if literal!=raw_candidate["old"]:
            continue
        targets=assign.targets if isinstance(assign,ast.Assign) else [assign.target]
        names={v.id for v in targets if isinstance(v,ast.Name)}
        if any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
               and n.func.attr=="match" and isinstance(n.func.value,ast.Name)
               and n.func.value.id in names for n in ast.walk(tree)):
            return True
    return False


def filter_by_native_original_witnesses(originals,catalog,witnesses):
    if not witnesses:
        return [],[]
    selected=[];evidence=[]
    for c in catalog:
        source=originals[c["path"]].decode("utf-8")
        tree=ast.parse(source)
        candidate={**c,"_original_source":source}
        uses=_pattern_uses_match(tree,candidate)
        discriminates=False
        if uses:
            try:
                old=ast.literal_eval(c["old"])
                new=ast.literal_eval(c["new"])
                if isinstance(old,str) and isinstance(new,str):
                    before=re.compile(old);after=re.compile(new)
                    discriminates=any(
                        before.match(w) is not None and after.match(w) is None
                        for w in witnesses if isinstance(w,str))
            except (re.error,ValueError,TypeError,SyntaxError):
                discriminates=False
        evidence.append({"path":c["path"],"line":c["line"],
                         "original_source_sha256":c["original_source_sha256"],
                         "candidate_sha256":c["candidate_sha256"],
                         "source_bound_match_call":uses,
                         "separates_original_failing_literal":discriminates,
                         "candidate_original_family":c["family"]})
        if uses and discriminates:
            selected.append(c)
    return selected,evidence


def main(output):
    output=Path(output).absolute()
    if output.exists():
        raise ValueError("UNKNOWN_EVIDENCE_OUTPUT_NOT_FRESH")
    frozen()
    original_catalog=parent.source_catalog
    filter_called=[False]

    def source_only_with_original_failure(originals,imported):
        if filter_called[0]:
            raise ValueError("UNKNOWN_REPLAYED_OR_OUTCOME_CONDITIONED_FILTER")
        filter_called[0]=True
        old=original_catalog(originals,imported)
        admitted=json.loads((output/"source-owned-native-original/RESULT.json").read_text())
        baseline_junit=(output/"source-owned-native-original/native.xml").read_bytes()
        head_test=(Path(admitted["work_dir"])/
                   parent.frozen()["original"]["test"]).read_bytes()
        original_cases=parent.parse_native_cases(baseline_junit,admitted["protected_nodes"])
        observations=source_neutral_residuals(head_test,admitted["protected_nodes"],original_cases)
        chosen,evidence=filter_by_native_original_witnesses(originals,old,observations)
        # Check every emitted edit is literally a candidate of the frozen
        # source-neutral original. No human-inserted winning source.
        if any(x not in old for x in chosen):
            raise ValueError("UNKNOWN_NEW_UNQUALIFIED_REPAIR_GRAMMAR")
        (output/"V3_RESIDUAL_SELECTION_BEFORE_CANDIDATE_NATIVE.json").write_text(
           json.dumps({"status":"SOURCE_ONLY_ORIGINAL_FAILURE_DISCRIMINATOR",
              "science":"EXPOSED_ONLY_NOT_G2",
              "native_candidate_test_executed":False,
              "original_failure_witness_sha256":[sha(v.encode()) for v in observations],
              "old_candidate_count":len(old),"selected_count":len(chosen),
              "candidate_audit":evidence,
              "selected_source_sha256":[x["candidate_sha256"] for x in chosen]
             },sort_keys=True,indent=2)+"\n")
        return chosen

    parent.source_catalog=source_only_with_original_failure
    try:
        result=parent.main(output)
    finally:
        parent.source_catalog=original_catalog
    return result


if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: python -m research.unified_consequence_runtime.g2_deer_residual_witness_v3 FRESH_OUTPUT")
    report=main(Path(sys.argv[1]))
    print("G2_EXPOSED_RESIDUAL_METHOD",report["status"],"G2",report["G2"])
