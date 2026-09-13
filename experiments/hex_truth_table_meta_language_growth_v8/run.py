#!/usr/bin/env python3
import itertools, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"results"
V7_AUTH=ROOT.parent/"hex_meta_selector_genesis_v7"/"AUTHORITY.json"

def source_objects(n,m,mode):
    arcs=[(i,j) for i in range(n) for j in range(n) if i!=j]
    if mode=="all_single_relation_graphs":
        assert m==1
        out=[]
        for bits in range(1<<len(arcs)):
            E=frozenset(a for k,a in enumerate(arcs) if (bits>>k)&1)
            out.append((E,))
        return out
    if mode=="one_arc_each":
        return [tuple(frozenset([a]) for a in xs)
                for xs in itertools.product(arcs,repeat=m)]
    raise ValueError(mode)

def source_canon(obj,n):
    vals=[]
    for p in itertools.permutations(range(n)):
        vals.append(tuple(
            tuple(sorted((p[u],p[v]) for u,v in E))
            for E in obj
        ))
    return min(vals)

def encode(obj,n,selected_relations):
    m=len(obj)
    roles=2*m+1
    fresh=2*m
    idx=lambda v,r:roles*v+r
    edges=set()
    for rel,E in enumerate(obj):
        tail,head=2*rel,2*rel+1
        for u,v in E:
            edges.add(tuple(sorted((idx(u,tail),idx(v,head)))))
    for rel in selected_relations:
        for role in (2*rel,2*rel+1):
            for v in range(n):
                edges.add(tuple(sorted((idx(v,role),idx(v,fresh)))))
    return frozenset(edges)

def role_maps(n,roles):
    ps=list(itertools.permutations(range(n)))
    out=[]
    for role_perms in itertools.product(ps,repeat=roles):
        mp=[0]*(n*roles)
        for v in range(n):
            for r in range(roles):
                mp[roles*v+r]=roles*role_perms[r][v]+r
        out.append(tuple(mp))
    return out

def target_canon(edges,maps):
    best=None
    for mp in maps:
        z=tuple(sorted(
            tuple(sorted((mp[u],mp[v])))
            for u,v in edges
        ))
        if best is None or z<best:
            best=z
    return best

def world(n,m,mode):
    objs=source_objects(n,m,mode)
    src=[source_canon(x,n) for x in objs]
    maps=role_maps(n,2*m+1)
    cache={}
    def evaluate(selected):
        selected=tuple(selected)
        if selected in cache:
            return cache[selected]
        ts=[target_canon(encode(x,n,selected),maps) for x in objs]
        mm=0
        first=None
        for i in range(len(objs)):
            for j in range(len(objs)):
                s=src[i]==src[j]
                t=ts[i]==ts[j]
                if s!=t:
                    mm+=1
                    if first is None:
                        first={
                            "a":[[list(e) for e in sorted(R)] for R in objs[i]],
                            "b":[[list(e) for e in sorted(R)] for R in objs[j]],
                            "source_iso":s,
                            "target_iso":t
                        }
        cache[selected]=(mm,first)
        return cache[selected]
    return objs,evaluate

def tt_tuple(mask):
    return tuple((mask>>i)&1 for i in range(4))

def tt_select(tt,m):
    selected=[]
    for i in range(m):
        first=int(i==0)
        last=int(i==m-1)
        bit_index=2*first+last
        if tt[bit_index]:
            selected.append(i)
    return selected

def main():
    v7=json.loads(V7_AUTH.read_text())
    if v7["verdict"]!="VERIFIED_META_RULE_GENESIS_AND_TRANSFER":
        raise RuntimeError("V7 authority missing")

    prior_objs,prior_eval=world(3,1,"all_single_relation_graphs")
    stage1_objs,stage1_eval=world(3,2,"one_arc_each")
    stage2_objs,stage2_eval=world(2,3,"one_arc_each")

    old={
        "FIRST":{
            "prior_selected":[0],
            "prior_mismatches":prior_eval([0])[0],
            "stage1_selected":[0],
            "stage1_mismatches":stage1_eval([0])[0]
        },
        "LAST":{
            "prior_selected":[0],
            "prior_mismatches":prior_eval([0])[0],
            "stage1_selected":[1],
            "stage1_mismatches":stage1_eval([1])[0]
        }
    }

    candidates=[]
    for mask in range(16):
        tt=tt_tuple(mask)
        psel=tt_select(tt,1)
        s1sel=tt_select(tt,2)
        pmm,pfirst=prior_eval(psel)
        s1mm,s1first=stage1_eval(s1sel)
        candidates.append({
            "operator_id":mask,
            "truth_table":list(tt),
            "prior_selected_relations":psel,
            "prior_mismatches":pmm,
            "stage1_selected_relations":s1sel,
            "stage1_mismatches":s1mm,
            "survives_prior_and_stage1":pmm==0 and s1mm==0,
            "prior_first_mismatch":pfirst,
            "stage1_first_mismatch":s1first
        })

    survivors1=[c for c in candidates if c["survives_prior_and_stage1"]]

    stage2=[]
    for c in survivors1:
        tt=tuple(c["truth_table"])
        sel=tt_select(tt,3)
        mm,first=stage2_eval(sel)
        stage2.append({
            "operator_id":c["operator_id"],
            "truth_table":c["truth_table"],
            "selected_relations":sel,
            "mismatch_count":mm,
            "qualified":mm==0,
            "first_mismatch":first
        })

    survivors2=[x for x in stage2 if x["qualified"]]
    selected=survivors2[0] if len(survivors2)==1 else None

    mutations=[]
    if selected:
        base=tuple(selected["truth_table"])
        for bit in range(4):
            mut=list(base)
            mut[bit]=1-mut[bit]
            mut=tuple(mut)
            if bit==3:
                sel=tt_select(mut,1)
                mm,first=prior_eval(sel)
                stage="prior_one_relation"
            elif bit in (1,2):
                sel=tt_select(mut,2)
                mm,first=stage1_eval(sel)
                stage="two_relation_consequence"
            else:
                sel=tt_select(mut,3)
                mm,first=stage2_eval(sel)
                stage="three_relation_continuation"
            mutations.append({
                "flipped_bit_index":bit,
                "mutated_truth_table":list(mut),
                "witness_stage":stage,
                "selected_relations":sel,
                "mismatch_count":mm,
                "fails":mm>0,
                "first_mismatch":first
            })

    selected_tt=selected["truth_table"] if selected else None
    matches_v7=(selected_tt==[1,1,1,1] and v7["selected_program"]==["ATOM","TRUE"])

    gates={
        "G1_prior_world_complete":len(prior_objs)==64,
        "G2_initial_language_prior_pass":all(x["prior_mismatches"]==0 for x in old.values()),
        "G3_initial_language_stage1_inadequate":all(x["stage1_mismatches"]>0 for x in old.values()),
        "G4_complete_operator_substrate":len(candidates)==16,
        "G5_exactly_two_survive_prior_and_stage1":len(survivors1)==2,
        "G6_unique_stage2_survivor":len(survivors2)==1,
        "G7_selected_table_all_ones":selected_tt==[1,1,1,1],
        "G8_single_bit_mutations_fail":len(mutations)==4 and all(x["fails"] for x in mutations),
        "G9_matches_v7_selected_behavior":matches_v7,
        "G10_world_sizes":len(stage1_objs)==36 and len(stage2_objs)==8
    }

    verdict="QUALIFIED_META_LANGUAGE_PRIMITIVE_FOR_HEX_HELDOUT" if all(gates.values()) else "NEGATIVE_OR_PARTIAL"
    evidence={
        "verdict":verdict,
        "classification":"FINITE_EXHAUSTIVE_META_LANGUAGE_PRIMITIVE_CONSTRUCTION",
        "old_language":old,
        "operator_substrate_size":16,
        "candidate_operators":candidates,
        "stage1_survivors":survivors1,
        "stage2_results":stage2,
        "selected_operator":selected,
        "single_bit_mutations":mutations,
        "matches_v7":matches_v7,
        "gates":gates,
        "claim_boundary":[
            "complete binary Boolean operator substrate supplied",
            "finite qualification and continuation worlds",
            "subject and verifier supplied"
        ]
    }

    OUT.mkdir(exist_ok=True)
    (OUT/"evidence.json").write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    if selected:
        (OUT/"selected_operator.json").write_text(
            json.dumps(selected,indent=2,sort_keys=True)+"\n"
        )
    print(json.dumps(evidence,indent=2,sort_keys=True))
    return 0 if verdict.startswith("QUALIFIED") else 1

if __name__=="__main__":
    raise SystemExit(main())
