#!/usr/bin/env python3
"""Target-directed reverse certificates, keeping the original Q7/Q14 bank intact.

For hard first crossings with q<n, y<n+q/3<4n/3. A reverse word
p=(a*y-c)/d with a/d<=3/4 and p>0 gives p<n. Search must stop at
that target, not at the earlier and weaker test p<y.
This is finite certificate-family coverage, not a Collatz proof.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from collatz_reverse_predecessor_tree import Cert, T, reverse_apply, enumerate_first_contractions


def enumerate_target(Q: int, numerator: int = 3, denominator: int = 4) -> list[Cert]:
    if not isinstance(Q, int) or isinstance(Q, bool) or not 1 <= Q <= 14:
        raise ValueError('Q must be an integer in 1..14')
    if not 0 < numerator < denominator:
        raise ValueError('target must be strictly between zero and one')
    limit = numerator * 3**Q // denominator
    max_depth = limit.bit_length()-1
    out: list[Cert] = []

    def visit(word: str, a: int, c: int, d: int, odds: int) -> None:
        if word and denominator*a <= numerator*d:
            residue = c * pow(a, -1, d) % d
            out.append(Cert(word,len(word),odds,a,c,d,residue))
            return
        remaining = Q-odds
        # Even the strongest possible continuation (all remaining O) fails.
        if (len(word) >= max_depth or
            denominator*a*2**remaining > numerator*d*3**remaining):
            return
        visit(word+'E',2*a,2*c,d,odds)
        if odds < Q:
            visit(word+'O',2*a,2*c+d,3*d,odds+1)
    visit('',1,0,1,0)
    return out


def verify_certificates(certs: list[Cert], numerator: int=3, denominator: int=4) -> int:
    checks = 0
    for c in certs:
        assert c.a == 2**c.steps and c.d == 3**c.odd_inverse_steps
        assert denominator*c.a <= numerator*c.d
        assert 0 <= c.residue < c.d
        # Symbolically check every positive residue lift y=first+d*t, t>=0.
        first = c.residue if c.residue else c.d
        offset, slope = first, c.d
        for ch in c.word:
            if ch == 'E':
                offset, slope = 2*offset, 2*slope
            else:
                assert (2*offset-1)%3 == 0 and (2*slope)%3 == 0
                offset, slope = (2*offset-1)//3, 2*slope//3
                assert offset>0 and offset%2 == 1 and slope%2 == 0
        assert slope == c.a and c.d*offset+c.c == c.a*first
        # Independent concrete forward replays supplement the symbolic check.
        for y in (first, first+5*c.d, first+17*c.d):
            p = reverse_apply(y,c.word)
            assert p is not None and p>0, (c,y,p)
            assert c.d*p+c.c == c.a*y, (c,y,p)
            z=p
            for _ in c.word: z=T(z)
            assert z==y, (c,y,p,z)
            assert denominator*p <= numerator*y
            checks+=1
    return checks


def coverage(certs: list[Cert], Q: int) -> tuple[bytearray,dict]:
    M=3**Q
    table=bytearray(M)
    for c in certs:
        if c.residue%3 == 1:
            count=(M-1-c.residue)//c.d+1
            table[c.residue:M:c.d]=b'\x01'*count
    total=M//3
    hits=sum(table[1::3])
    by9={str(r):{'covered':sum(table[r::9]),'total':M//9} for r in (1,4,7)} if Q>=2 else {}
    return table,{'covered':hits,'total':total,'uncovered':total-hits,'by_mod9':by9}


def audit(Q: int=14) -> dict:
    legacy=enumerate_first_contractions(Q)
    filtered=[c for c in legacy if 4*c.a<=3*c.d]
    target=enumerate_target(Q)
    checks=verify_certificates(target)
    old, old_stats=coverage(filtered,Q)
    new, new_stats=coverage(target,Q)
    assert all(not a or b for a,b in zip(old,new))
    assert new[1]==0  # The terminal-one residue remains an explicit separator.
    payload='\n'.join(f'{c.word}:{c.a}:{c.c}:{c.d}:{c.residue}' for c in target)
    result={
      'schema':'COLLATZ_TARGET_DIRECTED_REVERSE_AUDIT_V1',
      'base_commit':'f7b90932980c81a63a7b3592cb1e37dce94f93ea',
      'odd_inverse_budget':Q,'target_ratio':[3,4],
      'legacy_first_contraction_count':len(legacy),
      'legacy_ratio_filtered_count':len(filtered),
      'target_directed_count':len(target),
      'positive_integer_replay_checks':checks,
      'symbolically_verified_residue_families':len(target),
      'legacy_ratio_filtered_coverage':old_stats,
      'target_directed_coverage':new_stats,
      'additional_covered_residues':new_stats['covered']-old_stats['covered'],
      'certificate_sha256':hashlib.sha256(payload.encode()).hexdigest(),
      'regression':{'source':11,'endpoint':13,'EOO_predecessor':11,'EOOO_predecessor':7,
                    'scope':'arithmetic target test; not a hypothetical hard Collatz orbit'},
      'uncovered_one_class':{'modulus':3**Q,'residue':1,'positive_signature_example':1+2*3**Q},
      'boundary':'Finite ratio-sufficient coverage on all endpoint residues 1 mod 3; not a count of reachable hard crossings. All-depth certificate soundness and all-depth completeness are distinct.',
      'global_collatz':'UNKNOWN',
    }
    if Q==14:
        assert old_stats['covered']==33723 and old_stats['total']==1594323
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--q',type=int,default=14)
    print(json.dumps(audit(ap.parse_args().q),indent=2,sort_keys=True))
