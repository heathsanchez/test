from __future__ import annotations
from itertools import product

from kernel import Kernel
from challenge_pack import WORLDS

def norm_partition(row):
    return tuple(tuple(int(x) for x in block) for block in row)

def witnesses(result):
    out=[]
    for cls in result.get("class_witnesses",[]):
        out.append({
            "action_class":tuple(int(x) for x in cls["action_class"]),
            "minimum_block_count":int(cls["minimum_block_count"]),
            "frontier":tuple(norm_partition(p) for p in cls["frontier"]),
        })
    return tuple(out)

def common_refinement(parts,state_count=8):
    groups={}
    for state in range(state_count):
        key=[]
        for p in parts:
            idx=next(i for i,b in enumerate(p) if state in b)
            key.append(idx)
        groups.setdefault(tuple(key),[]).append(state)
    return tuple(sorted(tuple(v) for v in groups.values()))

def classify(parts,state_count=8):
    meet=common_refinement(parts,state_count)
    block_product=1
    for p in parts:
        block_product*=len(p)
    discrete=all(len(cell)==1 for cell in meet) and len(meet)==state_count
    if discrete and block_product==state_count:
        return "COMPLEMENTARY"
    if discrete and block_product>state_count:
        return "CONSTRAINED"
    return "UNDERRESOLVED"

def main():
    k=Kernel()
    for kind in ("one_class","two_class","three_class","two_by_four"):
        r=k.synthesize(WORLDS[(kind,0)])
        print("\n==",kind,"==")
        print("status",r.get("status"))
        print("classes",r.get("action_classes"))
        print("quotient_class_count",r.get("quotient_class_count"))
        ws=witnesses(r)
        for i,w in enumerate(ws):
            print("class",i,"actions",w["action_class"],"blocks",w["minimum_block_count"],"frontier",len(w["frontier"]))
        if ws:
            combos=list(product(*(w["frontier"] for w in ws)))
            counts={}
            for combo in combos:
                c=classify(combo)
                counts[c]=counts.get(c,0)+1
            print("combination_count",len(combos))
            print("classification_counts",counts)

if __name__=="__main__":
    main()
