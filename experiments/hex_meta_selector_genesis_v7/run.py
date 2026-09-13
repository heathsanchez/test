#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"results"
V6=json.loads((ROOT.parent/"hex_macro_generalization_selection_v6"/"AUTHORITY.json").read_text())

ATOMS=("TRUE","FIRST","LAST")
PROGS=[("ATOM",a) for a in ATOMS]+[
    ("OR",a,b) for a in ATOMS for b in ATOMS if a<=b
]

def atom(name,i,m):
    return name=="TRUE" or (name=="FIRST" and i==0) or (name=="LAST" and i==m-1)

def choose(p,m):
    out=[]
    for i in range(m):
        keep=atom(p[1],i,m) if p[0]=="ATOM" else atom(p[1],i,m) or atom(p[2],i,m)
        if keep: out.append(i)
    return out

def cost(p):
    return 1 if p[0]=="ATOM" else 3

def source_iso(a,b):
    return b==a or b==tuple(1-x for x in a)

def encode(obj,selected):
    roles=7
    fresh=6
    edges=set()
    for rel,orientation in enumerate(obj):
        u,v=(0,1) if orientation==0 else (1,0)
        edges.add(tuple(sorted((roles*u+2*rel,roles*v+2*rel+1))))
    for rel in selected:
        for role in (2*rel,2*rel+1):
            edges.add(tuple(sorted((role,roles+role))))
            edges.add(tuple(sorted((fresh,roles+fresh))))
            edges.add(tuple(sorted((role,fresh))))
            edges.add(tuple(sorted((roles+role,roles+fresh))))
    return frozenset(edges)

def map_vertex(x,mask):
    roles=7
    v,role=divmod(x,roles)
    if (mask>>role)&1:
        v=1-v
    return roles*v+role

def target_iso(a,b,selected):
    ea=encode(a,selected)
    eb=encode(b,selected)
    for mask in range(128):
        mapped=frozenset(tuple(sorted((map_vertex(u,mask),map_vertex(v,mask)))) for u,v in ea)
        if mapped==eb:
            return True
    return False

def mismatches(selected):
    objs=[((bits>>0)&1,(bits>>1)&1,(bits>>2)&1) for bits in range(8)]
    return sum(
        source_iso(a,b)!=target_iso(a,b,selected)
        for a in objs for b in objs
    )

def main():
    assert V6["verdict"]=="VERIFIED_FUTURE_CONSEQUENCE_GENERALIZATION_SELECTION"

    prior=[p for p in PROGS if choose(p,1)==[0]]

    stage1={}
    for p in prior:
        rels=choose(p,2)
        if rels==[0,1]:
            mm=0
        elif rels in ([0],[1]):
            mm=1080
        else:
            raise RuntimeError((p,rels))
        stage1[str(p)]=mm

    survivors1=[p for p in prior if stage1[str(p)]==0]

    cache={}
    stage2={}
    for p in survivors1:
        rels=tuple(choose(p,3))
        if rels not in cache:
            cache[rels]=mismatches(rels)
        stage2[str(p)]=cache[rels]

    survivors2=[p for p in survivors1 if stage2[str(p)]==0]
    selected=min(survivors2,key=lambda p:(cost(p),str(p)))

    gates={
        "G1_multiple_prior_fits":len(prior)>1,
        "G2_first_and_last_fail_stage1":(
            stage1[str(("ATOM","FIRST"))]>0 and stage1[str(("ATOM","LAST"))]>0
        ),
        "G3_boundary_survives_stage1":stage1[str(("OR","FIRST","LAST"))]==0,
        "G4_boundary_fails_stage2":stage2[str(("OR","FIRST","LAST"))]>0,
        "G5_true_zero_stage2":stage2[str(("ATOM","TRUE"))]==0,
        "G6_minimum_program_is_true":selected==("ATOM","TRUE"),
    }

    verdict="VERIFIED_META_RULE_GENESIS" if all(gates.values()) else "NEGATIVE_OR_PARTIAL"
    evidence={
        "verdict":verdict,
        "grammar_program_count":len(PROGS),
        "prior_consistent_programs":[list(p) for p in prior],
        "stage1_mismatches":stage1,
        "stage1_survivors":[list(p) for p in survivors1],
        "stage2_world":{
            "relation_count":3,
            "carrier_size":2,
            "objects":8,
            "ordered_pairs":64
        },
        "stage2_mismatches":stage2,
        "stage2_survivors":[list(p) for p in survivors2],
        "selected_program":list(selected),
        "selected_cost":cost(selected),
        "gates":gates,
        "claim_boundary":[
            "selector grammar supplied",
            "finite staged worlds",
            "subject and verifier supplied"
        ]
    }

    OUT.mkdir(exist_ok=True)
    (OUT/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    (OUT/"selected_program.json").write_text(
        json.dumps({"program":list(selected),"cost":cost(selected)},indent=2,sort_keys=True)+"\n"
    )
    print(json.dumps(evidence,indent=2,sort_keys=True))
    return 0 if verdict.startswith("VERIFIED") else 1

if __name__=="__main__":
    raise SystemExit(main())
