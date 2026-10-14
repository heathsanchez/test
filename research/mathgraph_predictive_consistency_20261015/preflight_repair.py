#!/usr/bin/env python3
"""Type-directed preflight input normalization from source-derived protocols.

Human-designed typed meta-operator. It constructs patch INSTANCES, not a
self-invented operator grammar; see FROZEN_PREFLIGHT_REPAIR.md.
"""
from __future__ import annotations
import ast, collections.abc, hashlib, json, os, pathlib, re
import subprocess, sys, tempfile, time, difflib

HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import invariant_generator as gen
prior=gen.prior

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def find_method(source, subject):
    tree=ast.parse(source)
    matches=[]
    for cl in tree.body:
        if isinstance(cl,ast.ClassDef) and cl.name==subject["class"]:
            matches += [(cl,f) for f in cl.body
                        if isinstance(f,ast.FunctionDef)
                        and f.name==subject["method"]]
    if len(matches)!=1:
        raise ValueError("UNKNOWN_UNIQUE_CHANGED_METHOD")
    return matches[0]

def synthesize_preflight_patch(source, subject, protocol):
    owner,method=find_method(source,subject)
    if not method.body:
        raise ValueError("UNKNOWN_EMPTY_METHOD")
    args=method.args
    if not args.args:
        raise ValueError("UNKNOWN_NO_RECEIVER")
    recv=args.args[0].arg
    # Entirely typed by the public Python collection contract,
    # AST binding shapes and external iterable interface.
    if protocol=="mapping" and args.vararg is not None:
        a=args.vararg.arg
        body=[
            "if "+a+":",
            "    "+a+" = (dict("+a+"[0]),) + "+a+"[1:]"
        ]
        rule="canonical-mapping-input-before-mutating-self"
    elif protocol=="set" and len(args.args)>=2 and args.vararg is None:
        a=args.args[1].arg
        body=[a+" = type("+recv+")("+a+")"]
        rule="canonical-set-input-before-mutating-self"
    else:
        raise ValueError("UNKNOWN_TYPED_PRECONDITION")
    doc=method.body[0]
    k=1 if isinstance(doc,ast.Expr) and isinstance(doc.value,ast.Constant) and isinstance(doc.value.value,str) else 0
    if k>=len(method.body):
        raise ValueError("UNKNOWN_BODY_INSERTION")
    anchor=method.body[k]
    # Insert BEFORE the first mutating operation, after original docstring.
    lines=source.splitlines(keepends=True)
    pad=" "*anchor.col_offset
    insertion="".join(pad+s+"\n" for s in body)
    patched="".join(lines[:anchor.lineno-1]) + insertion + "".join(lines[anchor.lineno-1:])
    compile(patched,"<generated-source-preflight>","exec")
    return patched,{"rule":rule,"first_arg":a,"line":anchor.lineno,
                    "generated_lines":body,"protocol":protocol,
                    "target_receiver_from_source":recv,
                    "operator_human_designed":True}

def run_scoped_native_suite(root):
    env=dict(os.environ)
    env["PYTHONPATH"]=os.pathsep.join((str(root/"src"),str(root)))
    options=[]
    if (root/"tests").exists(): options += [root/"tests"]
    if (root/"test").exists(): options += [root/"test"]
    if not options:
        return {"status":"UNKNOWN_NO_TEST_DIRECTORY"}
    t=time.monotonic()
    try:
        p=subprocess.run([sys.executable,"-m","pytest","-q",str(options[0])],
                         cwd=root,env=env,text=True,capture_output=True,timeout=180)
    except subprocess.TimeoutExpired:
        return {"status":"UNKNOWN_SUITE_TIMEOUT",
                "seconds":round(time.monotonic()-t,3)}
    log=(p.stdout or "")+(p.stderr or "")
    successes=re.findall(r"(\d+) passed",log)
    total=int(successes[-1]) if successes else 0
    return {"status":"PASS" if p.returncode==0 and total>0 else
            "UNKNOWN_NO_TEST_EXECUTION" if p.returncode==0 else "FAIL",
            "count_passed":total,"exit":p.returncode,
            "seconds":round(time.monotonic()-t,3),
            "log_sha256":sha(log.encode("utf-8")),
            "stdout_tail":p.stdout[-2500:],"stderr_tail":p.stderr[-1700:]}

def detailed_native_assessment(old,patched):
    a=gen.assess(old,patched)
    if a["status"] not in ("WARRANTED_BOUNDED_NATIVE_INVARIANT_SEPARATION",
                           "UNKNOWN_NO_CONSEQUENTIAL_OBSERVER"):
        return {"status":"UNKNOWN_NATIVE_COMPARISON","detail":a}
    o=old.get("operations",[])
    p=patched.get("operations",[])
    if len(o)!=len(p):return {"status":"UNKNOWN_DIFFERENT_OBSERVATIONS"}
    repaired=0
    introduced=0
    stable=0
    for x,y in zip(o,p):
        xo=x["native"].get("derived",{}).get("status")
        yo=y["native"].get("derived",{}).get("status")
        if xo=="VIOLATION" and yo=="CONSISTENT":
            repaired+=1
        if xo=="CONSISTENT" and yo=="VIOLATION":
            introduced+=1
        if xo=="CONSISTENT" and yo=="CONSISTENT":
            stable+=1
    return {"status":("PASS_SCOPED" if repaired>0 and introduced==0
                      else "REJECTED_OR_UNKNOWN"),
            "old_violations_repaired":repaired,"newly_introduced_violations":introduced,
            "preserved_consistent_observations":stable,
            "total_paired_programs":len(o)}

def execute(target,workspace,output):
    start=time.monotonic()
    try:
        _,trees=prior.make_worktrees(workspace,target)
        candidates=gen.synthesize_candidates(trees["head"],trees,target)
        records=[]
        for subj in candidates:
            old=gen.run_worker(trees["base"],subj,target["base"])
            author=gen.run_worker(trees["head"],subj,target["head"])
            prior_d=gen.assess(old,author)
            if prior_d["status"]!="WARRANTED_BOUNDED_NATIVE_INVARIANT_SEPARATION":
                records.append({"method":subj,"status":"UNKNOWN_UNQUALIFIED_OBSERVER",
                                "old_author_differential":prior_d});continue
            p=old.get("protocol")
            if p not in ("mapping","set"):
                records.append({"method":subj,"status":"UNKNOWN_UNSUPPORTED_INTERFACE"});continue
            srcpath=trees["base"]/subj["file"]
            original=srcpath.read_bytes()
            try:
                proposed,op=synthesize_preflight_patch(original.decode("utf-8"),subj,p)
            except Exception as err:
                records.append({"method":subj,"status":"UNKNOWN_OPERATOR_APPLICABILITY",
                                "error":str(err)[:350]});continue
            proposed_bytes=proposed.encode("utf-8")
            if proposed_bytes==original:
                records.append({"method":subj,"status":"UNKNOWN_IDENTITY_PATCH"});continue
            git_blob=prior.checked(["git","-C",str(trees["base"]),"hash-object",str(srcpath)])
            before_digest=sha(original)
            patched_digest=sha(proposed_bytes)
            diff="".join(difflib.unified_diff(original.decode("utf-8").splitlines(keepends=True),
                        proposed.splitlines(keepends=True),fromfile="a/"+subj["file"],
                        tofile="b/"+subj["file"]))
            patchfile=output/(
                target["repo"].replace("/","_")+"-preflight.patch")
            patchfile.write_text(diff,encoding="utf-8")
            try:
                srcpath.write_bytes(proposed_bytes)
                patched_native=gen.run_worker(trees["base"],subj,target["base"])
                test_suite=run_scoped_native_suite(trees["base"])
            finally:
                # Real removal/abatement, not a dummy recorded label.
                srcpath.write_bytes(original)
            removed_native=gen.run_worker(trees["base"],subj,target["base"])
            removed_assessment=gen.assess(removed_native,author)
            simulated=srcpath.read_bytes()==original
            srcpath.write_bytes(proposed_bytes)
            replay_sha=sha(srcpath.read_bytes())
            srcpath.write_bytes(original)
            trial=detailed_native_assessment(old,patched_native)
            qualified=(trial["status"]=="PASS_SCOPED"
                       and test_suite["status"]=="PASS"
                       and removed_assessment["status"]=="WARRANTED_BOUNDED_NATIVE_INVARIANT_SEPARATION"
                       and simulated and replay_sha==patched_digest
                       and srcpath.read_bytes()==original)
            records.append({
                "method":subj,
                "status":("WARRANTED_BOUNDED_PREDECLARED_REPAIR_INSTANCE" if qualified
                          else "UNKNOWN_OR_REJECTED_REPAIR"),
                "qualified":qualified,"typed_preflight_rule":op,
                "original_blob_git_sha":git_blob,
                "original_source_sha256":before_digest,
                "generated_source_sha256":patched_digest,
                "source_patch_sha256":prior.sha_file(patchfile),
                "patch_file_name":patchfile.name,
                "source_diff":diff,
                "prior_reproduced_observer":prior_d["minimal_witness"],
                "repaired_observer":trial,
                "scoped_original_suite":test_suite,
                "removed_patch_native_restores_violation":removed_assessment["status"],
                "source_exactly_restored":simulated and srcpath.read_bytes()==original,
                "candidate_replay_sha_identical":replay_sha==patched_digest,
                "subject_sha_unchanged":target["base"],
            })
        return {"repo":target["repo"],"role":target["role"],"qualified":any(x.get("qualified") for x in records),
                "records":records,"original":target["base"],"author_head":target["head"],
                "elapsed_seconds":round(time.monotonic()-start,3)}
    except Exception as err:
        return {"repo":target["repo"],"qualified":False,
                "status":"UNKNOWN_REPAIR_HARNESS","error":type(err).__name__,
                "message":str(err)[:1600],
                "elapsed_seconds":round(time.monotonic()-start,3)}

def main():
    out=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "evidence")
    out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mathgraph-preflight-") as tmp:
        data=[execute(t,pathlib.Path(tmp)/("family"+str(i)),out)
              for i,t in enumerate(gen.TARGETS)]
    verdict="WARRANTED_BOUNDED_TWO_TYPE_DIRECTED_PREFLIGHT_REPAIRS" if all(
        x["qualified"] for x in data) else "UNKNOWN_OR_REJECTED_PREFLIGHT_REPAIR_TRANSFER"
    report={"status":verdict,"results":data,
            "source_sha256":prior.sha_file(__file__),
            "frozen_protocol_sha256":prior.sha_file(HERE/"FROZEN_PREFLIGHT_REPAIR.md"),
            "human_authored_type_directed_operator":True,
            "scientific_L7":"UNKNOWN",
            "unrestricted_safe_repair":"UNKNOWN",
            "strong_agent_baseline":"NOT_RUN",
            "no_upstream_write":True}
    (out/"repair_report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "status":verdict,
        "report_sha256":prior.sha_file(out/"repair_report.json"),
        "results":[{"repo":z["repo"],"qualified":z["qualified"],
                    "record_summaries":[{"status":v["status"],"source_method":v["method"]["method"],
                                         "rule":v.get("typed_preflight_rule",{}).get("rule"),
                                         "suite":v.get("scoped_original_suite",{}).get("status"),
                                         "suite_tests":v.get("scoped_original_suite",{}).get("count_passed"),
                                         "ablation":v.get("removed_patch_native_restores_violation")}
                                         for v in z.get("records",[])]}
                    for z in data],
        "L7":"UNKNOWN"},sort_keys=True))
    return 0 if all(x["qualified"] for x in data) else 1

if __name__=="__main__":
    raise SystemExit(main())
