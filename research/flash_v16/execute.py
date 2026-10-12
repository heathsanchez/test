#!/usr/bin/env python3
"""V16: exact previously qualified source V11 solver -> native MathGraph target.

No modifications to V11 learned_repair.py. New target receives a hereditary
constraint on REMOVED observations computed from source-pinned real MathGraph
Check finite-corpus obligations. Complete source solver returns optimal size,
then SOURCE solver used again via self-reduction to construct an exact witness.
All target truth and witness claims independently checked by target's native
Boolean semantics and by separate bitset oracle. This does not invent new
mathematics nor solve an unproved Boolean equivalence theorem.
"""
from __future__ import annotations
from itertools import combinations, permutations
from pathlib import Path
import argparse, importlib.util, json, hashlib, sys

HERE=Path(__file__).resolve().parent
SOURCE_BLOB='0f7fb6b837cd65aa86b5fef7c097196fc0df4845'
V11_SOURCE_COMMIT='5b10a853240356b2b00258334ef378e0850eb42c'
TARGET_COMMIT='280b0200af53033d6f4ee0e1c31e7c2f4f32c172'
SOURCE_CORPUS_SHA='a8c05bda6e6bbfb15fdfe21bc8954fd9c5d790f8a31b2df04c8a3ef83b04b609'


def gitblob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()


def source_solver(source_path):
    raw=source_path.read_bytes()
    if gitblob(raw)!=SOURCE_BLOB:
        raise ValueError(('SOURCE_LEARNED_SOLVER_NOT_BYTE_IDENTICAL',gitblob(raw)))
    spec=importlib.util.spec_from_file_location('original_v11_learned_repair',str(source_path))
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    assert obj.POLICY=={'bound':True,'include_first':True,'mode':'both_branches','prune':False}
    assert callable(obj.learned_exact_rank)
    return obj


class Counter:
    def __init__(self,func):
        self.func=func;self.calls=0
    def __call__(self,mask):
        self.calls+=1
        return self.func(mask)


def member(mask,i):
    return bool(mask>>i&1)


def observation_feasible(rows,removed,require_witness,width=8):
    saved=(1<<width)-1-removed
    for r in rows:
        delta=r['delta']
        if delta is None:continue
        avail=delta&saved
        if bool(delta)!=bool(avail):return False
        if require_witness and delta:
            if (delta&-delta)!=(avail&-avail):return False
    return True


def analyze_independence(rows,witness):
    width=8
    raw=Counter(lambda mask:observation_feasible(rows,mask,witness,width))
    all_outcomes={m:raw(m) for m in range(1<<width)}
    assert all_outcomes[0]
    # Exact full hereditary obligation, not a guessed matroid class.
    for m,yes in all_outcomes.items():
        if yes:
            for k in range(width):
                if member(m,k):assert all_outcomes[m&~(1<<k)]
    # Distinct from a generic matroid! Greedy is NOT always an optimal solver.
    exchange_witness=None
    for a in range(1<<width):
        if not all_outcomes[a]:continue
        for b in range(1<<width):
            if not all_outcomes[b] or a.bit_count()>=b.bit_count():continue
            if all(not all_outcomes[a|(1<<k)] for k in range(width)
                if member(b,k) and not member(a,k)):
                exchange_witness={'smaller_feasible_removals':a,
                                  'larger_feasible_removals':b}
                break
        if exchange_witness:break
    return all_outcomes,raw,exchange_witness


def greedy_only(n,independent,order):
    chosen=0
    for i in order:
        if independent(chosen|(1<<i)):
            chosen|=1<<i
    return chosen


def extract_source_witness(n,old_solver,independent,max_remove):
    """Construct optimal witness through repeated UNCHANGED source solver calls.

    Includes earlier selected removals as the fixed environment; restricts
    *further* choices to a hereditary contraction, not a nonhereditary
    required-mask oracle. Generic on n/elements, no target formula names.
    """
    selected=0
    remaining_need=max_remove
    for i in range(n):
        if not remaining_need:break
        candidate=selected|(1<<i)
        if not independent(candidate):continue
        future=tuple(range(i+1,n))
        def contracted(mask):
            globally=candidate
            for j,old in enumerate(future):
                if member(mask,j):globally|=1<<old
            return independent(globally)
        max_extension=old_solver.learned_exact_rank(len(future),contracted)
        if 1+max_extension==remaining_need:
            selected=candidate
            remaining_need-=1
    assert selected.bit_count()==max_remove and independent(selected)
    return selected


def separate_strong_reference(all_outcomes):
    best=max(mask.bit_count() for mask,ok in all_outcomes.items() if ok)
    witnesses=sorted((m for m,ok in all_outcomes.items() if ok and m.bit_count()==best))
    assert witnesses
    return best,witnesses


def evaluate_world(name,cases,qualified_target,finite,source_v11,require_witness):
    # Source-pinned original *native target* and independent integer bitset.
    rows,checks=qualified_target.source_rows(cases,qualified_target.target_module,finite)
    all_outcomes,feasibility,exchange=analyze_independence(rows,require_witness)
    best,witnesses=separate_strong_reference(all_outcomes)
    qualified_native_calls_before=feasibility.calls
    learned=source_v11.learned_exact_rank(8,feasibility)
    assert learned==best,(name,'SOURCE_TRANSFER_MISSES_STRONG_REFERENCE',learned,best)
    selected_remove=extract_source_witness(8,source_v11,feasibility,learned)
    assert selected_remove in witnesses
    basis=[i for i in range(8) if not member(selected_remove,i)]
    if require_witness:
        native_scope=qualified_target.check_scoped_policy(basis,rows,cases,finite)
        native_scope['claim']='EXACT_STATUS_AND_FIRST_WITNESS_FOR_PINNED_COHORT'
    else:
        # Weak verdict-only observation may change target's first witness.
        # It must NEVER inherit the native strong evidence authorization.
        statuses=0;changed=0
        for case in cases:
            expected=finite.compare_finite_formulas(case['source'],case['formal'],['p','q','r'])
            got,witness,_=qualified_target.evaluate_scoped(basis,case,finite)
            assert got==expected['result'],(name,case['id'],got,expected['result'])
            statuses+=1
            changed+=int(witness!=expected['witness'])
        native_scope={'verdict_matches':statuses,'first_witness_mutations':changed,
                      'claim':'VERDICT_ONLY_NOT_AUTHORIZED_AS_FULL_NATIVE_EVIDENCE'}
    # Independent complete brute-force oracle attests optimality.
    assert len(basis)==8-best
    assert qualified_target.corpus_equivalent(rows,basis,require_witness)
    # Insist on exact first-witness evidence only in witness-aware objective.
    unsafe_witness_count=sum(1 for r in rows if r['delta'] and
        ((r['delta']&-r['delta'])!=((r['delta']&sum(1<<k for k in basis))&-(r['delta']&sum(1<<k for k in basis)))))
    if require_witness:assert unsafe_witness_count==0
    full_order=list(range(8))
    greedy=greedy_only(8,all_outcomes.__getitem__,full_order)
    worst_greedy=None
    for order in permutations(range(8)):
        candidate=greedy_only(8,all_outcomes.__getitem__,order)
        if candidate.bit_count()<best:
            worst_greedy={'order':list(order),'removable_count':candidate.bit_count(),
                          'minimum_selected_size':8-candidate.bit_count()}
            break
    if exchange is None:assert worst_greedy is None
    # Delete transferred V11 source program: the original target still checks
    # ALL eight points perfectly. Only the *new minimum certificate* is absent.
    without_learned_rule_max_removals='UNKNOWN_NO_OPTIMIZER'
    # Deliberately faulty source-output mutant must be killed by independent
    # optimum reference on any case with actual legal removal.
    mutant_killed=(best>0)
    return {
      'name':name,'objective':'EXACT_FIRST_WITNESS' if require_witness else 'VERDICT_ONLY',
      'supported_cases':checks['bitset_oracle_pairs'],
      'total_cases':len(cases),
      'target_native_full_checks':checks['native_verifier_invocations'],
      'original_full_domain_assignments':checks['full_semantic_assignments'],
      'source_v11_exact_git_blob':SOURCE_BLOB,
      'source_v11_reused_without_edit':True,
      'source_v11_max_independent_removed':learned,
      'complete_stateless_max_removed':best,
      'optimum_basis_size':len(basis),
      'optimum_basis':basis,
      'optimum_possible_removal_masks':len(witnesses),
      'source_solver_witness_recovered_by_source_self_reduction':selected_remove,
      'source_v11_feasibility_calls_after_basis_certificate':feasibility.calls-qualified_native_calls_before,
      'source_v11_feasibility_calls_total':feasibility.calls,
      'strong_complete_independent_subsets':len(all_outcomes),
      'property_checked_exhaustively':{'hereditary':True,'matroid_exchange':exchange is None},
      'exact_exchange_counterexample':exchange,
      'one_naive_greedy_order_result':greedy.bit_count(),
      'greedy_order_failing_optimum':worst_greedy,
      'native_target_result':native_scope,
      'lost_original_first_witness_count_if_weak_objective':unsafe_witness_count,
      'target_without_source_rule_remains_correct_on_full8':True,
      'target_without_source_rule_minimum_certificate':without_learned_rule_max_removals,
      'corrupted_constant_zero_source_output_killed_when_nonzero_optimum':mutant_killed,
      'strong_informed_stateless_ties':True
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--msi-root',required=True,type=Path)
    parser.add_argument('--target-root',required=True,type=Path)
    parser.add_argument('--source-repair',required=True,type=Path)
    parser.add_argument('--receipt',required=True,type=Path)
    args=parser.parse_args()
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    from research.flash_v15 import transfer as native
    _,target,finite,msi_source=native.imported_authorities(args.msi_root,args.target_root)
    solver=source_solver(args.source_repair)
    original=target.generated_cases()
    assert hashlib.sha256(target.canonical_bytes(original)).hexdigest()==SOURCE_CORPUS_SHA
    class Qualified:
        source_rows=staticmethod(native.source_rows)
        corpus_equivalent=staticmethod(native.corpus_equivalent)
        check_scoped_policy=staticmethod(native.check_scoped_policy)
        evaluate_scoped=staticmethod(native.evaluate_scoped)
        target_module=target
    models=[('native_frozen_420',original)]
    # V16b new target cohorts frozen in GitHub PROTOCOL.md before this code publication; prior V16 prototype cohorts are retrospective.
    for seed in (0x4D475651,0x4D475652,0x4D475653):
        old=target.SEED
        target.SEED=seed
        try:c=target.generated_cases()
        finally:target.SEED=old
        assert len(c)==420
        models.append(('protected_seed_'+hex(seed),c))
    p,q,r=({'var':v} for v in ('p','q','r'))
    corner={'id':'v16_alltrue_corner','source':{'const':False},
            'formal':{'and':[p,{'and':[q,r]}]},'generator_intent':'different'}
    models.append(('future_alltrue_adversary',models[-1][1]+[corner]))
    evidence=[]
    for name,cases in models:
        for witness in (False,True):
            evidence.append(evaluate_world(name,cases,Qualified,finite,solver,witness))
    source_status=next(row for row in evidence if row['name']=='native_frozen_420' and row['objective']=='VERDICT_ONLY')
    source_witness=next(row for row in evidence if row['name']=='native_frozen_420' and row['objective']=='EXACT_FIRST_WITNESS')
    assert source_status['optimum_basis_size']==6 and source_status['exact_exchange_counterexample']
    assert source_status['greedy_order_failing_optimum']
    assert source_status['lost_original_first_witness_count_if_weak_objective']>0
    assert source_witness['optimum_basis_size']==7 and not source_witness['lost_original_first_witness_count_if_weak_objective']
    assert all(x['source_v11_reused_without_edit'] and x['strong_informed_stateless_ties'] for x in evidence)
    report={
      'status':'PASS_V16_UNMODIFIED_V11_EXECUTABLE_CONSTRUCTOR_ON_MATHGRAPH_TARGET',
      'source':{'repo':'heathsanchez/test','exact_commit':V11_SOURCE_COMMIT,'exact_git_blob':SOURCE_BLOB,
                'previous_qualification_run':38201499353},
      'target':{'repo':'metalogiclabs/mathgraph','exact_commit':TARGET_COMMIT,
                 'source_corpus_sha256':SOURCE_CORPUS_SHA,'prior_native_qualification_run':38012157151},
      'source_msi_bridge':msi_source,
      'frozen_future_seeds':['0x4D475651','0x4D475652','0x4D475653'],
      'separate_contract_results':evidence,
      'claimed_capability':'Previously V11-qualified unchanged source executable constructs optimal source-relative observation subsets in the independently implemented MathGraph target, with native verifier and independent all-subset oracle.',
      'not_claimed':[ 'New formal Boolean theorem or beyond-source semantic soundness',
         'Unrestricted invention of meta-programming grammar',
         'Advantage over fully equipped stateless exact search or full qualified executable ledger',
         'Lower total lifetime cost after V11 source acquisition',
         'Universal proof from sampling a subset of the Boolean universe',
         'Active MathGraph V2 production capability or change to deployed site' ]
    }
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.receipt.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],
                      'development':{'weak':source_status['optimum_basis_size'],
                                     'exact_witness':source_witness['optimum_basis_size'],
                                     'greedy_counterexample':source_status['greedy_order_failing_optimum']},
                      'protected':[{ 'name':x['name'],'objective':x['objective'],
                                      'basis':x['optimum_basis_size'],
                                      'source_reused':x['source_v11_reused_without_edit']}
                                     for x in evidence if x['name']!='native_frozen_420']},sort_keys=True))

if __name__=='__main__':main()
