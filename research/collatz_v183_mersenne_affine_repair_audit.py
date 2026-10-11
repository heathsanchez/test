"""V183: reuse the true terminal seed of the FIRST joint V178/V181
Mersenne residual as a sound, source-attached infinite all-offset
two-clock LOWER-source family. Quantify actual NEW candidate-source
residue exclusions and verify it does NOT swallow the whole
unbounded V182 residual Mersenne exponent family.

Original exact facts:
T^193(2097151)=2, odds=109, 3^109<2^193.

For every w>=0:
 T^193(2097151+2^193*w)=2+3^109*w
 and 2+3^109*w<2097151+2^193*w.

This excludes a progression ONLY as the HYPOTHETICAL LEAST bad
source. For w>0 the smaller companion may itself be bad, so
this is NOT convergence for the whole progression.
"""
from __future__ import annotations
import json
from hashlib import sha256
from pathlib import Path


def T(n:int,c:int=1)->int:
    assert n>0
    return n//2 if n%2==0 else (3*n+c)//2


def advance(n:int,k:int,c:int=1)->tuple[int,int]:
    odd=0
    for _ in range(k):
        odd+=n%2
        n=T(n,c)
    return n,odd


def main()->None:
    n0=(1<<21)-1
    L=1<<193
    R=3**109
    assert n0==2097151
    assert (L>R>0)
    assert advance(n0,193)==(2,109)
    assert advance(n0,193,7)[0]!=2
    sample_offsets=(0,1,2,3,7,100,1000,100000,10**12)
    for w in sample_offsets:
        n=n0+L*w
        p=2+R*w
        assert 0<p<n
        assert advance(n,193)[0]==p
        if w:
            assert p!=2
    # The modified S5 one-arrow false map freezes at source5;
    # the true Mersenne proof does not hold under this false law.
    x=n0
    for _ in range(193):
        x=5 if x==5 else T(x)
    assert x==5

    bankpath=Path('research/collatz_v178_compact_bank.json')
    bank=json.loads(bankpath.read_text())
    rules=bank['selected']
    M=bank['M']
    assert M==(1<<12)*3**6 and len(rules)==205
    assert all(M%r[0]==0 for r in rules)
    def covered(rem:int)->bool:
        return any(rem%r[0]==r[1] for r in rules)
    assert not covered(n0%M)
    # New stride L=2^193; combined period is L*729.
    # Each complete w-mod-729 cycle selects one original source
    # from each of the 729 CRT residues above low 12 bits=4095.
    # Of those EXACT 729 sources, 396 were not in V178's bank,
    # so the new all-offset certificate is a genuine NEW subset.
    lifts=[]
    for w in range(729):
        n=n0+L*w
        assert n%(1<<12)==4095
        lifts.append({
           'w':w,
           'source_mod_old_M':n%M,
           'not_covered_by_old_bank':not covered(n%M)
        })
    newly=sum(x['not_covered_by_old_bank'] for x in lifts)
    assert newly==396
    assert len(lifts)-newly==333

    # The V182 joint residual n_(2+243t) is NOT consumed for t>0
    # by this particular 193-clock affine progression, since for
    # t>=1 exponent 21+2430t>=193, so n_m=-1 mod2^193.
    # It differs from n0 modulo L. Computed using modular pow.
    remaining=[]
    for t in (0,1,2,3,9,100,1000000):
        K=21+2430*t
        source_mod_L=(pow(2,K,L)-1)%L
        in_progression=source_mod_L==n0%L
        assert in_progression == (t==0)
        remaining.append({
            'exponent_parameter_t':t,
            'mersenne_exponent_K':K,
            'this_rule_applies':in_progression
        })

    out={
       'schema':'COLLATZ_V183_MERSENNE_TERMINAL_SEED_AFFINE_REPAIR',
       'original_n':n0,
       'terminal_clock':193,
       'terminal_endpoint':2,
       'source_clock_odd_count':109,
       'source_stride':'2^193',
       'companion_stride':'3^109',
       'all_offset_source_rank_guard':True,
       'exact_genuine_source_replays':len(sample_offsets),
       'newly_excluded_residues_per_combined_period':newly,
       'already_excluded_residues_per_combined_period':729-newly,
       'combined_period':'2^193*729',
       'this_rule_does_NOT_cover_all_mersenne_joint_residuals':True,
       'joint_family_noncoverage_controls':remaining,
       'false_G7_and_one_arrow_negative_controls':True,
       'rule_is_not_terminal_certification_of_each_member':True,
       'proof_bank_marginal_density_is_tiny':True,
       'all_source_global_coverage_proved':False,
       'global_collatz':'UNKNOWN','qed':False,
    }
    Path('evidence').mkdir(exist_ok=True)
    Path('evidence/v183-exact.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({
      'schema':out['schema'],
      'newly_excluded_residues_per_new_period':newly,
      'sampled_exact_offsets':len(sample_offsets),
      'global_collatz':'UNKNOWN'
    },sort_keys=True))


if __name__=='__main__':
    main()
