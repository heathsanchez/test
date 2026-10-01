"""Cut one guarded exit from a live cell; preserve its unclosed complement.

No claim of eventual guard availability, finite kernel emptiness, or QED.
The universal source-lift theorem is checked separately by Lean.
"""
import hashlib
import json
import collatz_crystal_parameter_quotient_v25 as bank
from collatz_consequential_splice_reuse_v57 import FRONTIER, orbit

BASE = 3403982007377265835376667
LOWER = 1516043288339062768749913
MODULUS = 2**83

def compiled_exit(d,r,u,enabled=True):
    """Execute the qualified cylinder rule without a trajectory search."""
    n=bank.N0+bank.NC*(r+2**d*u)
    if not enabled or n<BASE or (n-BASE)%MODULUS:
        return None
    w=(n-BASE)//MODULUS
    return dict(theorem='live_splice_guard_exit',source=str(n),
        lower=str(LOWER+2*3**51*w),common_step=83)

def main():
    assert BASE == bank.N0 + bank.NC*900
    original = bank.classify_cell(10,900)
    assert not original['terminal']
    # The first direct/quarter-splice exit of the nominated base trajectory.
    for k in range(1,80):
        x,_=orbit(BASE,k)
        assert x >= BASE
        assert not (x%8==5 and (x-1)//4<BASE)
    assert orbit(BASE,80)==(4*LOWER+1,51)
    common,q=orbit(BASE,83)
    assert (common,q)==(2274064932508594153124870,52)
    assert orbit(LOWER,1)[0]==common
    assert LOWER%2==1 and 0<LOWER<BASE
    assert 2*3**51 <= MODULUS

    # Exact guard on the original live family, not a new state coordinate.
    # n = BASE + NC*1024*u lies in this class iff 2^14 divides u.
    assert bank.NC*1024 == 2**69*3**8
    assert pow(3**8,-1,2**14)*3**8 % 2**14 == 1
    # One less source bit loses odd quarter-owner admission on this word.
    assert orbit(BASE+2**82,80)==(4*LOWER+1+4*3**51,51)
    assert orbit(BASE+2**82,80)[0]%8==1
    replays=[]
    for u in (0,1,2,7,27,243,65537):
        n=BASE+MODULUS*u
        p=LOWER+2*3**51*u
        assert 0<p<n and orbit(n,83)[0]==orbit(p,1)[0]
        replays.append(dict(u=u,n=str(n),p=str(p)))

    # Actual capability application and removal ablation on the live cell.
    # The old cell-level bank returns UNKNOWN; this executable guard earns
    # exits for its admitted subfamily with zero future trajectory search.
    executed=[]
    for u in (0,1,16384,32768):
        hit=compiled_exit(10,900,u)
        assert bool(hit)==(u%16384==0)
        assert compiled_exit(10,900,u,enabled=False) is None
        if hit:
            n=int(hit['source']);p=int(hit['lower'])
            assert 0<p<n and orbit(n,83)[0]==orbit(p,1)[0]
        executed.append(dict(u=u,enabled='EXIT' if hit else 'UNKNOWN',disabled='UNKNOWN'))

    # Reclose the frozen 128 cells without pretending partial removal
    # eliminates a whole cell. Symbolic congruence compatibility is exact.
    closed=live=whole_new=partial=0
    for r in FRONTIER:
        for bit in (0,1):
            child=r+512*bit
            old=bank.classify_cell(10,child)
            n=bank.N0+bank.NC*child
            s=bank.NC*1024
            compatible=(n-BASE)%__import__('math').gcd(s,MODULUS)==0
            entire=compatible and s%MODULUS==0
            closed+=old['terminal']
            live+=not old['terminal']
            whole_new+=entire and not old['terminal']
            partial+=compatible and not entire and not old['terminal']
    assert (closed,live,whole_new,partial)==(13,115,0,1)
    result=dict(schema='COLLATZ_LIVE_SPLICE_GUARD_V58',
        original_live_cell=dict(depth=10,r=900,interface=original['interface']),
        failed_guard='step-66 endpoint is 7 mod 8; uniform lower-source reverse search also fails',
        nominated_exit=dict(step=80,common_step=83,odd_count=52),
        universal_class=dict(base=str(BASE),modulus=str(MODULUS),lower=str(LOWER),lower_slope=str(2*3**51)),
        applicability_on_original_cell='u = 0 mod 16384; equivalently t = 900 mod 16777216',
        surviving_complement='t = 900 mod 1024 AND t != 900 mod 16777216',
        fixed_word_quarter_guard_minimum_source_bits=83,
        removed_incidental_source_factor=3**8,
        reclosure=dict(input=128,previously_closed=closed,live_cells=live,
            newly_closed_whole_cells=whole_new,live_cells_with_new_certified_subcylinder=partial),
        replays=replays,
        executed_capability_ablation=executed,
        evidence_boundary='universal dyadic cylinder is Lean checked separately; prospective eventual availability unproved',
        global_collatz='UNKNOWN')
    result['certificate_sha256']=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__':main()
