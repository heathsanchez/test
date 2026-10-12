#!/usr/bin/env python3
"""Source-identical V11 search-rule transfer to MathGraph finite oracle."""
from __future__ import annotations
from itertools import combinations,permutations
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys

V11_BLOB="0f7fb6b837cd65aa86b5fef7c097196fc0df4845"
SOURCE_CORPUS_SHA="a8c05bda6e6bbfb15fdfe21bc8954fd9c5d790f8a31b2df04c8a3ef83b04b609"
V11_COMMIT="5b10a853240356b2b00258334ef378e0850eb42c"
TARGET_COMMIT="280b0200af53033d6f4ee0e1c31e7c2f4f32c172"

def git_blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def load_v11(path):
    actual=git_blob(path.read_bytes())
    assert actual==V11_BLOB,("SOURCE_ALGORITHM_MUTATED",actual)
    spec=importlib.util.spec_from_file_location("original_v11",path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.POLICY=={"bound":True,"include_first":True,"mode":"both_branches","prune":False}
    return m

def eligible(rows,removed,witness):
    selected=255^removed
    for r in rows:
        d=r["delta"]
        if d is None:continue
        filtered=d&selected
        if bool(filtered)!=bool(d):return False
        if witness and d and (d&-d)!=(filtered&-filtered):return False
    return True

def hereditary(table):
    assert table[0]
    for mask,ok in enumerate(table):
        if ok:
            for i in range(8):
                if mask>>i&1:assert table[mask&~(1<<i)]

def exchange_witness(table):
    for a in range(256):
        if not table[a]:continue
        for b in range(256):
            if not table[b] or a.bit_count()>=b.bit_count():continue
            if not any(table[a|(1<<i)] for i in range(8)
                       if b>>i&1 and not (a>>i&1)):
                return [a,b]
    return None

def greedy(table,order):
    chosen=0
    for i in order:
        if table[chosen|(1<<i)]:chosen|=1<<i
    return chosen

def source_witness(solver,predicate,best):
    """Recover witness through *unchanged* V11 solver on hereditary contractions."""
    chosen=0;need=best;calls=0
    for i in range(8):
        if not need:break
        candidate=chosen|(1<<i)
        if not predicate(candidate):continue
        remaining=tuple(range(i+1,8))
        def contraction(local):
            full=candidate
            for bit,index in enumerate(remaining):
                if local>>bit&1:full|=1<<index
            return predicate(full)
        extension=solver.learned_exact_rank(len(remaining),contraction)
        calls+=1
        if extension+1==need:
            chosen=candidate
            need-=1
    assert chosen.bit_count()==best and predicate(chosen)
    return chosen,calls

def test_family(name,cases,solver,bridge,finite):
    rows,oldcost=bridge.source_rows(cases,bridge.target_module,finite)
    checked=[]
    for witness in (False,True):
        checks=0
        def predicate(m):
            nonlocal checks
            checks+=1
            return eligible(rows,m,witness)
        table=[predicate(i) for i in range(256)]
        hereditary(table)
        exact=max(i.bit_count() for i in range(256) if table[i])
        original_calls=checks
        measured=solver.learned_exact_rank(8,predicate)
        assert measured==exact,(name,witness,measured,exact)
        chosen,recursions=source_witness(solver,predicate,exact)
        assert table[chosen]
        selected=[i for i in range(8) if not(chosen>>i&1)]
        if witness:
            native=bridge.check_scoped_policy(selected,rows,cases,finite)
            assert native["scoped_native_status_and_witness_matches"]==len(cases)
        else:
            mismatch=0
            for c in cases:
                t=finite.compare_finite_formulas(c["source"],c["formal"],["p","q","r"])
                s,w,_=bridge.evaluate_scoped(selected,c,finite)
                assert s==t["result"]
                mismatch+=int(w!=t["witness"])
            native={"verdicts_preserved":len(cases),
                    "first_witness_changes":mismatch,
                    "warrant":"NOT_AUTHORIZED_AS_EXACT_NATIVE_EVIDENCE"}
        witness_counter=None
        for order in permutations(range(8)):
            tested=greedy(table,order)
            if tested.bit_count()<exact:
                witness_counter={"order":list(order),
                                 "greedy_removed":tested.bit_count(),
                                 "exact_removed":exact}
                break
        exchange=exchange_witness(table)
        if witness_counter:assert exchange is not None
        checked.append({
          "objective":"EXACT_STATUS_AND_FIRST_WITNESS" if witness else "VERDICT_ONLY",
          "native_cases":len(cases),
          "full_original_semantic_evaluations":oldcost["full_semantic_assignments"],
          "original_source_v11_reused_byte_identical":True,
          "optimal_removed_count":measured,
          "optimal_basis_size":len(selected),
          "optimal_basis":selected,
          "strong_stateless_optimum":exact,
          "source_v11_oracle_calls_for_search_and_recovery":checks-original_calls,
          "independent_exhaustive_contract_checks":original_calls,
          "source_v11_self_reduction_steps":recursions,
          "greedy_failure":witness_counter,
          "matroid_exchange_counterexample":exchange,
          "native_outcome":native,
          "old_target_full8_remains_authoritative":True,
          "no_strict_gain_over_complete_stateless":True})
    return checked

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--msi-root",type=Path,required=True)
    cli.add_argument("--target-root",type=Path,required=True)
    cli.add_argument("--source-repair",type=Path,required=True)
    cli.add_argument("--output",type=Path,required=True)
    args=cli.parse_args()
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    from research.flash_v15 import transfer as bridge
    _,target,finite,msi=bridge.imported_authorities(args.msi_root,args.target_root)
    solver=load_v11(args.source_repair)
    bridge.target_module=target
    development=target.generated_cases()
    assert hashlib.sha256(target.canonical_bytes(development)).hexdigest()==SOURCE_CORPUS_SHA
    observed={"native_development_420":development}
    for seed in (0x4D475649,0x4D475650):
        saved=target.SEED;target.SEED=seed
        try:future=target.generated_cases()
        finally:target.SEED=saved
        assert len(future)==420
        observed["frozen_future_"+hex(seed)]=future
    p,q,r=({"var":k} for k in ("p","q","r"))
    adversary={"id":"v16_alltrue_corner","source":{"const":False},
               "formal":{"and":[p,{"and":[q,r]}]},"generator_intent":"different"}
    observed["frozen_future_with_adversary"]=observed["frozen_future_0x4d475650"]+[adversary]
    rows={name:test_family(name,c,solver,bridge,finite) for name,c in observed.items()}
    weak,strict=rows["native_development_420"]
    assert weak["optimal_basis_size"]==6 and weak["greedy_failure"] is not None
    assert weak["matroid_exchange_counterexample"] is not None
    assert weak["native_outcome"]["first_witness_changes"]>0
    assert strict["optimal_basis_size"]==7
    assert all(x["original_source_v11_reused_byte_identical"] and
               x["optimal_removed_count"]==x["strong_stateless_optimum"]
               for family in rows.values() for x in family)
    report={
       "status":"PASS_V16_UNCHANGED_SOURCE_QUALIFIED_CONSTRUCTOR_TRANSFER",
       "source":{"repo":"heathsanchez/test","commit":V11_COMMIT,"git_blob":V11_BLOB,
                 "prior_ci_run":38201499353},
       "target":{"repo":"metalogiclabs/mathgraph","commit":TARGET_COMMIT,
                 "native_frozen_corpus_sha256":SOURCE_CORPUS_SHA,"prior_ci":38012157151},
       "cross_project_results":rows,
       "source_msi_observation_check":msi,
       "frozen_future_seeds":["0x4D475649","0x4D475650"],
       "limitations":[
         "Source V11 typed branch grammar supplied, no open-ended generator invention",
         "New target task is scoped minimum basis construction, not a previously unproved Boolean theorem",
         "Status-only 6-of-8 changes first witnesses and must fail closed for full native contract",
         "Source V11 solver reused byte-for-byte; target-independent adapter is newly authored",
         "Strong full-information stateless solver ties all optimum results",
         "Original full eight-assignment target verifier remains universal for the declared Bool3 DSL",
         "No total-lifetime amortization of V11 source acquisition or real-world physics"
       ]
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"status":report["status"],
        "development":{"status_only_basis_size":weak["optimal_basis_size"],
             "native_witness_basis_size":strict["optimal_basis_size"],
             "greedy_failure":weak["greedy_failure"]},
        "protected":[{"name":name,"weak_size":r[0]["optimal_basis_size"],
                      "native_size":r[1]["optimal_basis_size"]}
                      for name,r in rows.items() if name!="native_development_420"]},sort_keys=True))

if __name__=="__main__":main()
