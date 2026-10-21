#!/usr/bin/env python3
"""Induce a new proof-program grammar by composing upstream source lemmas.

Unlike the preceding finite/Nat-direction constructor, no target-specific
lemma names or proof programs are supplied.  The upstream source supplies
candidate *rewrite primitives*. The meta-substrate (source mining, structural
simp/constructor tactics, subset enumeration) is still human-authored;
therefore this is bounded meta-grammar EXTENSION, not an autonomous invention
of the meta-substrate itself. Every accepted target is Lean checked.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
import subprocess
import time
from pathlib import Path


def encode(x):
    return json.dumps(x, sort_keys=True, indent=2) + "\n"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(path, *args):
    return subprocess.check_output(
        ["git", "-C", str(path), *args], text=True
    ).strip()


def frozen_source(repo, protocol):
    if git(repo, "rev-parse", "HEAD") != protocol["upstream"]["commit"]:
        raise ValueError("UPSTREAM_COMMIT_CHANGED")
    rows=[]
    for spec in protocol["exact_source_modules"]:
        if git(repo, "hash-object", spec["path"]) != spec["git_blob"]:
            raise ValueError("UPSTREAM_BLOB_CHANGED:" + spec["path"])
        rows.append((spec, (repo / spec["path"]).read_text(encoding="utf-8")))
    return rows


def mine_lemmas(sources):
    """Read original Lean theorem declarations, never a manually seeded winner."""
    result={}
    for spec,src in sources:
        lines=src.splitlines()
        for i,line in enumerate(lines):
            m=re.match(r"^\s*(?:@\[[^\]]+\]\s+)?(?:private\s+)?theorem\s+([A-Za-z][A-Za-z0-9_']*)\b",line)
            if not m:
                continue
            name=m.group(1)
            if name in ("inj",):
                continue
            qualified=spec["namespace"]+"."+name
            # Structural lemma lexical extraction uses ORIGINAL source bytes;
            # limit to header, not an existing human proof body.
            summary=" ".join(lines[i:i+4]).split(" := by")[0].split(" := rfl")[0]
            result[qualified]={"name":qualified,"header":summary[:600],"source":spec["path"]}
    if len(result)<6:
        raise ValueError("SOURCE_LEMMA_INDEX_UNDERSUPPLIED")
    return result


def features(text):
    text=text.replace("++"," append ").replace("∈"," mem ")
    tokens=set(re.findall(r"[a-z]+|[A-Z]+(?=[^a-z]|$)",text))
    lower=text.lower()
    for keyword in ("tolts","toflts","prod","append","mtr","mem","setimage"):
        if keyword in lower: tokens.add(keyword)
    return {str(x).lower() for x in tokens if len(x)>=3}


def candidates(index, goal, retained, count=11):
    tokens=features(goal)
    available=[]
    for name,row in index.items():
        if name in retained:
            continue
        pieces=set(x.lower() for x in re.findall(
            r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|[0-9]+",
            name.split(".")[-1]))
        lower_name=name.lower()
        bonus=0
        for word in ("tolts","toflts","prod","append","mtr","mem","setimage"):
            if word in lower_name and word in goal.lower():
                bonus+=4 if word not in ("mtr","mem") else 2
        if "++" in goal and "++" in row["header"]:
            bonus+=7
        if "∈" in goal and "∈" in row["header"]:
            bonus+=6
        score=bonus+sum(1 for w in pieces if w in tokens)
        available.append((-score,name))
    available.sort()
    return [name for _,name in available[:count]]


def theorem_source(protocol, goal, tactic):
    imports="\n".join(
        "import "+spec["import"] for spec in protocol["exact_source_modules"])
    return (
        imports+"\n\nnamespace GeneratedStructuralTransport\n"
        "open Cslib\n"
        "theorem exact_target\n    "+goal["statement"]+" := by\n"
        +"\n".join("  "+line for line in tactic.split("\n"))+
        "\nend GeneratedStructuralTransport\n"
    )


def tactic_variants(lemmas, structural):
    refs=list(lemmas)
    refs.extend(structural)
    if len(refs)!=len(set(refs)):
        raise AssertionError("DUPLICATE_SOURCE_PROOF_ATOM")
    if not refs:
        return ["rfl","simp","simp_all","grind","aesop"]
    args=", ".join(refs)
    return [
        "simpa ["+args+"]",
        "simp ["+args+"]",
        "cases t\nsimpa ["+args+"]",
        "cases t\nsimp ["+args+"]",
        "simp_all ["+args+"]"
    ]


def native_run(repo,file,timeout):
    start=time.monotonic()
    try:
        p=subprocess.run(["lake","env","lean",str(file)],
            cwd=repo,timeout=timeout,capture_output=True,text=True,check=False)
        return p.returncode,(p.stdout+p.stderr)[-1100:],time.monotonic()-start
    except subprocess.TimeoutExpired:
        return 124,"NATIVE_TOOLCHAIN_TIMEOUT",time.monotonic()-start


def method_trial(repo,protocol,goal,program,output,name,timeout,history,budget):
    if len(history)>=budget:
        raise ValueError("NATIVE_COMPOSITION_BUDGET_EXHAUSTED")
    script=theorem_source(protocol,goal,program)
    path=output/"candidate.lean"
    path.write_text(script)
    code,diag,duration=native_run(repo,path,timeout)
    row={"stage":goal["stage"],"program":program,
         "returncode":code,"accepted":code==0,
         "duration_s":round(duration,5),
         "diagnostic_sha256":digest(diag.encode()),
         "diagnostic_tail":diag[-350:],
         "source_sha256":digest(script.encode())}
    history.append(row)
    return code==0,script


def run(cslib,protocol_path,out):
    raw=protocol_path.read_bytes()
    p=json.loads(raw)
    if p.get("schema")!="metalogic.typed-method-grammar-extension-native.v1":
        raise ValueError("WRONG_FROZEN_PROGRAM")
    if git(cslib,"rev-parse","HEAD")!=p["upstream"]["commit"]:
        raise ValueError("WRONG_NATIVE_TOOLCHAIN_SOURCE")
    sources=frozen_source(cslib,p)
    library=mine_lemmas(sources)
    out.mkdir(parents=True,exist_ok=True)
    # Save discovered (but untrusted) library separately from qualified proof
    # methods, allowing audit of what came from actual source text.
    (out/"source-lemma-index.json").write_text(encode(library))
    history=[]
    budget=p["constructor"]["max_independent_native_invocations_total"]
    timeout=p["constructor"]["timeout_seconds_per_trial"]
    structural=p["constructor"]["basic_structural_lemmas"]
    retained=[]
    results=[]
    baseline_events=[]
    for goal in p["target_goals"]:
        stage=goal["stage"]
        # Measure strong local standard tactics with identical native source.
        baseline_solutions=[]
        for baseline in ("rfl","simp","simp_all","grind","aesop"):
            ok,_=method_trial(cslib,p,goal,baseline,out,
                "baseline",timeout,history,budget)
            if ok:
                baseline_solutions.append(baseline)
        baseline_events.append({"stage":stage,"method_ties":baseline_solutions})

        previous=tuple(retained)
        reused=False
        tactic_used=None
        script=None
        winners=[]
        if previous:
            for tactic in tactic_variants(previous,structural):
                ok,source=method_trial(cslib,p,goal,tactic,out,
                    "previous",timeout,history,budget)
                if ok:
                    reused=True
                    tactic_used=tactic
                    script=source
                    break
        if not reused:
            pool=candidates(
                library,goal["statement"],retained,
                count=p["constructor"]["max_candidate_source_lemmas"]
            )
            found=False
            # Bounded sorted search: minimize number of newly acquired
            # source rewrites before cost of tactics. Candidate names are
            # extracted from the immutable ORIGINAL upstream source, never
            # from a human-provided solution list.
            for count in range(1,p["constructor"]["max_new_source_lemmas_per_stage"]+1):
                if found:break
                for additions in itertools.combinations(pool,count):
                    if found:break
                    new_refs=tuple(retained)+additions
                    for tactic in tactic_variants(new_refs,structural):
                        ok,source=method_trial(cslib,p,goal,tactic,out,
                            "candidate",timeout,history,budget)
                        if ok:
                            tactic_used=tactic
                            script=source
                            winners=list(additions)
                            found=True
                            break
            if not found:
                status={
                    "stage":stage,"goal_id":goal["goal_id"],
                    "status":"UNKNOWN_NATIVE_METHOD_NOT_FOUND",
                    "old_method_reachable":False,
                    "baseline_tactics":baseline_solutions,
                    "prior_method":list(previous),
                    "candidate_lemma_pool":pool
                }
                results.append(status)
                break
        assert script is not None and tactic_used is not None
        proof=out/(stage.lower()+".lean")
        proof.write_text(script)
        # Minimality/reach proof: deleting each newly licensed source lemma
        # from the JUST-qualified proof plan must lose validity. This is
        # plan-relative method dependence, not global semantic impossibility.
        deletions=[]
        for lemma in winners:
            mutated=tactic_used.replace(lemma+", ","").replace(
                ", "+lemma,"").replace(lemma,"")
            ok,_=method_trial(cslib,p,goal,mutated,out,
                "deletion",timeout,history,budget)
            deletions.append({"lemma":lemma,"candidate_passed_without":ok})
        if winners and any(x["candidate_passed_without"] for x in deletions):
            # Do not promote a superfluous source operator.
            results.append({
                "stage":stage,"goal_id":goal["goal_id"],
                "status":"UNKNOWN_NOT_CAUSALLY_REQUIRED",
                "deletions":deletions
            })
            break
        retained.extend(winners)
        row={
            "stage":stage,"goal_id":goal["goal_id"],"status":"PASS_SCOPED",
            "source_lemmas_retained":list(retained),
            "new_method_primitives":winners,
            "previous_exact_program_reused":reused,
            "source_lemma_deletion_checks":deletions,
            "accepted_tactic_program":tactic_used,
            "native_proof_path":proof.name,
            "native_proof_sha256":digest(proof.read_bytes()),
            "verified_native":True,
            "baseline_ties":baseline_solutions,
            "original_goal":goal["statement"],
            "stage_native_trials":sum(row["stage"]==stage for row in history)
        }
        results.append(row)
        # Earned source-theorem memory only after exact native checking.
        (out/"retained-method-grammar.json").write_text(
            encode({"schema":"metalogic.method-grammar-memory.v1",
                "qualified_source_commit":p["upstream"]["commit"],
                "source_lemmas":retained,
                "qualifications":[{"stage":r["stage"],"native_proof_sha256":r.get("native_proof_sha256"),
                    "new_primitives":r.get("new_method_primitives",[])}
                    for r in results if r["status"]=="PASS_SCOPED"],
                "publisher_authority":"NONE"}))
    (out/"candidate.lean").unlink(missing_ok=True)
    full=len(results)==len(p["target_goals"]) and all(
        x["status"]=="PASS_SCOPED" for x in results)
    gain=sum(bool(x.get("new_method_primitives")) for x in results)
    report={
        "schema":"metalogic.typed-source-method-grammar-result.v1",
        "protocol_raw_sha256":digest(raw),
        "exact_upstream_sha":p["upstream"]["commit"],
        "source_module_sha256s":{row["path"]:row["git_blob"] for row,_ in sources},
        "native_source_theorem_count":len(library),
        "native_theorem_names_were_mined":True,
        "native_goal_scoped_results":results,
        "native_feedback_trials":history,
        "native_call_count":len(history),
        "native_baseline_controls":baseline_events,
        "stage_passed":sum(x["status"]=="PASS_SCOPED" for x in results),
        "method_grammar_grew_at":gain,
        "scientific_status":"WARRANTED_BOUNDED_NATIVE_METHOD_GRAMMAR_EXTENSION" if full else "UNKNOWN",
        "source_self_modified_generator":"NO_HUMAN_CODE_WRITTEN_AFTER_FREEZE",
        "meta_generator_substrate_human_written":True,
        "source_theorems_are_original_preexisting":True,
        "general_autonomous_L7":"UNKNOWN",
        "novel_mathematical_theorem":"NOT_CLAIMED",
        "strong_equally_informed_stateless_baseline":"UNMEASURED",
        "source_publication_or_action_authority":"NONE",
        "scope":"three user-frozen native goals over original CSLib product/LTS/powerset semantic transports",
    }
    (out/"report.json").write_text(encode(report))
    print("UPSTREAM_MINED_SOURCE_LEMMAS="+str(len(library)))
    print("QUALIFIED_STAGES="+str(report["stage_passed"]))
    print("NATIVE_LEAN_CALLS="+str(len(history)))
    for row in results:
        print("STAGE_RESULT="+json.dumps({
            k:row.get(k) for k in (
              "stage","goal_id","status","new_method_primitives",
              "previous_exact_program_reused","baseline_ties")}))
    return full


def main():
    a=argparse.ArgumentParser()
    a.add_argument("--cslib",type=Path,required=True)
    a.add_argument("--protocol",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    x=a.parse_args()
    passed=run(x.cslib.resolve(),x.protocol.resolve(),x.out.resolve())
    if not passed:
        raise SystemExit(2)


if __name__=="__main__":
    main()
