"""V179 exact source reduction to V178's sparse genuine-future normal form.

Every move is a V178 certified source-index reduction by a V177
all-offset REAL Collatz two-clock equality and strictly smaller
positive source. The deterministic *first applicable* rule is chosen
only as a canonical audit policy. Lean V179 separately proves any
valid descent sequence must terminate at an irreducible source and
preserve actual future-equivalence and CollatzGood in both directions.

No convergence oracle is invoked. Reaching a small irreducible
representative does NOT establish its terminal convergence.
The G7 synthetic model fails the actual +1 source equations and
cannot inherit the true-map normalizer's claims.

Global Collatz UNKNOWN — NO QED.
"""
from __future__ import annotations
import hashlib,json,random
from collections import Counter
from pathlib import Path


def T(n:int)->int:
    assert n>0
    return n//2 if n%2==0 else (3*n+1)//2


def G7(n:int)->int:
    assert n>0
    return n//2 if n%2==0 else (3*n+7)//2


def advance(n:int,k:int,F=T)->int:
    for _ in range(k):
        n=F(n)
    return n


def first_applicable(n:int,bank):
    for L,res,base,p,i,j,a,b,R,gain in bank:
        if n>=base and (n-base)%L==0:
            w=(n-base)//L
            smaller=p+R*w
            assert 0<smaller<n
            assert n==base+L*w
            return smaller,(base,p,i,j,w)
    return None,None


def normal_form(n:int,bank,replay=True):
    assert n>0
    start=n
    steps=0
    chain_hash=hashlib.sha256()
    first_three=[]
    while True:
        p,witness=first_applicable(n,bank)
        if p is None:
            return {
              'starting_source':start,'irreducible_source':n,
              'strict_source_descent_steps':steps,
              'edge_sha256':chain_hash.hexdigest(),
              'first_moves':first_three}
        base,small,i,j,w=witness
        if replay:
            assert advance(n,i)==advance(p,j), (start,n,p,witness)
        assert p<n
        chain_hash.update(f'{n}:{p}:{i}:{j}:{w}\n'.encode())
        if len(first_three)<3:
            first_three.append({
              'original_source':n,'smaller_real_source':p,
              'original_clock':i,'smaller_clock':j,
              'base_rule_source':base,'base_rule_companion':small,
              'affine_offset':w})
        n=p
        steps+=1
        assert steps <= start


def main():
    source=Path('research/collatz_v178_compact_bank.json')
    payload=json.loads(source.read_text())
    bank=payload['selected']
    assert len(bank)==205
    M=payload['M']
    N=payload['N']
    rng=random.Random(179)
    tested=0
    maxdepth=0
    endcounts=Counter()
    depths=Counter()
    above_activation=0
    examples=[]
    for n in range(1,(1<<18)):
        r=normal_form(n,bank,True)
        p=r['irreducible_source']
        assert 0<p<=n
        assert first_applicable(p,bank)[0] is None
        if p>=N:
            above_activation+=1
            assert not any(
              p%entry[0]==entry[1] for entry in bank)
        depths[r['strict_source_descent_steps']]+=1
        maxdepth=max(maxdepth,r['strict_source_descent_steps'])
        endcounts[p]+=1
        tested+=1
        if n in (1,2,3,5,7,27,31,63,127,703,16383,65535,131071,262143):
            examples.append(r)
    # Very large genuine sources are still reduced exactly using
    # full-precision Python integers and the same verified lift formula.
    extreme=[]
    for n in [10**9+1,10**12+2,(1<<64)-1,(1<<100)-1]:
        r=normal_form(n,bank,True)
        extreme.append({
          'starting_source':str(n),
          'irreducible_source':str(r['irreducible_source']),
          'strict_source_descent_steps':r['strict_source_descent_steps']})

    # A rule for the TRUE T map cannot certify G7 source5:
    # T^2(5)=4 but G7^2(5)=20, and G7's second cycle persists.
    assert advance(5,2,T)==4
    assert advance(5,2,G7)==20
    assert [G7(z) for z in (5,11,20,10)]==[11,20,10,5]
    assert {5,11,20,10}.isdisjoint({7,14})

    out={
      'schema':'COLLATZ_V179_ALL_SOURCE_SPARSE_FUTURE_NORMAL_FORM_AUDIT',
      'rule_bank_N':N,'rule_bank_period':M,'kernel_checked_rule_count':len(bank),
      'finite_original_sources_exact_reduced':tested,
      'max_strict_descent_steps_observed':maxdepth,
      'histogram_of_strict_descent_steps':dict(sorted(depths.items())),
      'distinct_irreducible_normal_forms_tested':len(endcounts),
      'normal_forms_at_or_above_activation_height':above_activation,
      'highest_multiplicity_single_normal_form':max(endcounts.values()),
      'extreme_big_nat_replays':extreme,
      'selected_examples':examples,
      'every_admitted_edge_has_real_clocks_and_strict_smaller_source':True,
      'totality_of_reduction_for_all_n_proved_separately_in_Lean':True,
      'terminal_convergence_of_residuals_proved':False,
      'source_sample_is_not_universal_Collatz_proof':True,
      'synthetic_G7_second_future_basin_protected':True,
      'global_collatz':'UNKNOWN','qed':False
    }
    Path('evidence').mkdir(exist_ok=True)
    p=Path('evidence/v179-exact.json')
    p.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({
      'schema':out['schema'],'checked':tested,'maxsteps':maxdepth,
      'distinct_residuals':len(endcounts),
      'global_collatz':out['global_collatz']
    },sort_keys=True))

if __name__=='__main__':
    main()
