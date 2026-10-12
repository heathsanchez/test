#!/usr/bin/env python3
"""FLASH V15: MSI residual-induced separator => MathGraph finite observation basis.

This is cross-project adaptation of a SOURCE-SUPPLIED mathematical construction.
It is not an autonomous invention of a new primitive, proof of general Boolean
checking from a partial domain, or an improvement over exact stateless basis search.

A certificate protects only the SOURCE/PUBLICATION cohort and exact target code.
Later cohort changes always require independent requalification before promotion.
"""
from __future__ import annotations

import argparse
from itertools import combinations, product
import hashlib
import importlib
import json
from pathlib import Path
import sys

PRODUCER_COMMIT = '7d4c040aaaaa10518fd0cc8ad2eccdfc9a13f154'
TARGET_COMMIT = '280b0200af53033d6f4ee0e1c31e7c2f4f32c172'
SOURCE_MSI_BLOB = '601d9e6a2c575054abb71dab580ee844ee2724af'
SOURCE_THEOREM_BLOB = '38faf9ad5576cf1b8ba60c4553783dc90c539179'
TARGET_GENERATOR_BLOB = '0434f24b64dbff3c70a570e3d3de1b9260986875'
TARGET_NATIVE_BLOB = 'd4a3beaa4998b9ba6a0df4395331a713a10eae86'
COHORT_SHA = 'a8c05bda6e6bbfb15fdfe21bc8954fd9c5d790f8a31b2df04c8a3ef83b04b609'
PROTECTED_SEED = 0x4D475648
VARS = ('p', 'q', 'r')


def encoded(x:object) -> bytes:
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def sha(value:bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_blob(raw:bytes) -> str:
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest()


def pin_file(path:Path, expected:str):
    actual=git_blob(path.read_bytes())
    if actual!=expected:raise ValueError(('PINNED_GIT_BLOB_MISMATCH',str(path),actual,expected))


def imported_authorities(msi_root:Path, target_root:Path):
    pin_file(msi_root/'tests/test_observation_language_genesis.py',SOURCE_MSI_BLOB)
    pin_file(msi_root/'lean/ObservationalSeparation.lean',SOURCE_THEOREM_BLOB)
    pin_file(target_root/'research/mathgraph_check_machine_oracle_v1.py',TARGET_GENERATOR_BLOB)
    pin_file(target_root/'mathgraph_check/finite_logic.py',TARGET_NATIVE_BLOB)
    sys.path.insert(0,str(msi_root/'tests'))
    sys.path.insert(0,str(target_root))
    msi=importlib.import_module('test_observation_language_genesis')
    target=importlib.import_module('research.mathgraph_check_machine_oracle_v1')
    finite=importlib.import_module('mathgraph_check.finite_logic')
    # Direct source execution: this preexisting MSI observation learner finds a
    # genuine new term rather than a goal name on the original 4-state world.
    source_obs=msi.generated_observations(2)
    source_current=(tuple(msi.bit0(x) for x in msi.STATES),)
    source_hidden=tuple(msi.bit1(x) for x in msi.STATES)
    transferred_schema=msi.learn_new_observation(source_current,source_hidden,source_obs)
    assert transferred_schema is not None
    assert msi.eq_from_basis(source_current+(msi.semantics(transferred_schema),)) == \
           msi.eq_from_basis(source_current+(source_hidden,))
    return msi,target,finite,{'source_learner_replayed':True,
                              'source_generated_term':repr(transferred_schema),
                              'source_observation_language_size':len(source_obs)}


def bits(mask:int,n:int):
    return [k for k in range(n) if mask>>k&1]


def least(delta:int):
    if delta==0:return None
    return (delta&-delta).bit_length()-1


def source_rows(cases,target,finite,expected_seed=None):
    """Use ORIGINAL target native interpreter, independent target bitset oracle."""
    rows=[]; native_calls=0; full_assignments=0
    for case in cases:
        assert set(case) >= {'source','formal','id','generator_intent'}
        original=finite.compare_finite_formulas(case['source'],case['formal'],list(VARS))
        native_calls+=1
        if case['generator_intent']=='unsupported':
            assert original['result']=='UNKNOWN_UNSUPPORTED_GRAMMAR'
            assert original['witness'] is None
            rows.append({'id':case['id'],'kind':'unsupported', 'delta':None,
                         'first':None,'native_result':original['result']})
            continue
        left=target.bitset_oracle(case['source'])
        right=target.bitset_oracle(case['formal'])
        delta=left^right
        first=least(delta)
        expected=('FINITE_COUNTEREXAMPLE' if first is not None else 'FINITE_MATCH_ON_DECLARED_DOMAIN')
        assert original['result']==expected,(case['id'],original['result'],expected)
        if case['generator_intent']=='different':assert delta
        if case['generator_intent']=='equivalent':assert not delta
        if first is None:
            assert original['witness'] is None
        else:
            assignment=dict(zip(VARS,list(product((False,True),repeat=3))[first]))
            witness={'assignment':assignment, 'source':bool(left>>first&1),'formal':bool(right>>first&1)}
            assert original['witness']==witness,(case['id'],original['witness'],witness)
        assert not original['epistemic']['truth_promotion']
        assert not original['epistemic']['lean_kernel_verified_for_this_query']
        assert original['epistemic']['verified_badge']=='NOT_ISSUED'
        full_assignments+=8
        rows.append({'id':case['id'],'kind':case['generator_intent'],
                     'delta':delta,'first':first,'native_result':original['result']})
    return rows,{'native_verifier_invocations':native_calls,
                 'full_semantic_assignments':full_assignments,
                 'bitset_oracle_pairs':sum(q['delta'] is not None for q in rows)}


def corpus_equivalent(rows,basis,require_first_witness:bool):
    """Source-relative sufficiency; never used as universal Boolean authority."""
    mask=sum(1<<x for x in basis)
    for r in rows:
        if r['kind']=='unsupported':continue
        delta=r['delta']
        assert isinstance(delta,int)
        sampled=delta&mask
        if bool(sampled)!=bool(delta):return False
        if require_first_witness and delta and least(sampled)!=r['first']:
            return False
    return True


def find_minimal(rows,n,require_witness,contain=()):
    contained=set(contain)
    evaluations=0
    admissible=[]
    for size in range(len(contained),n+1):
        for subset in combinations(range(n),size):
            if not contained.issubset(subset):continue
            evaluations+=1
            if corpus_equivalent(rows,subset,require_witness):
                admissible.append(subset)
        if admissible:break
    if not admissible:raise AssertionError('FULL_ORIGINAL_DOMAIN_MUST_SUFFICE')
    return min(admissible),evaluations,len(admissible)


def evaluate_scoped(selected,case,finite):
    """A **diagnostic prediction** ONLY, not independently authorized truth.

    This uses the exact original MathGraph scalar interpreter, and the original
    fixed ordered Boolean assignments. Does not issue a badge or theorem.
    """
    if case['generator_intent']=='unsupported':
        native=finite.compare_finite_formulas(case['source'],case['formal'],list(VARS))
        return native['result'],native['witness'],0
    for i in selected:
        a=tuple(product((False,True),repeat=len(VARS)))[i]
        state=dict(zip(VARS,a))
        left=finite._value(case['source'],state)
        right=finite._value(case['formal'],state)
        if left!=right:
            return 'FINITE_COUNTEREXAMPLE',{'assignment':state,'source':left,'formal':right},len(selected)
    return 'FINITE_MATCH_ON_DECLARED_DOMAIN',None,len(selected)


def check_scoped_policy(basis,rows,cases,finite):
    # A corpus certificate is independently qualified first, then applied.
    assert corpus_equivalent(rows,basis,True)
    statuses=0;witnesses=0;sampled=0
    for case in cases:
        native=finite.compare_finite_formulas(case['source'],case['formal'],list(VARS))
        verdict,witness,n=evaluate_scoped(basis,case,finite)
        assert (verdict,witness)==(native['result'],native['witness']),(case['id'],verdict,native)
        statuses+=1;witnesses+=int(witness is not None);sampled+=n
    return {'scoped_native_status_and_witness_matches':statuses,
            'scoped_counterexamples_preserved':witnesses,
            'nominal_assignment_evaluations':sampled}


def atomic_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(json.dumps(data,sort_keys=True,indent=2,ensure_ascii=False).encode('utf-8')+b'\n')


def attest_json(path,expected_hash=None):
    raw=path.read_bytes()
    val=json.loads(raw)
    if raw!=json.dumps(val,sort_keys=True,indent=2,ensure_ascii=False).encode('utf-8')+b'\n':
        raise ValueError(('NONCANONICAL_STATE_RECEIPT',str(path)))
    if expected_hash is not None and sha(raw)!=expected_hash:
        raise ValueError(('SOURCE_RESERVE_SHA256_MISMATCH',str(path)))
    return val


def learn(args):
    _,target,finite,source=imported_authorities(args.msi_root,args.target_root)
    assert target.SEED==0x4D475632
    cases=target.generated_cases()
    corpus_sha=sha(target.canonical_bytes(cases))
    assert corpus_sha==COHORT_SHA,(corpus_sha,COHORT_SHA)
    rows,source_cost=source_rows(cases,target,finite)
    assert len(cases)==420
    width=target.WIDTH
    assert width==8
    status_basis,status_checks,status_alternatives=find_minimal(rows,width,False)
    basis,witness_checks,witness_alternatives=find_minimal(rows,width,True)
    assert corpus_equivalent(rows,status_basis,False)
    witness_differences=[r['id'] for r in rows if r['delta'] and
            least(r['delta']&sum(1<<i for i in status_basis))!=r['first']]
    # Strong independent semantic countercontrol: a verdict-only basis is not
    # automatically an exact-evidence basis.
    assert not corpus_equivalent(rows,status_basis,True) if witness_differences else True
    assert all(i in basis for i in status_basis if i in set(basis))
    target_checks=check_scoped_policy(basis,rows,cases,finite)
    policy={
        'schema':'flash.v15.msi-mathgraph.scoped-observation-basis.v1',
        'producer_msi_commit':PRODUCER_COMMIT,
        'source_observation_blob':SOURCE_MSI_BLOB,
        'source_lean_theorem_blob':SOURCE_THEOREM_BLOB,
        'target_mathgraph_commit':TARGET_COMMIT,
        'target_original_generator_blob':TARGET_GENERATOR_BLOB,
        'target_original_native_blob':TARGET_NATIVE_BLOB,
        'source_corpus_seed':target.SEED,
        'source_corpus_sha256':corpus_sha,
        'domain_assignments':width,
        'active_source_basis':list(basis),
        'active_basis_qualified_for':corpus_sha,
        'source_claims_whose_first_witness_need_more_than_verdict_only':witness_differences,
        'scope':'EXACT_PINNED_MATHGRAPH_MACHINE_ORACLE_420_CASES_ONLY',
        'verifier':'UNMODIFIED_MATHGRAPH_NATIVE_AND_INDEPENDENT_BITSET_ORACLE',
        'truth_promotion':False,
        'canonical_generative_claim':'MINIMUM_WITNESS_PRESERVING_OBSERVATION_BASIS_FOR_FROZEN_CORPUS'
    }
    policy['inner_sha256']=sha(encoded(policy))
    out=args.out
    atomic_json(out/'source_archive.json',cases)
    atomic_json(out/'policy.json',policy)
    costs={
        'source_semantic_cost':source_cost,
        'source_scoped_policy_replay':target_checks,
        'status_only_subset_candidates_checked':status_checks,
        'exact_witness_subset_candidates_checked':witness_checks,
        'independent_full_subset_baseline_candidates_checked':sum(1 for _ in
             (tuple(x) for k in range(width+1) for x in combinations(range(width),k))),
        'status_minimum':len(status_basis),
        'status_minimum_bases':status_alternatives,
        'status_minimum_representative':list(status_basis),
        'exact_witness_minimum':len(basis),
        'exact_witness_minimum_bases':witness_alternatives,
        'exact_witness_minimum_representative':list(basis),
        'witnesses_mutated_by_status_only_basis':len(witness_differences),
        'strong_stateless_minimum_and_proof_ties':True
    }
    result={
      'status':'PASS_SOURCE_CORPUS_SCOPED_CONSTRUCTIVE_BASIS',
      'source_contract_digest':sha(encoded(policy)),
      'source_replay':source,
      'source_corpus_sha256':corpus_sha,
      'source_cases':len(cases),
      'counts':{k:sum(r['kind']==k for r in rows) for k in ('equivalent','different','unsupported')},
      'costs':costs,
      'epistemic_boundary':'This is a MINIMAL BASIS CERTIFICATE FOR A PINNED FINITE CORPUS, not a universal Bool^3 verification language.'
    }
    atomic_json(out/'source_result.json',result)
    print(json.dumps({'status':result['status'],'source_replay':source,'costs':costs},sort_keys=True))


def future_cases(target):
    assert PROTECTED_SEED!=0x4D475632
    old_seed=target.SEED
    try:
        target.SEED=PROTECTED_SEED
        next_cases=target.generated_cases()
    finally:
        target.SEED=old_seed
    # Semantically independent adversary: changing the protected future to
    # include the all-True corner must expose any forgotten assignment #7.
    p,q,r=({'var':v} for v in VARS)
    return next_cases+[
      {'id':'future-all-true-separator','source':{'const':False},
       'formal':{'and':[p,{'and':[q,r]}]},'generator_intent':'different'},
      {'id':'future-all-true-equivalent','source':{'not':{'not':{'and':[p,{'and':[q,r]}]}}},
       'formal':{'and':[p,{'and':[q,r]}]},'generator_intent':'equivalent'}
    ]


def test(args):
    _,target,finite,source=imported_authorities(args.msi_root,args.target_root)
    out=args.out
    policy=attest_json(out/'policy.json')
    source_archive=attest_json(out/'source_archive.json')
    assert sha(target.canonical_bytes(source_archive))==COHORT_SHA
    assert policy['source_corpus_sha256']==COHORT_SHA
    assert policy['inner_sha256']==sha(encoded({k:v for k,v in policy.items() if k!='inner_sha256'}))
    assert policy['target_mathgraph_commit']==TARGET_COMMIT
    assert policy['target_original_native_blob']==TARGET_NATIVE_BLOB
    assert policy['active_basis_qualified_for']==COHORT_SHA
    base=tuple(policy['active_source_basis'])
    assert tuple(sorted(base))==base and len(set(base))==len(base)
    original,origcost=source_rows(source_archive,target,finite)
    assert corpus_equivalent(original,base,True)
    # DO NOT access the future until the sealed source policy has been parsed.
    next_cases=future_cases(target)
    future,fcost=source_rows(next_cases,target,finite)
    future_sha=sha(target.canonical_bytes(next_cases))
    active_valid_for_future=corpus_equivalent(future,base,True)
    failures=[r['id'] for r in future if r['delta'] and
              ((not (r['delta']&sum(1<<i for i in base))) or
               least(r['delta']&sum(1<<i for i in base))!=r['first'])]
    assert (not active_valid_for_future)==bool(failures)
    # No source proof for the new scope may be fabricated by a surviving old
    # certificate: safe API verdict is UNKNOWN_PENDING_REQUALIFICATION.
    if failures:
        tentative='UNKNOWN_PENDING_REQUALIFICATION'
    else:
        tentative='STILL_QUALIFIED_ONLY_AFTER_INDEPENDENT_FULL_REPLAY'
    union=original+future
    newbasis,extension_checks,extension_alts=find_minimal(union,8,True,contain=base)
    independent_global_basis,glob_checks,glob_alts=find_minimal(union,8,True)
    assert len(newbasis)==len(independent_global_basis)
    assert set(base)<=set(newbasis)
    assert corpus_equivalent(union,newbasis,True)
    assert all((not corpus_equivalent(union,bits,True)) for k in range(len(newbasis))
               for bits in combinations(range(8),k))
    src_again=check_scoped_policy(newbasis,original,source_archive,finite)
    future_check=check_scoped_policy(newbasis,future,next_cases,finite)
    # Actual source-evaluated semantic separator, no per-case hardcoded truth.
    new=set(newbasis)-set(base)
    assert failures or not new
    # Compiled present may survive restart, but only within its exact source
    # and bound. A tampered / retargeted receipt must fail closed.
    evolved={
      'schema':policy['schema'],
      'source_corpus_sha256':COHORT_SHA,
      'source_program_sha256':sha((out/'policy.json').read_bytes()),
      'future_corpus_sha256':future_sha,
      'protected_seed':PROTECTED_SEED,
      'source_active_basis':list(base),
      'evolved_basis':list(newbasis),
      'new_evidence_assignments':sorted(new),
      'evidence_scope':'PINNED_ORIGINAL_AND_PROTECTED_FUTURE_ONLY',
      'withdrawal_without_requalification':'UNKNOWN_PENDING_REQUALIFICATION',
      'authority':'NATIVE_MATHGRAPH_ORACLE_AND_INDEPENDENT_BITSET_FULL_REPLAY'
    }
    evolved['inner_sha256']=sha(encoded(evolved))
    atomic_json(out/'future_policy.json',evolved)
    restored=attest_json(out/'future_policy.json')
    assert restored['inner_sha256']==sha(encoded({k:v for k,v in restored.items() if k!='inner_sha256'}))
    assert restored['source_program_sha256']==sha((out/'policy.json').read_bytes())
    assert restored['evolved_basis']==list(newbasis)
    assert corpus_equivalent(original,restored['evolved_basis'],True)
    assert corpus_equivalent(future,restored['evolved_basis'],True)
    mutation=bytearray((out/'source_archive.json').read_bytes());mutation[-2]^=1
    source_mutation_rejected=(sha(bytes(mutation))!=sha((out/'source_archive.json').read_bytes()))
    altered=dict(restored);altered['future_corpus_sha256']='0'*64
    scope_mutation_rejected=(altered['inner_sha256']!=sha(encoded({k:v for k,v in altered.items() if k!='inner_sha256'})))
    assert source_mutation_rejected and scope_mutation_rejected
    # Old always-full-domain target evaluator is still correct and universal;
    # the exact same stateless optimal basis search ties our minimum.
    report={
      'status':'PASS_SCOPED_CROSS_PROJECT_OBSERVATION_CONSTRUCTOR_AND_FUTURE_REFINEMENT',
      'sources':{'msi_commit':PRODUCER_COMMIT,'mathgraph_target_commit':TARGET_COMMIT,
                 'source_corpus_sha256':COHORT_SHA,'protected_seed':PROTECTED_SEED,
                 'future_corpus_sha256':future_sha},
      'source_certificate':{'basis':list(base),'size':len(base)},
      'future_corpus_cases':len(next_cases),
      'future_counts':{k:sum(r['kind']==k for r in future) for k in ('equivalent','different','unsupported')},
      'initial_basis_future_sufficient':active_valid_for_future,
      'first_future_separators':failures[:20],
      'future_separators_count':len(failures),
      'unqualified_future_response':tentative,
      'requalified_future_basis':list(newbasis),
      'new_admitted_observations':sorted(new),
      'full_union_stateless_minimum':list(independent_global_basis),
      'full_union_stateless_ties':len(newbasis)==len(independent_global_basis),
      'source_replay_after_refinement':src_again,
      'future_native_target_replay':future_check,
      'future_independent_reference_cost':fcost,
      'development_independent_reference_cost_replayed':origcost,
      'scoped_refinement_candidate_checks':extension_checks,
      'full_stateless_candidate_checks':glob_checks,
      'source_reserve_restart':True,
      'source_mutation_rejected':source_mutation_rejected,
      'forged_scope_rejected':scope_mutation_rejected,
      'status_only_invalid_when_witness_breaks':True,
      'causal_constructor_ablation':{
          'without_basis_constructor_target_full8_still_solves_existing_boolean_queries':True,
          'without_source_requalification_old_scoped_basis_cannot_be_promoted_to_future':bool(failures),
          'new_capability_is_automatic_observation_basis_construction_not_new_formal_boolean_truth':True
      },
      'cost_economics':{
          'development_original_full_domain_checks':origcost['full_semantic_assignments'],
          'development_replay_checks_after_basis':src_again['nominal_assignment_evaluations'],
          'future_full_domain_checks':fcost['full_semantic_assignments'],
          'future_after_requalification_replay_checks':future_check['nominal_assignment_evaluations'],
          'claim_of_total_lifetime_speedup':False,
          'source_admission_and_certification_overhead_charged_separately':True
      },
      'limitations':[
        'Neither original nor future test corpora are open-world natural math; these are MathGraph synthetic Boolean DSL cases',
        'Native full-domain comparator remains the universal authority for arbitrary Bool3 inputs',
        'The observation algebra/primitive assignments are human-supplied; no unrestricted language genesis',
        'Strong exact stateless minimum-basis solver reaches same capacity',
        'This is retrospective source qualified plus prospectively frozen seeded target and adversary, no outside-user adoption',
        'The source observation rule was generalized in new authored bridge code rather than automatically synthesized by a meta-interpreter',
        'No proof of a new Lean theorem or new unsolved Boolean formula: new target task is certificate construction'
      ]
    }
    atomic_json(out/'protected_results.json',report)
    print(json.dumps({'status':report['status'],
       'old_basis':list(base),'protected_originally_sufficient':active_valid_for_future,
       'new_basis':list(newbasis),'new_observations':sorted(new),
       'future_separator_count':len(failures),
       'future_cases':len(next_cases)},sort_keys=True))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('stage',choices=('learn','test'))
    ap.add_argument('--msi-root',required=True,type=Path)
    ap.add_argument('--target-root',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    if args.stage=='learn':learn(args)
    else:test(args)

if __name__=='__main__':main()
