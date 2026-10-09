"""Source-indexed F-collision proof-search prototype and exact checker.

UNKNOWN means that the three-rule grammar supplies no certificate. It is
not a Collatz counterexample. Arbitrary finite certificate soundness is
formalized separately in Collatz.FSwapGrammar.
"""
from __future__ import annotations
import hashlib
import json


def T(n: int) -> int:
    return n // 2 if n % 2 == 0 else (3*n+1)//2


def iterate(n: int, t: int) -> int:
    for _ in range(t):
        n = T(n)
    return n


def compile_certificate(n: int, allow_swap: bool = True,
                        budget: int = 512) -> dict | None:
    if n <= 0 or budget <= 0:
        raise ValueError('positive source and budget required')
    current, clock, steps = n, 0, []
    for _ in range(budget):
        if current % 4 == 2:
            steps.append({'rule': 'close', 'source': current})
            return {'source': n, 'clock': clock+2, 'steps': steps}
        if current % 2 == 1:
            steps.append({'rule': 'odd', 'source': current})
            current, clock = T(current), clock+1
        elif allow_swap and current % 64 == 56:
            steps.append({'rule': 'swap', 'source': current})
            current, clock = 8+9*((current-56)//64), clock+6
        else:
            return None
    return None


def verify_certificate(c: dict) -> int:
    current, clock = c['source'], 0
    if not isinstance(current, int) or current <= 0:
        raise ValueError('nonpositive source')
    steps = c['steps']
    if not steps:
        raise ValueError('empty proof')
    for index, row in enumerate(steps):
        if row['source'] != current:
            raise ValueError('source coupling lost')
        rule = row['rule']
        if rule == 'odd' and current % 2 == 1:
            if T(3*current+2) != 3*T(current)+2:
                raise ValueError('odd transport failed')
            current, clock = T(current), clock+1
        elif rule == 'swap' and current % 64 == 56:
            q = (current-56)//64
            child = 8+9*q
            if iterate(current,6) != 3*child+2:
                raise ValueError('first branch swap failed')
            if iterate(3*current+2,6) != child:
                raise ValueError('second branch swap failed')
            current, clock = child, clock+6
        elif rule == 'close' and current % 4 == 2:
            if index != len(steps)-1:
                raise ValueError('proof continues after closure')
            if iterate(current,2) != iterate(3*current+2,2):
                raise ValueError('critical pair failed')
            clock += 2
        else:
            raise ValueError('inadmissible rule')
    if steps[-1]['rule'] != 'close' or clock != c['clock']:
        raise ValueError('wrong final rule or clock')
    if iterate(c['source'],clock) != iterate(3*c['source']+2,clock):
        raise ValueError('original trajectories did not coincide')
    return clock


def affine_check(k: int, s: int) -> dict:
    if min(k,s) < 0:
        raise ValueError('run lengths must be nonnegative')
    bits = [1]*k + [0]*3 + [1]*(s+3) + [0,0]
    depth, r = len(bits), 0
    for j, bit in enumerate(bits):
        if iterate(r,j)%2 != bit:
            r += 1<<j
    M = 1<<depth
    x,a,y,b = r,M,3*r+2,3*M
    for bit in bits:
        if a%2 or b%2 or x%2 != bit:
            raise ValueError('affine parity not uniform')
        x,a = (x//2,a//2) if x%2==0 else ((3*x+1)//2,3*a//2)
        y,b = (y//2,b//2) if y%2==0 else ((3*y+1)//2,3*b//2)
    if (x,a)!=(y,b):
        raise ValueError('all-offset collision failed')
    for q in (0,1,7):
        n = r+M*q
        c = compile_certificate(n)
        if c is None or verify_certificate(c)!=depth:
            raise ValueError('grammar did not derive expected collision')
    return dict(initial_odd_run=k,following_odd_run=s,
                residue=r,modulus=M,clock=depth,
                common_intercept=x,common_slope=a)


def main() -> None:
    grid = [affine_check(k,s) for k in (0,1,2,6,12,31)
            for s in (0,1,2,7,20,31)]
    witness = compile_certificate(22652991)
    assert witness is not None and verify_certificate(witness)==15
    result = dict(schema='COLLATZ_SOURCE_INDEXED_F_SWAP_GRAMMAR',
                  status='EXACT_EXECUTABLE_AND_SYMBOLIC_REGRESSIONS',
                  family_grid=grid,certificate=witness,
                  smaller_source=15909919,predecessor_clock=24,
                  common_endpoint=40821428,
                  phase_counterexample=dict(source=3,F_source=11,
                                            at_time_10=[2,1]),
                  universal_grammar_coverage=False,
                  global_collatz='UNKNOWN',qed=False)
    assert iterate(15909919,24)==iterate(22652991,15)==40821428
    payload=json.dumps(result,sort_keys=True,separators=(',',':')).encode()
    result['payload_sha256']=hashlib.sha256(payload).hexdigest()
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=='__main__':
    main()
