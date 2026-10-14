#!/usr/bin/env python3
"""Explicitly source-native subclass counterexample to a preflight patch.

Human-authored applicability falsifier, not autonomous repair-language invention.
The subject class/method is source-derived by the same frozen AST scanner.
"""
from __future__ import annotations
import ast,hashlib,importlib,json,pathlib,subprocess,sys,tempfile,time,difflib

HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import invariant_generator as gen
import preflight_repair as pre
prior=gen.prior

def sha(x):return hashlib.sha256(x).hexdigest()

def worker(args):
    root=pathlib.Path(args["root"]);subj=args["subject"]
    actual=prior.call(["git","-C",str(root),"rev-parse","HEAD"])
    if actual["code"] or actual["stdout"].strip()!=args["sha"]:
        print(json.dumps({"status":"UNKNOWN_SOURCE_IDENTITY"}));return 0
    try:
        importer,modname=prior.find_import_info(root,subj["file"])
        sys.path.insert(0,str(importer))
        module=importlib.import_module(modname)
        cls=getattr(module,subj["class"])
        class Derived(cls):
            def __init__(self,source,required_token):
                self.required_token=required_token
                super().__init__(source)
        instance=Derived([0,1],object())
        arg=[1,2]
        try:
            getattr(instance,subj["method"])(arg)
            call={"ok":True}
        except Exception as exc:
            call={"ok":False,"error":type(exc).__name__,"detail":str(exc)[:250]}
        observed={"len":len(instance),"contents":list(instance),
                  "tag_preserved":isinstance(instance.required_token,object)}
        norm=observed["contents"]==[0,2] and observed["len"]==2
        print(json.dumps({"status":"CONSISTENT_SUBCLASS" if call["ok"] and norm else
                          "INTRODUCED_SUBCLASS_FAILURE" if not call["ok"] else
                          "UNEXPECTED_SUBCLASS_BEHAVIOUR",
                          "original_source_sha":actual["stdout"].strip(),
                          "native_method":subj["method"],"call":call,
                          "projection":observed,"expected":[0,2]}))
    except Exception as exc:
        print(json.dumps({"status":"UNKNOWN_SUBCLASS_HARNESS",
                          "error":type(exc).__name__,"detail":str(exc)[:400]}))
    return 0

def run_worker(root,subject,sha_value):
    p=subprocess.run([sys.executable,str(pathlib.Path(__file__).resolve()),
                      "worker",json.dumps({"root":str(root),
                                            "subject":subject,"sha":sha_value})],
                     capture_output=True,text=True,check=False,timeout=50)
    try:
        result=json.loads(p.stdout)
        result["exit"]=p.returncode
        return result
    except Exception:
        return {"status":"UNKNOWN_UNPARSEABLE_SUBCLASS","stderr":p.stderr[-300:]}

def lexical_normalization(proposed,subject,generated_operator):
    if generated_operator.get("protocol")!="set":
        raise ValueError("UNKNOWN_NON_SET_APPLICABILITY")
    first=generated_operator["generated_lines"][0]
    placeholder="type("+generated_operator["target_receiver_from_source"]+")"
    if first.count(placeholder)!=1:
        raise ValueError("UNKNOWN_MISSING_DYNAMIC_CTOR")
    replacement=first.replace(placeholder,subject["class"])
    if proposed.count(first)!=1:
        raise ValueError("UNKNOWN_AMBIGUOUS_INSERTION")
    updated=proposed.replace(first,replacement,1)
    compile(updated,"<typed-lexical-preflight>","exec")
    return updated,{"old_generated_line":first,"new_generated_line":replacement,
                    "policy":"bind canonical representation to source lexical owner",
                    "type_name_source":"frozen AST changed owner.name",
                    "human_authored_candidate_family":True}

def native_subject(target,workspace,out):
    now=time.monotonic()
    try:
        _,trees=prior.make_worktrees(workspace,target)
        candidates=gen.synthesize_candidates(trees["head"],trees,target)
        records=[]
        for subject in candidates:
            old=gen.run_worker(trees["base"],subject,target["base"])
            head=gen.run_worker(trees["head"],subject,target["head"])
            before=gen.assess(old,head)
            if before["status"]!="WARRANTED_BOUNDED_NATIVE_INVARIANT_SEPARATION":
                records.append({"status":"UNKNOWN_NO_QUALIFIED_ORIGINAL_OBSERVER"});continue
            if old.get("protocol")!="set":
                records.append({"status":"UNKNOWN_ADVERSARY_NOT_APPLICABLE"});continue
            sourcepath=trees["base"]/subject["file"]
            original=sourcepath.read_bytes()
            first_patch,first_rule=pre.synthesize_preflight_patch(
                original.decode("utf-8"),subject,old["protocol"])
            original_client=run_worker(trees["base"],subject,target["base"])
            head_client=run_worker(trees["head"],subject,target["head"])
            sourcepath.write_text(first_patch,encoding="utf-8")
            try:
                first_client=run_worker(trees["base"],subject,target["base"])
            finally:sourcepath.write_bytes(original)
            restored_client=run_worker(trees["base"],subject,target["base"])
            initial_rejected=(original_client["status"]=="CONSISTENT_SUBCLASS"
                              and head_client["status"]=="CONSISTENT_SUBCLASS"
                              and first_client["status"]=="INTRODUCED_SUBCLASS_FAILURE"
                              and restored_client["status"]=="CONSISTENT_SUBCLASS")
            new_patch,new_rule=lexical_normalization(first_patch,subject,first_rule)
            altbytes=new_patch.encode("utf-8")
            sourcepath.write_bytes(altbytes)
            try:
                alt_client=run_worker(trees["base"],subject,target["base"])
                repaired=gen.run_worker(trees["base"],subject,target["base"])
                scope=pre.detailed_native_assessment(old,repaired)
                suite=pre.run_scoped_native_suite(trees["base"])
                patch= "".join(difflib.unified_diff(
                    original.decode("utf-8").splitlines(keepends=True),
                    new_patch.splitlines(keepends=True),
                    fromfile="a/"+subject["file"],tofile="b/"+subject["file"]))
                filename=(target["repo"].replace("/","_")+
                          "_lexical_preflight.patch")
                (out/filename).write_text(patch)
            finally:sourcepath.write_bytes(original)
            again=run_worker(trees["base"],subject,target["base"])
            ablated=gen.run_worker(trees["base"],subject,target["base"])
            observed_restore=gen.assess(ablated,head)
            qualified=(initial_rejected
                       and alt_client["status"]=="CONSISTENT_SUBCLASS"
                       and scope["status"]=="PASS_SCOPED"
                       and suite["status"]=="PASS"
                       and again["status"]=="CONSISTENT_SUBCLASS"
                       and observed_restore["status"]=="WARRANTED_BOUNDED_NATIVE_INVARIANT_SEPARATION"
                       and sourcepath.read_bytes()==original)
            records.append({
                "subject":subject,"status":("WARRANTED_BOUNDED_LEXICAL_CONSTRUCTOR_REPAIR"
                                            if qualified else "UNKNOWN_OR_REJECTED_BROAD_CANDIDATE"),
                "first_candidate_status":("REJECTED_SUBCLASS_UNSAFE" if initial_rejected
                                          else "UNKNOWN_OR_NOT_FALSIFIED"),
                "qualified":qualified,
                "original_subclass":original_client,"author_head_subclass":head_client,
                "first_generated_repair_subclass":first_client,
                "physical_removal_original_subclass":restored_client,
                "new_lexical_candidate_subclass":alt_client,
                "new_candidate_rule":new_rule,
                "original_git_file_sha256":sha(original),
                "first_generated_file_sha256":sha(first_patch.encode("utf-8")),
                "new_generated_file_sha256":sha(altbytes),
                "new_generated_patch_sha256":prior.sha_file(out/filename),
                "new_patch_file":filename,
                "source_native_repair_corpus":scope,
                "original_suite_on_lexical_patch":suite,
                "physical_removal_native_original":observed_restore["status"],
                "original_file_exactly_restored":sourcepath.read_bytes()==original,
            })
        return {"repo":target["repo"],"eligible":any(r.get("first_candidate_status")=="REJECTED_SUBCLASS_UNSAFE" for r in records),
                "qualified":any(r.get("qualified") for r in records),
                "records":records,"elapsed_seconds":round(time.monotonic()-now,3)}
    except Exception as exc:
        return {"repo":target["repo"],"qualified":False,"status":"UNKNOWN_HARNESS",
                "error":type(exc).__name__,"detail":str(exc)[:1200]}

def main():
    if len(sys.argv)>1 and sys.argv[1]=="worker":
        return worker(json.loads(sys.argv[2]))
    out=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "evidence")
    out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mgcheck-subclass-") as tmp:
        results=[native_subject(t,pathlib.Path(tmp)/("family"+str(i)),out)
                 for i,t in enumerate(gen.TARGETS)]
    selected=[r for r in results if r["eligible"]]
    conclusion=("WARRANTED_BOUNDED_REJECT_DYNAMIC_SUBCLASS_AND_QUALIFY_LEXICAL_FIX"
                if len(selected)==1 and selected[0]["qualified"] else
                "UNKNOWN_OR_REJECTED_SUBCLASS_REPAIR_GATE")
    report={"status":conclusion,"results":results,
            "human_authored_adversary_and_second_candidate":True,
            "scientific_L7":"UNKNOWN","universal_subclass_support":"UNKNOWN",
            "source_sha256":prior.sha_file(__file__),
            "protocol_sha256":prior.sha_file(HERE/"FROZEN_SUBCLASS_ADVERSARY.md"),
            "safe_to_merge":"UNKNOWN","no_upstream_writes":True}
    (out/"adversarial_report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "status":report["status"],
        "report_sha256":prior.sha_file(out/"adversarial_report.json"),
        "results":[{"repo":r["repo"],"qualified":r["qualified"],
                    "eligible":r["eligible"],
                    "records":[{"status":v["status"],"original_failed_policy":
                                  v.get("first_candidate_status"),
                                "native_suite":v.get("original_suite_on_lexical_patch",{}).get("status"),
                                "tests":v.get("original_suite_on_lexical_patch",{}).get("count_passed"),
                                "native_repair":v.get("source_native_repair_corpus",{}).get("status")}
                               for v in r.get("records",[])]}
                   for r in results],
        "L7":"UNKNOWN"},sort_keys=True))
    return 0 if conclusion.startswith("WARRANTED") else 1

if __name__=="__main__":
    raise SystemExit(main())
