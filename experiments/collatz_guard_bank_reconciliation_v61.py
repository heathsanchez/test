"""Prevent a diagnostic frontier from replacing the warranted residual.

Consume the qualified full bank, prove finite prefix partition equality, and
measure guarded consequences after saturation. Never count rediscovery as gain.
"""
import argparse
import hashlib
import json
from pathlib import Path
from fractions import Fraction
import collatz_crystal_parameter_quotient_v25 as bank
from collatz_consequential_splice_reuse_v57 import FRONTIER

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--bank-dir',required=True)
    args=ap.parse_args();root=Path(args.bank_dir)
    result=json.loads(next(root.rglob('backward-cover-result.json')).read_text())
    certs=json.loads(next(root.rglob('backward-cover-certificates.json')).read_text())
    claimed=result.pop('certificate_sha256')
    digest=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert claimed==digest=='bca7a47524a79847d7a4aa0471d167e6fe7571247254ba9ab07f7533fe05b05f'
    assert len(certs)==3294
    slots=[False]*(2**18)
    for c in certs:
        assert 0<=c['r']<2**c['h'] and c['h']<=18
        for r in range(c['r'],2**18,2**c['h']):
            assert not slots[r]
            slots[r]=True
    residual=set(result['unresolved_cells'])
    assert {r for r,v in enumerate(slots) if not v}==residual
    assert sum(slots)==239659 and len(residual)==22485
    # Join the kernel bank with the independently qualified frozen V25 bank.
    # Keeping 22485 as the whole current residual would discard these laws.
    frozen_live=[]
    for r in FRONTIER:
        for bit in (0,1):
            child=r+512*bit
            hit=bank.classify_cell(10,child)
            if not hit['terminal']:
                frozen_live.append(child)
            else:
                e=hit['exit'];n=bank.N0+bank.NC*child;s=bank.NC*1024
                if e['kind']=='D':assert e['endpoint0']<n and e['endpointSlope']<=s
                elif e['kind']=='M':assert 0<e['reverse']['p0']<n and e['reverse']['pSlope']<=s
                else:assert e['kind']=='S' and e['endpoint0']%8==5 and e['endpoint0']<=4*n
    assert len(frozen_live)==115
    joined=sorted(r for r in residual if r%1024 in frozen_live)
    assert set(joined)<=residual
    prior=[(i,c) for i,c in enumerate(certs) if c['h']<=12 and 3972%2**c['h']==c['r']]
    assert len(prior)==1
    i,c=prior[0]
    assert (c['r'],c['h'],c['kind'],c['k'],c['q'])==(3972,12,'S',71,45)
    assert not any(r%4096==3972 for r in residual)
    # V58 is a deeper subset of a genuinely unresolved full-bank leaf.
    assert 900 in residual
    baseline=Fraction(239659,2**18)
    after_v58=baseline+Fraction(1,2**24)
    assert after_v58==Fraction(15338177,16777216)
    live900=sorted(r for r in residual if r%1024==900)
    assert len(live900)==114
    # This check precedes all proposal generation in the retained state.
    state=dict(schema='COLLATZ_GUARD_BANK_RECONCILIATION_V61',
        objective='universal original-source eventual exit/progress',
        authority=dict(branch='collatz-backward-symbolic-cover-chunks-20260930',
            commit='e547e2ae0eee71be4647a8282d6b8fa870d00458',run=36663027013,
            artifact=11074639536,result_sha256=claimed),
        saturation=dict(certified_laws=3294,depth=18,closed_slots=239659,residual_slots=22485),
        joined_reclosure=dict(frozen_v25_depth=10,frozen_v25_live_cells=115,
            depth18_residual_after_both_banks=len(joined),
            residual_residues=joined,
            boundary='join of these two qualified banks; other ROS warrants are not asserted exhausted'),
        v60_lineage=dict(prior_certificate_index=i,prior_certificate=c,
            incremental_original_family_closure=0,
            retained_gain='dyadic generalization and zero-search execution; original-family guard already qualified'),
        v58_lineage=dict(original_family_extra_coverage='1/16777216',
            baseline_coverage=str(baseline),saturated_plus_v58_coverage=str(after_v58)),
        active_900_residual=dict(full_bank_residues=live900,
            extra_exclusion='t=900 modulo 16777216',
            boundary='finite upper residual; no all-future bad-source claim'),
        proposal_admission='reject rediscovery of a saturated guarded law as new mathematical closure',
        next_obligation='all-depth natural-source bar or source-coherent progress on the saturated complement',
        universal_admission='UNKNOWN',universal_progress='UNKNOWN',global_collatz='UNKNOWN')
    state['certificate_sha256']=hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()
    print(json.dumps(state,indent=2,sort_keys=True))

if __name__=='__main__':main()
