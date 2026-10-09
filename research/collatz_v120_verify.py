"""Independent exact-affine V120 verifier.

Do not accept generator assertions as evidence. Reconstruct BOTH forward
F branches and the complete reverse source path symbolically. No reliance on
sample offsets for the all-q claim; samples are optional regression controls.
This checker does NOT assert exhaustive all-positive-source coverage.
"""
import argparse
from collections import Counter
import hashlib
import json
from research.collatz_v120_phase_elimination import (
    PRODUCT, DYADIC, TERNARY, v112_predecessor, shortcut
)

def affine_T(x,a):
    assert a%2==0,("nonuniform shortcut parity",x,a)
    if x%2==0:return x//2,a//2
    return (3*x+1)//2,3*a//2

def check_rule(rule):
    n=rule["residue"];m=rule["modulus"]
    assert 0<n<m and PRODUCT%m==0
    source=(n,m)
    partner=(3*n+2,3*m)
    clock=0
    assert rule["collision_path"][-1]=="close"
    for op in rule["collision_path"]:
        if op=="odd":
            assert source[0]%2==1 and source[1]%2==0
            assert partner==(3*source[0]+2,3*source[1])
            source=affine_T(*source)
            partner=affine_T(*partner)
            clock+=1
        elif op=="close":
            assert source[0]%4==2 and source[1]%4==0
            for _ in range(2):
                source=affine_T(*source)
                partner=affine_T(*partner)
            clock+=2
        else:
            raise AssertionError(("unverified F grammar constructor",op))
    assert source==partner and clock==rule["collision_clock"]
    x,a=3*n+2,3*m
    word=rule["reverse_word"]
    for op in word:
        if op=="E":x,a=2*x,2*a
        elif op=="O":
            assert x>=2 and x%3==2 and a%3==0
            old_x,old_a=x,a
            x,a=(2*x-1)//3,2*a//3
            assert 3*x+1==2*old_x and 3*a==2*old_a
        else:raise AssertionError(op)
    assert (x,a)==(rule["predecessor"],rule["slope"])
    assert len(word)==rule["reverse_clock"]
    assert 0<x<n and 0<a<=m
    # These are only regression checks. The affine guards are the universal
    # proof schema for all nonnegative family offsets.
    for q in (0,1,9):
        src=n+m*q
        earlier=x+a*q
        assert 0<earlier<src
        A=src;B=3*src+2
        for _ in range(clock):A=shortcut(A);B=shortcut(B)
        assert A==B
        for _ in word:earlier=shortcut(earlier)
        assert earlier==3*src+2

def verify(source):
    assert source["schema"]=="COLLATZ_V120_PHASE_AWARE_ELIMINATION"
    assert source["source_modulus"]==PRODUCT
    payload=dict(source)
    digest=payload.pop("payload_sha256")
    assert hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()==digest
    rules=source["rules"];records=source["records"]
    assert len(rules)==149 and len(records)==4408
    for r in rules:check_rule(r)
    assert len(set(r["reverse_word"] for r in rules))==17
    assert len(set(tuple(r["collision_path"]) for r in rules))==9
    keys=set()
    for record in records:
        n=record["residue"]
        assert n not in keys
        keys.add(n)
        assert v112_predecessor(n) is None
        assert not(n%16==11 and n%729==45)
        # Re-derive the exact compact rule lift and both source coefficients.
        possible=[rule for rule in rules
            if n%rule["modulus"]==rule["residue"]
            and record["reverse_word"]==rule["reverse_word"]
            and record["collision_clock"]==rule["collision_clock"]
            and record["collision_path"]==rule["collision_path"]]
        assert any(
            record["predecessor"] ==
                rule["predecessor"]+rule["slope"]*
                    ((n-rule["residue"])//rule["modulus"])
            and record["slope"] ==
                rule["slope"]*(PRODUCT//rule["modulus"])
            for rule in possible
        ),("lost source lineage",record)
    assert len(keys)==4408
    assert source["v112_covered"]==4617
    assert source["v112_unresolved"]==164439
    assert source["earlier_F_covered"]==93
    assert source["unknown_classes"]==159938
    assert 4617+93+4408+159938==144*1174
    rules_blob=json.dumps(rules,sort_keys=True,separators=(",",":")).encode()
    verdict=dict(schema="COLLATZ_V120_INDEPENDENT_SYMBOLIC_QUALIFICATION",
        exact_rule_count=149,exact_new_crt_families=4408,
        reverse_word_types=17,collision_path_types=9,
        old_v112_covered=4617,prior_F_covered=93,
        remaining_unknown_crt=159938,source_modulus=PRODUCT,
        all_offset_affine_rules_verified=True,
        all_individual_Lean_witnesses_checked=False,
        universal_original_source_bar_proved=False,
        global_collatz="UNKNOWN",qed=False,
        rules_sha256=hashlib.sha256(rules_blob).hexdigest(),
        generated_evidence_sha256=digest)
    verdict["certificate_sha256"]=hashlib.sha256(
        json.dumps(verdict,sort_keys=True,separators=(",",":")).encode()
    ).hexdigest()
    return verdict

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",required=True)
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    with open(args.input) as f:source=json.load(f)
    result=verify(source)
    with open(args.out,"w") as f:json.dump(result,f,sort_keys=True,indent=2)
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
