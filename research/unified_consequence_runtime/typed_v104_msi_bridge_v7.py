"""V7 source-bound adapter: V6 typed native evidence → ORIGINAL V104/MSI rules.

No learning language, Pareto chooser, verifier, or old evidentiary authority
is reimplemented. The existing V104 AST generator and MSI V10 key functions
are executed from authenticated, pinned Git source. Each proposed executable
is committed as a *new*, independently checkable local Git candidate tree.
The old source and every original Git symlink/gitlink remain untouched.

This bridge by itself grants no G2, causal compounding or external permission.
Synthetic tests only qualify representation and outcome/evidence plumbing.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from . import typed_source_inventory_v5 as typed
from . import typed_native_authority_v6 as native
from . import decisive_native as original
from . import decisive_native_verify as verifier
from .qualify_recursive_frontier import original_candidates
from .developmental_choice import profile_binding, choose_verified_profiles

SCHEMA = "UDM_SOURCE_BOUND_TYPED_V104_MSI_BRIDGE_V7"
_GIT_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False)


def _git(repo,*args,raw=False,input_bytes=None):
    command=["git","-C",str(repo),*args]
    proc=subprocess.run(command,input=input_bytes,capture_output=True,timeout=45)
    if proc.returncode:
        raise ValueError("source Git operation refused: "+" ".join(args[:2]))
    return proc.stdout if raw else proc.stdout.decode().strip()


def _source(repo,base):
    repo=Path(repo).absolute()
    return typed.snapshot(repo,base)


def _blobs(repo,base):
    snap=_source(repo,base)
    return snap, {row["path"]:row for row in snap["manifest"] if row["mode"] in typed.REGULAR_MODES}


def _git_blob_oid(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()


def _author_rows(repo,base,rows):
    if not isinstance(rows,(tuple,list)) or not rows:
        raise ValueError("frozen independent author-test blob refs required")
    snap,regular=_blobs(repo,base)
    out={}
    for item in rows:
        if not isinstance(item,dict) or set(item)!={"path","git_oid","sha256","bytes"}:
            raise ValueError("frozen author-test record must bind all four fields")
        path=item["path"]
        typed._path(path)
        if (not original.is_test(path) or path=="setup.py" or
                not path.endswith(".py") or not re.fullmatch(r"[0-9a-f]+",item["bytes"])):
            raise ValueError("author test path or exact byte transport invalid")
        raw=bytes.fromhex(item["bytes"])
        if (not _GIT_HEX40.fullmatch(item["git_oid"]) or
                not _SHA256.fullmatch(item["sha256"]) or
                digest(raw)!=item["sha256"] or
                _git_blob_oid(raw)!=item["git_oid"]):
            raise ValueError("author-test Git object and byte identity mismatch")
        if path in out:
            raise ValueError("duplicate frozen author-test path")
        if path in snap["gitlinks"] or (path in regular and regular[path]["mode"] not in typed.REGULAR_MODES):
            raise ValueError("cannot make opaque source into author-test authority")
        if any(path==entry["path"] for entry in snap["links"]):
            raise ValueError("symlink may not become protected author-test input")
        if path in regular:
            old=typed._git(repo,"cat-file","blob",regular[path]["oid"])
            if old==raw:
                raise ValueError("no changed author-test obligation")
        else:old=b""
        out[path]=(old,raw,item["git_oid"])
    return snap,regular,out


def _static_functions(path,raw):
    try:
        tree,nodes=verifier._test_nodes(path,raw)
    except (SyntaxError,UnicodeError,ValueError) as error:
        raise ValueError("author-test AST authority refused") from error
    output={}
    def visit(body,prefix):
        for x in body:
            if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef)) and x.name.startswith("test_"):
                output[prefix+"::"+x.name]=ast.dump(x,include_attributes=False)
            elif isinstance(x,ast.ClassDef):
                visit(x.body,prefix+"::"+x.name)
    visit(tree.body,path)
    if sorted(output)!=sorted(nodes):
        raise ValueError("author-test static node correspondence uncertain")
    return output


def changed_author_assertions(repo,base,rows):
    """Only independently head-authored additions/changes define obligations."""
    _,_,inputs=_author_rows(repo,base,rows)
    needs=[]
    for path,(old,raw,_) in inputs.items():
        previous=_static_functions(path,old) if old else {}
        new=_static_functions(path,raw)
        needs.extend(node for node,v in new.items() if previous.get(node)!=v)
    if not needs:
        raise ValueError("no changed independent author assertions to protect")
    return sorted(set(needs))


def _candidate(candidate,regular):
    if (not isinstance(candidate,dict) or set(candidate)!={"replacements"} or
            not isinstance(candidate["replacements"],list)):
        raise ValueError("wrong original V104 candidate shape")
    seen=set()
    for row in candidate["replacements"]:
        if not isinstance(row,dict) or set(row)!={"path","original_sha256","replacement"}:
            raise ValueError("wrong original V104 replacement")
        name=row["path"]
        typed._path(name)
        if (name in seen or name not in regular or not name.endswith(".py") or
                original.is_test(name) or Path(name).name in ("setup.py","conftest.py")):
            raise ValueError("candidate may edit only an original regular production Python file")
        if (not isinstance(row["replacement"],str) or
                not isinstance(row["original_sha256"],str) or
                row["original_sha256"] != regular[name]["sha256"]):
            raise ValueError("original production SHA256 does not match candidate")
        try:ast.parse(row["replacement"],filename=name)
        except (SyntaxError,UnicodeError) as error:
            raise ValueError("candidate generated malformed Python") from error
        seen.add(name)
    return seen


def construct_candidate(repo,base,author_rows,candidate,out):
    """Create an exact Git commit locally from pinned base+independent tests+candidate.

    This does not fetch or inspect repaired head production. A Git worktree is
    detached, only independently allowed paths are changed and the generated
    source commit's complete typed tree is re-inventoried after sealing.
    """
    repo=Path(repo).absolute()
    snap,regular,authors=_author_rows(repo,base,author_rows)
    original_native=_source(repo,base)
    allowed=_candidate(candidate,regular)
    changed_author_assertions(repo,base,author_rows)
    dest=Path(out).absolute()
    if dest.exists() or dest.resolve()!=dest or dest.is_relative_to(repo):
        raise ValueError("new canonical disposable candidate worktree required")
    if any(x in allowed for x in authors):
        raise ValueError("candidate cannot overlap protected independent tests")
    started=time.perf_counter();complete=False
    gitdir=repo / ".git"
    if not gitdir.exists():raise ValueError("source Git repository unavailable")
    _git(repo,"worktree","add","--detach",str(dest),base)
    try:
        for path,(_,raw,oid) in sorted(authors.items()):
            target=dest/path
            if target.exists() and target.is_symlink():
                raise ValueError("author-test blob would follow tracked link")
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw)
            # Local object's Git blob ID must match externally signed head-test OID.
            if _git(dest,"hash-object",str(target))!=oid:
                raise ValueError("installed author tests differ from frozen Git blob")
        for row in candidate["replacements"]:
            path=row["path"]
            dest.joinpath(path).write_text(row["replacement"])
        edits=sorted(set(authors)|allowed)
        _git(dest,"add","--",*edits)
        status=_git(dest,"diff","--cached","--name-only").splitlines()
        if set(status)!=set(edits):
            raise ValueError("candidate staged unexpected or missing source changes")
        commit_env=dict(os.environ, GIT_AUTHOR_NAME="V7 Research",
                        GIT_AUTHOR_EMAIL="v7@example.invalid",
                        GIT_COMMITTER_NAME="V7 Research",
                        GIT_COMMITTER_EMAIL="v7@example.invalid")
        cmd=["git","-C",str(dest),"commit","-qm","isolated V104 candidate and exact frozen author tests"]
        p=subprocess.run(cmd,env=commit_env,capture_output=True,timeout=45)
        if p.returncode:raise ValueError("no content-addressed candidate Git commit")
        revision=_git(dest,"rev-parse","HEAD")
        if _git(dest,"rev-parse","HEAD^")!=base:
            raise ValueError("generated candidate does not extend original base")
        updated=_source(repo,revision)
        if updated["counts"]!=snap["counts"] and any(row["path"] not in snap["manifest"] for row in []):
            raise ValueError("unexpected source counts")
        for old in original_native["manifest"]:
            if old["path"] in edits:continue
            recent=next((x for x in updated["manifest"] if x["path"]==old["path"]),None)
            if recent!=old:
                raise ValueError("original source outside candidate/test scope changed")
        changed=True
        for path,(prior,raw,oid) in authors.items():
            target=next((x for x in updated["manifest"] if x["path"]==path),None)
            if target is None or target.get("oid")!=oid:
                raise ValueError("tested Git candidate lacks original author assertion blob")
        complete=True
        return {"schema":SCHEMA, "status":"SOURCE_BOUND_CANDIDATE_COMMIT_NO_WARRANT",
                "source_base":base,"candidate_commit":revision,
                "candidate_tree":updated["git_tree"],
                "typed_manifest_sha256":updated["manifest_sha256"],
                "protocol_source_manifest_sha256":snap["manifest_sha256"],
                "author_test_blobs":[{"path":k,"oid":v[2],"sha256":digest(v[1])}
                                     for k,v in sorted(authors.items())],
                "required":changed_author_assertions(repo,base,author_rows),
                "candidate_sha256":digest(canonical(candidate).encode()),
                "changed_paths":edits,
                "seconds":time.perf_counter()-started}
    finally:
        # The original bare/source HEAD remains unchanged; ephemeral tree only.
        try:_git(repo,"worktree","remove","--force",str(dest))
        except ValueError:
            if complete:raise


def native_profile(repo,candidate_context,out,*,interpreter=sys.executable,timeout=90):
    """Two actual source-native processes; UNKNOWN cannot become a failure."""
    if candidate_context.get("status")!="SOURCE_BOUND_CANDIDATE_COMMIT_NO_WARRANT":
        raise ValueError("qualified typed candidate provenance required")
    dest=Path(out).absolute()
    if dest.exists():raise ValueError("new native output required")
    staged=native.stage(repo,candidate_context["candidate_commit"],dest)
    requires=tuple(candidate_context["required"])
    first=native.run_protected(repo,candidate_context["candidate_commit"],dest,
                                required=requires,interpreter=interpreter,timeout=timeout)
    second=native.run_protected(repo,candidate_context["candidate_commit"],dest,
                                 required=requires,interpreter=interpreter,timeout=timeout)
    native.verify_stage(repo,candidate_context["candidate_commit"],dest)
    bound={
        "source_commit":candidate_context["candidate_commit"],
        "candidate_sha256":candidate_context["candidate_sha256"],
        "original_source":candidate_context["source_base"],
        "author_test_blobs":candidate_context["author_test_blobs"],
        "required":candidate_context["required"],
        "typed_manifest_sha256":staged["typed_manifest_sha256"],
        "measured_executions":[first,second]
    }
    status="UNKNOWN_NATIVE_EVIDENCE"
    if (first.get("status")==second.get("status") and
            first.get("native_exit") is not None and second.get("native_exit") is not None and
            first.get("native_calls")==1 and second.get("native_calls")==1 and
            first.get("executed")==second.get("executed") and
            first.get("deselected")==second.get("deselected") and
            first.get("imported_project_files")==second.get("imported_project_files")):
        if first["status"]=="PASS_SCOPED_NATIVE":
            status="VERIFIED_REPEATED_PASS_SCOPED_NATIVE"
        elif first["status"]=="FAIL_NATIVE_PROTECTED":
            status="VERIFIED_REPEATED_FAIL_NATIVE_PROTECTED"
    return {**bound,"schema":"UDM_V7_TYPED_NATIVE_REPEATED_PROFILE",
            "status":status, "native_calls":(first.get("native_calls",0)+second.get("native_calls",0)),
            "measurements":[0 if status=="VERIFIED_REPEATED_PASS_SCOPED_NATIVE" else 1,2]
                if status in ("VERIFIED_REPEATED_PASS_SCOPED_NATIVE",
                              "VERIFIED_REPEATED_FAIL_NATIVE_PROTECTED") else None,
            "native_evidence_sha256":digest(canonical(bound).encode()),
            "cost_seconds":sum(row.get("native_seconds",0) for row in (first,second)),
            "full_suite":False,"G2":"UNKNOWN"}


def catalog_v104_typed(repo,base,production_paths,triskelion,msi,*,cap=64,observation=None):
    """Run original source-pinned V104 and MSI only; no target-specific builder."""
    if not isinstance(production_paths,(tuple,list)) or not production_paths:
        raise ValueError("nonempty predeclared production scope required")
    snap,regular=_blobs(repo,base)
    evidence=observation or {}
    rows=[]
    for path in production_paths:
        typed._path(path)
        if path not in regular or original.is_test(path) or not path.endswith(".py"):
            raise ValueError("V104 production path not in original typed source")
        raw=typed._git(repo,"cat-file","blob",regular[path]["oid"])
        source=raw.decode("utf-8")
        for selector,builder,text in original_candidates(triskelion,source,cap=cap):
            locations=original.changed_lines(source,text)
            traces=evidence.get(path,())
            distance=min((abs(x-y) for x in locations for y in traces),default=1000000)
            mean=sum(locations)/len(locations) if locations else 0
            variance=sum((x-mean)**2 for x in locations)/len(locations) if locations else 0
            candidate={"replacements":[{"path":path,
                          "original_sha256":regular[path]["sha256"],
                          "replacement":text}]}
            rows.append({"id":verifier.fingerprint(candidate),"candidate":candidate,
                         "selector":selector,"builder":builder,"path":path,
                         "changed_lines":locations,
                         "features":{"K":distance,"c":max(1,len(locations)),"v":variance}})
    if not rows:
        raise ValueError("original V104 language produced no admissible operator")
    orders=original.orders(rows,msi)
    if len(orders)!=37 or any(set(order)!=set(r["id"] for r in rows) for order in orders.values()):
        raise ValueError("original MSI 36 policy orders are incomplete")
    return {"schema":"UDM_TYPED_ORIGINAL_V104_CATALOG_V7",
            "rows":rows,"orders":orders,
            "source":{"v104_language":"ORIGINAL_PINNED_V104",
                      "msi_policy":"ORIGINAL_PINNED_MSI_V10",
                      "v104":dict(__import__("research.unified_consequence_runtime.qualify_recursive_frontier",
                                             fromlist=["PINS"]).PINS["constructor_language"]),
                      "msi":original.POLICY_PIN},
            "original_typed_source_sha256":snap["manifest_sha256"],
            "budget_horizon":"8 native candidates per method, no complete grammar proof"}


def verified_profiles(records,candidates,futures):
    """Construct finite vectors only from actual positively classified receipts.

    This function checks the structural carrier. Independent native authority
    must have been established by the caller's actual process reexecution.
    """
    if not isinstance(records,list) or not isinstance(candidates,tuple) or not isinstance(futures,tuple):
        raise ValueError("finite immutable native record carriers required")
    if not candidates or not futures or len(set(candidates))!=len(candidates) or len(set(futures))!=len(futures):
        raise ValueError("duplicate or empty original method/future carriers")
    profiles={c:{} for c in candidates}
    bindings=[]
    for record in records:
        cand=record.get("candidate");future=record.get("future")
        if cand not in profiles or future not in futures or future in profiles[cand]:
            raise ValueError("wrong, duplicate or unexpected tested native profile")
        state=record.get("status")
        if state not in ("VERIFIED_REPEATED_PASS_SCOPED_NATIVE",
                         "VERIFIED_REPEATED_FAIL_NATIVE_PROTECTED"):
            raise ValueError("unverified/unknown native event cannot become failure")
        if (record.get("measurements") !=
            [0 if state=="VERIFIED_REPEATED_PASS_SCOPED_NATIVE" else 1,2]
            or record.get("native_calls")!=2 or
            not _GIT_HEX40.fullmatch(record.get("source_commit","")) or
            not _SHA256.fullmatch(record.get("native_evidence_sha256",""))):
            raise ValueError("native profile metrics, lineage or charged calls invalid")
        profiles[cand][future]=record["measurements"]
        bindings.append([cand,future,record["source_commit"],record["native_evidence_sha256"]])
    if any(set(profiles[c])!=set(futures) for c in candidates):
        raise ValueError("incomplete original method x frozen future evidence matrix")
    return {"schema":"UDM_COMPLETE_TYPED_NATIVE_PROFILE_CARRIER_V7",
            "candidates":list(candidates),"futures":list(futures),
            "profiles":profiles,"source_bindings":sorted(bindings),
            "bound_by_native_reexecution":"CALLER_MUST_ACTUALLY_EXECUTE",
            "G2":"UNKNOWN"}


def original_msi_decision(carrier,source_repo,*,scope):
    """Use original exact Git-pinned Pareto chooser; not an MDA G2 certificate."""
    candidates=tuple(carrier["candidates"]);futures=tuple(carrier["futures"])
    profiles=carrier["profiles"]
    binding=profile_binding(candidates,futures,profiles,scope={
        **scope,
        "typed_native_evidence_sha256":digest(canonical(carrier["source_bindings"]).encode()),
        "native_transport":"V6_SCOPED",
        "original_msi_policy":"V10",
        "original_v104_generator":"V104",
    })
    # The caller's source_repo is the independently pinned *task* source. The
    # Pareto algorithm itself must always be authenticated from the separate
    # Metalogic research checkout (SOURCE_PIN.repository=heathsanchez/test).
    # Never infer that a target/source repository contains that old Git commit.
    qualified_method_checkout=Path(__file__).resolve().parents[2]
    choice=choose_verified_profiles(qualified_method_checkout,candidates,futures,profiles,
                                    evidence_binding=binding)
    return {"schema":"UDM_V7_NATIVE_TO_ORIGINAL_PARETO_DECISION",
            "choice":choice,"profiles":profiles,
            "evidence_binding":binding,
            "scientific_promotion":"NONE",
            "MDA_POLICY_ADMISSION":"NOT_RUN_WITH_THIS_BRIDGE",
            "G2":"UNKNOWN"}
