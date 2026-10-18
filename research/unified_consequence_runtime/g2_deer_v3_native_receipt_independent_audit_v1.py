#!/usr/bin/env python3
"""Independent stdlib-only source/JUnit/mask audit of original exposed V3 evidence.

Runs no repaired source or test. Independently fetches immutable ORIGINAL base
and author HEAD test Git blobs, reconstructs strict-terminal substitutions, and
checks all native-reported JUnit consequences. Does not import the experimental
V2/V3 executors, learned method, or source-specific repair implementations.
"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/"research/unified_consequence_runtime/G2_DEER_V3_INDEPENDENT_AUDIT_MANIFEST.json"
SHA_40=re.compile(r"[0-9a-f]{40}\Z")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def git(work,*args,raw=False):
    done=subprocess.run(["git","-C",str(work),"--no-replace-objects",*args],
                        text=not raw,capture_output=True,timeout=90,check=True)
    return done.stdout if raw else done.stdout.strip()


def base_sources(plan,manifest):
    """Immutable public original Git: HEAD test blob only, NO author fixed production."""
    with tempfile.TemporaryDirectory(prefix="g2-deer-independent-original-") as d:
        work=Path(d)
        git(work,"init","-q")
        git(work,"remote","add","original","https://github.com/"+manifest["original_repository"]+".git")
        for sha in (manifest["original_base"],manifest["original_head_author_test"]):
            git(work,"fetch","-q","--depth=1","--filter=blob:none",
                "--no-tags","original",sha)
        paths=set(plan["original_source_sha256"])
        result={}
        for path in sorted(paths):
            if (path.startswith("/") or ".." in path.split("/") or
                "\\" in path or "\x00" in path or not path.startswith("backend/") or
                not path.endswith(".py")):
                raise ValueError("UNTRUSTED_GIT_SOURCE_PATH")
            blob=git(work,"show",manifest["original_base"]+":"+path,raw=True)
            if digest(blob)!=plan["original_source_sha256"][path]:
                raise ValueError("ORIGINAL_GIT_SOURCE_BLOB_NOT_IDENTITY_MATCH")
            mode=git(work,"ls-tree",manifest["original_base"],"--",path).split()[0]
            if mode not in ("100644","100755"):
                raise ValueError("UNSUPPORTED_ORIGINAL_GIT_SOURCE_MODE")
            result[path]=blob
        test=git(work,"show",manifest["original_head_author_test"]+":"+
                 manifest["original_author_test"],raw=True)
        if digest(test)!=manifest["original_author_test_sha256"]:
            raise ValueError("ORIGINAL_AUTHOR_TEST_SOURCE_INTEGRITY")
        return result,test


def strict_anchor_original_reconstruction(original,row):
    """Independent exact one-literal Python AST edit, not producer's generator."""
    s=original.decode("utf-8")
    tree=ast.parse(s)
    lines=s.splitlines(keepends=True)
    matches=[]
    for call in ast.walk(tree):
        if not (isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute)
                and isinstance(call.func.value,ast.Name)
                and call.func.value.id=="re" and call.func.attr=="compile"
                and call.args and isinstance(call.args[0],ast.Constant)):
            continue
        item=call.args[0]
        if item.lineno!=row["line"]:continue
        text=ast.get_source_segment(s,item)
        if not (text and len(text)>4 and text[0] in "rR"
                and text[1] in "'\"" and text[-1]==text[1]
                and text[-2]=="$"):
            continue
        start=sum(len(x) for x in lines[:item.lineno-1])+item.col_offset
        end=sum(len(x) for x in lines[:item.end_lineno-1])+item.end_col_offset
        new=text[:-2]+r"\Z"+text[-1]
        repaired=(s[:start]+new+s[end:]).encode("utf-8")
        ast.parse(repaired)
        if digest(repaired)==row["candidate_sha256"]:
            matches.append((repaired,ast.literal_eval(text),ast.literal_eval(new),tree))
    if len(matches)!=1:
        raise ValueError("UNQUALIFIED_SOURCE_NEUTRAL_CANDIDATE_IDENTITY")
    return matches[0]


def pre_native_selection_audit(originals,original_test,result,pre):
    rows=pre["candidate_audit"]
    kept=[r for r in rows if r["source_bound_match_call"]
                             and r["separates_original_failing_literal"]]
    selected=result["source_candidates"]
    if len(rows)!=6 or len(kept)!=len(selected)!=2:
        raise ValueError("SOURCE_ONLY_FILTER_SIZE_OR_TYPE")
    if [r["candidate_sha256"] for r in kept]!=[r["candidate_sha256"] for r in selected]:
        raise ValueError("POST_NATIVE_RETARGETED_WINNING_CANDIDATES")
    # Binding to a true failing ORIGINAL parametrized string case, not an
    # unconstrained hand-supplied filename or winning source location.
    tree=ast.parse(original_test)
    literal_strings=set()
    for node in ast.walk(tree):
        if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
        for dec in node.decorator_list:
            if not (isinstance(dec,ast.Call) and isinstance(dec.func,ast.Attribute)
                    and dec.func.attr=="parametrize" and len(dec.args)>=2):
                continue
            try:
                values=ast.literal_eval(dec.args[1])
            except (ValueError,TypeError):continue
            if isinstance(values,(tuple,list)):
                literal_strings.update(s for s in values if isinstance(s,str))
    baseline=set(k for k,v in result["original_vector"].items() if v=="FAIL")
    witnessed=[s for s in literal_strings if
               digest(s.encode()) in pre["original_failure_witness_sha256"]
               and all(repr(s)[1:-1] in k for k in baseline)]
    if len(witnessed)!=1:
        raise ValueError("ORIGINAL_PROTECTED_RESIDUAL_WITNESS_NOT_SOURCE_BOUND")
    witness=witnessed[0]
    if pre["old_candidate_count"]!=len(rows) or pre["selected_count"]!=2:
        raise ValueError("CANDIDATE_FILTER_WRONG_ORIGINAL_SCOPE")
    for item in rows:
        path=item["path"]
        if path not in originals or digest(originals[path])!=item["original_source_sha256"]:
            raise ValueError("CANDIDATE_ORIGINAL_GIT_SOURCE_MISMATCH")
        _,before,after,tree=strict_anchor_original_reconstruction(originals[path],item)
        # The only licensed use is an exact variable assigned re.compile that
        # is used at source-call AST .match, not an inert .fullmatch site.
        used=False
        for ass in ast.walk(tree):
            if not isinstance(ass,(ast.Assign,ast.AnnAssign)):continue
            call=ass.value
            if not (isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute)
                    and isinstance(call.func.value,ast.Name)
                    and call.func.value.id=="re" and call.func.attr=="compile"
                    and call.args and isinstance(call.args[0],ast.Constant)
                    and call.args[0].lineno==item["line"]):
                continue
            names={n.id for n in (ass.targets if isinstance(ass,ast.Assign) else [ass.target])
                   if isinstance(n,ast.Name)}
            if any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
                   and n.func.attr=="match" and isinstance(n.func.value,ast.Name)
                   and n.func.value.id in names for n in ast.walk(tree)):
                used=True
        differential=used and re.compile(before).match(witness) is not None and re.compile(after).match(witness) is None
        if used!=item["source_bound_match_call"] or differential!=item["separates_original_failing_literal"]:
            raise ValueError("SOURCE_NEUTRAL_FILTER_NOT_REPLAYABLE")
    return {"original_syntactic_candidates":len(rows),"witness_sha256":digest(witness.encode()),
            "pre_native_selected_candidates":len(kept),
            "native_outcome_used_for_candidate_selection":False}


def parse_xml(raw):
    root=ET.fromstring(raw)
    cases=list(root.iter("testcase"))
    if not cases:raise ValueError("EMPTY_TEST_COLLECTION")
    states={}
    for node in cases:
        classname=node.attrib.get("classname","")
        name=node.attrib.get("name","")
        if not classname or not name:
            raise ValueError("MISSING_JUNIT_CASE_ID")
        key=classname+"::"+name
        if key in states:raise ValueError("DUPLICATE_JUNIT_PARAM_CASE")
        tags={c.tag for c in node}
        if "error" in tags or "skipped" in tags or not tags<=set(("failure",)):
            raise ValueError("UNKNOWN_NON_EXECUTED_OR_ERROR_JUNIT")
        states[key]="FAIL" if "failure" in tags else "PASS"
    return dict(sorted(states.items()))


def receipt(folder,label,source,protected_names):
    target=folder/(label+".xml")
    raw=target.read_bytes()
    got=parse_xml(raw)
    if source["junit_sha256"]!=digest(raw):
        raise ValueError("UNTRUSTED_NATIVE_JUNIT_HASH:"+label)
    if source["vector"]!=got or set(got)!=set(protected_names):
        raise ValueError("NATIVE_PARAMETRIZED_CASE_IDENTITY_CHANGED:"+label)
    c=source["counts"]
    fails=sum(x=="FAIL" for x in got.values())
    if c!={"tests":len(got),"failures":fails,"errors":0,"skipped":0}:
        raise ValueError("JUNIT_COUNTS_AND_NATIVE_RECEIPT_DISAGREE:"+label)
    if source["returncode"]!=(0 if not fails else 1):
        raise ValueError("NATIVE_EXIT_AND_JUNIT_DISAGREE:"+label)
    for ext in ("stdout","stderr"):
        data=(folder/(label+"."+ext)).read_bytes()
        if digest(data)!=source[ext+"_sha256"]:
            raise ValueError("NATIVE_"+ext+"_HASH_MISMATCH:"+label)
    return got


def audit(folder):
    manifest=json.loads(MANIFEST.read_text())
    result=json.loads((folder/"RESULT.json").read_text())
    plan=json.loads((folder/"CANDIDATES_BEFORE_NATIVE.json").read_text())
    pre=json.loads((folder/"V3_RESIDUAL_SELECTION_BEFORE_CANDIDATE_NATIVE.json").read_text())
    verdict={"schema":"G2_DEER_V3_INDEPENDENT_BOUNDED_NATIVE_REPLAY_V1",
             "status":"UNKNOWN_NOT_QUALIFIED","G2":"UNKNOWN","G4":"UNKNOWN"}
    if (result["schema"]!="G2_EXPOSED_IMPORT_SCOPED_FINITE_MASK_NATIVE_V2"
            or result["status"]!="CANDIDATE_EXPOSED_NATIVE_IMPORT_COMPOSITION_AWAITING_INDEPENDENT_AUDIT"
            or result["science"]!="EXPOSED_ONLY_NOT_G2"
            or result["original_future_status"]!="OPENED_PRIOR_TO_THIS_EXPERIMENT"
            or any(result[x]!="UNKNOWN" for x in ("G2","G3","G4","G5","G6"))
            or any(result[x]!="NOT_EXECUTED" for x in ("Lean","CLC","FLASH","agent_comparator"))
            or result["native_calls"]!=10):
        raise ValueError("UNAUTHORIZED_SCIENCE_SCOPE_OR_NATIVE_BUDGET")
    orig,test=base_sources(plan,manifest)
    verdict["authenticated_original_files"]=len(orig)
    verdict["original_git_test_sha256"]=digest(test)
    verdict["candidate_filter"]=pre_native_selection_audit(orig,test,result,pre)
    candidates=result["source_candidates"]
    k=len(candidates)
    if k!=2 or len({c["path"] for c in candidates})!=2 or result["selected_mask"]!=3:
        raise ValueError("FINITE_TWO_SOURCE_CHANGE_NOT_WARRANTED")
    corrected={}
    for row in candidates:
        changed,old,new,_=strict_anchor_original_reconstruction(orig[row["path"]],row)
        corrected[row["path"]]=changed
        if row["family"]!="strict_terminal_anchor" or digest(changed)!=row["candidate_sha256"]:
            raise ValueError("UNQUALIFIED_OR_CHANGED_REGEX_OPERATOR")
    expected_source={mask:{p:digest((corrected[p] if p in corrected and mask&(1<<next(i for i,c in enumerate(candidates) if c["path"]==p)) else raw))
                            for p,raw in orig.items()} for mask in range(1<<k)}
    if set(int(x["mask"]) for x in plan["masks"])!=set(range(4)):
        raise ValueError("NO_PRENATIVE_COMPLETE_MASK_SCHEDULE")
    for x in plan["masks"]:
        if x["source_sha256"]!=expected_source[int(x["mask"])]:
            raise ValueError("MASK_SOURCE_SHA256_NOT_RECONSTRUCTED")
    baseline=parse_xml((folder/"source-owned-native-original/native.xml").read_bytes())
    if baseline!=result["original_vector"] or len(baseline)!=4 or list(baseline.values()).count("FAIL")!=2:
        raise ValueError("ORIGINAL_NATIVE_CASE_IDENTITY_NOT_AUTHENTIC")
    case_set=set(baseline)
    subsets={}
    for mask in range(4):
        row=result["masks"][str(mask)]
        if row["mask"]!=mask or row["source_sha256"]!=expected_source[mask]:
            raise ValueError("FINITELY_RECORDED_SOURCE_NOT_ORIGINAL_PROJECTION")
        subsets[mask]=receipt(folder,"mask-%02d"%mask,row["native"],case_set)
    if subsets[0]!=baseline or not all(x=="PASS" for x in subsets[3].values()):
        raise ValueError("FINITE_SOURCE_CLOSURE_NOT_EARNED")
    for a in subsets:
        for b in subsets:
            if a&b==a:
                if not {k for k,v in subsets[a].items() if v=="PASS"} <= {
                        k for k,v in subsets[b].items() if v=="PASS"}:
                    raise ValueError("NATIVE_SUBSET_PASS_SET_NOT_MONOTONE")
    if any(all(v=="PASS" for v in subsets[3^(1<<i)].values()) for i in (0,1)):
        raise ValueError("UNNECESSARY_EDIT_IN_RECORDED_CONSEQUENCE_QUOTIENT")
    for label,s in zip(("selected-repeat-a","selected-repeat-b"),result["protected_repeat"]):
        if any(v!="PASS" for v in receipt(folder,label,s,case_set).values()):
            raise ValueError("NATIVE_FINAL_NOT_REPEATABLE")
    removed=receipt(folder,"physical-all-withdrawal",result["withdrawal"],case_set)
    restored=receipt(folder,"physical-all-restoration",result["restoration"],case_set)
    if removed!=baseline or not all(v=="PASS" for v in restored.values()):
        raise ValueError("NATIVE_PHYSICAL_ABLATION_OR_RESTORATION_MISMATCH")
    full=(folder/"complete-author.xml").read_bytes()
    cases=parse_xml(full)
    if (digest(full)!=result["full_author"]["junit_sha256"] or
            len(cases)!=result["full_author"]["tests"] or len(cases)!=83
            or any(v!="PASS" for v in cases.values()) or
            result["full_author"]["returncode"]!=0 or
            any(result["full_author"][k] for k in ("failures","errors","skipped"))):
        raise ValueError("INDEPENDENT_FULL_AUTHOR_NATIVE_TEST_FAILED")
    if result["finite_lattice"]["selected_mask"]!=3 or (
         result["finite_lattice"]["fully_informed_ledger"]!="TIE_EQUAL_INFORMATION"):
        raise ValueError("INFORMED_LEDGER_ABLATION_UNWARRANTED")
    verdict.update(status="WARRANTED_BOUNDED_EXPOSED_IMPORT_DERIVED_NATIVE_FINITE_COMPOSITION",
                   native_case_count=4,
                   original_failed=2,full_author_passed=len(cases),
                   complete_native_subset_masks=4,original_native_cases_authentic=True,
                   causal_source_edits=2,qualified_original_git_sources=len(orig),
                   physical_withdrawal_restoration=True,
                   source_method_altered=False,
                   fully_informed_exhaustive_ledger="SAME_MINIMUM_CAUSAL_SOURCE_MASK_NO_UNIQUE_SELECTION_ADVANTAGE",
                   strong_agent="NOT_EXECUTED",
                   G2="UNKNOWN",G4="UNKNOWN",
                   proof_scope="EXPOSED_SOURCE_FINITE_NATIVE_AUTHOR_OBLIGATIONS_ONLY")
    return verdict


if __name__=="__main__":
    folder=Path(sys.argv[1]).resolve()
    result=audit(folder)
    destination=folder/"INDEPENDENT_AUDIT.json"
    if destination.exists():
        raise SystemExit("EXISTING_AUDIT_RECEIPT_REFUSED")
    destination.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ("status","G2","G4","complete_native_subset_masks",
              "causal_source_edits","full_author_passed")},sort_keys=True))
