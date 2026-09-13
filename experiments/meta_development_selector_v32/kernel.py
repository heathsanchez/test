from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Tuple
from basis import World, Const, Atom, Bin, signature, sufficient, mapping_for, predict_with, expr_cost, canonical_skeleton, instantiate_skeleton

@dataclass(frozen=True)
class CompiledMove:
    skeletons: Tuple[tuple, ...]
    provenance: Tuple[str, ...]

class Kernel:
    def __init__(self):
        self.compiled: Dict[str, CompiledMove] = {}

    @staticmethod
    def authority(w: World):
        if not w.complete: return {"status":"UNKNOWN_AUTHORITY"}
        if not w.validate(): return {"status":"INVALID_WORLD"}
        return None

    @staticmethod
    def _store(best, expr, sig):
        c=(expr.atoms(),expr.ops(),expr.depth(),expr.lag_sum(),repr(expr.data()))
        old=best.get(sig)
        if old is None or c < old[0]: best[sig]=(c,expr)

    def closure(self, w: World, *, max_atoms=3, max_depth=2):
        auth=self.authority(w)
        if auth: return auth
        records=w.records; best={}; tested=0
        for k in (0,1):
            e=Const(k); self._store(best,e,signature(e,records)); tested+=1
        for off in range(w.max_offset+1):
            for ch in range(w.channel_count):
                e=Atom(off,ch); self._store(best,e,signature(e,records)); tested+=1
        changed=True
        while changed:
            before=len(best)
            reps=[x[1] for x in best.values()]
            for l in reps:
                for r in reps:
                    if l.atoms()+r.atoms()>max_atoms: continue
                    if 1+max(l.depth(),r.depth())>max_depth: continue
                    for op in range(16):
                        e=Bin(op,l,r); tested+=1
                        self._store(best,e,signature(e,records))
            changed=len(best)>before
        rows=[]
        for sig,(_,e) in best.items():
            if sufficient(sig,w.targets):
                rows.append((expr_cost(e,sig),repr(e.data()),e,sig,mapping_for(sig,w.targets)))
        if not rows:
            return {"status":"CERTIFIED_INADEQUATE_IN_DECLARED_LANGUAGE","tested_candidate_count":tested,"unique_semantic_count":len(best),"frontier":[]}
        rows.sort(key=lambda x:(x[0],x[1]))
        cost=rows[0][0]; front=[x for x in rows if x[0]==cost]
        return {"status":"VERIFIED","tested_candidate_count":tested,"unique_semantic_count":len(best),
                "minimum_cost":list(cost),
                "frontier":[{"expr":x[2].data(),"skeleton":canonical_skeleton(x[2]),"mapping":list(x[4])} for x in front],
                "_frontier":tuple((x[2],x[3],x[4]) for x in front)}

    def solve(self,w:World,*,allow_acquisition=True,compiled_key=None):
        auth=self.authority(w)
        if auth:return auth
        if compiled_key and compiled_key in self.compiled:
            cm=self.compiled[compiled_key]; tested=0; rows=[]; seen=set()
            for sk in cm.skeletons:
                for e in instantiate_skeleton(sk,w.channel_count,w.max_offset):
                    key=repr(e.data())
                    if key in seen: continue
                    seen.add(key); tested+=1
                    sig=signature(e,w.records)
                    if sufficient(sig,w.targets):
                        rows.append((expr_cost(e,sig),repr(e.data()),e,sig,mapping_for(sig,w.targets)))
            if rows:
                rows.sort(key=lambda x:(x[0],x[1])); c=rows[0][0]; front=[x for x in rows if x[0]==c]
                return {"status":"VERIFIED","route":"REUSE_COMPILED_DEVELOPMENT","acquisition_search_count":0,
                        "tested_candidate_count":tested,"minimum_cost":list(c),"compiled_provenance":list(cm.provenance),
                        "frontier":[{"expr":x[2].data(),"skeleton":canonical_skeleton(x[2]),"mapping":list(x[4])} for x in front],
                        "_frontier":tuple((x[2],x[3],x[4]) for x in front)}
            if not allow_acquisition:
                return {"status":"UNKNOWN_DEVELOPMENT","route":"COMPILED_REPLAY_FAILED","acquisition_search_count":0,"tested_candidate_count":tested}
        if not allow_acquisition:
            return {"status":"UNKNOWN_DEVELOPMENT","route":"NO_COMPILED_DEVELOPMENT","acquisition_search_count":0,"tested_candidate_count":0}
        out=self.closure(w)
        if out.get("status")=="VERIFIED":
            out["route"]="DEVELOP"; out["acquisition_search_count"]=1
        return out

    def compile_from(self,key:str, named_results):
        sets=[]; prov=[]
        for name,res in named_results:
            if res.get("status")!="VERIFIED": return {"status":"REJECTED_TRAINING_RESULT"}
            sk={tupleize(row["skeleton"]) for row in res.get("frontier",[])}
            if not sk:return {"status":"REJECTED_EMPTY_FRONTIER"}
            sets.append(sk); prov.append(name)
        common=set.intersection(*sets) if sets else set()
        if not common:return {"status":"NO_RECURRING_DEVELOPMENT"}
        cm=CompiledMove(tuple(sorted(common,key=repr)),tuple(prov)); self.compiled[key]=cm
        return {"status":"VERIFIED","compiled_key":key,"skeleton_count":len(cm.skeletons),"skeletons":list(cm.skeletons),"provenance":prov}

    def select_intervention(self, world: World, solve_result, pool_records):
        if solve_result.get("status")!="VERIFIED": return {"status":"UNKNOWN_FRONTIER"}
        front=solve_result.get("_frontier",())
        if len(front)<2:return {"status":"NO_DISAMBIGUATION_NEEDED"}
        rows=[]
        for i,r in enumerate(pool_records):
            preds=[predict_with(e,m,r) for e,_sig,m in front]
            rows.append((len(set(preds)),tuple(preds),i))
        rows.sort(key=lambda x:(-x[0],x[2])); best=rows[0]
        return {"status":"VERIFIED","selected_index":best[2],"prediction_groups":best[0],"predictions":list(best[1]),
                "all_rows":[{"index":i,"groups":g,"predictions":list(p)} for g,p,i in rows]}

    def contraction(self,w:World,solve_result):
        if w.current_signature is None:return {"status":"NO_CURRENT_SIGNATURE"}
        if not sufficient(tuple(w.current_signature),w.targets):return {"status":"CURRENT_NOT_SUFFICIENT"}
        if solve_result.get("status")!="VERIFIED":return {"status":"UNKNOWN"}
        current_blocks=len(set(w.current_signature)); selected_blocks=solve_result["minimum_cost"][0]
        return {"status":"VERIFIED","current_blocks":current_blocks,"selected_blocks":selected_blocks,
                "contracted":selected_blocks<current_blocks}

def tupleize(x):
    if isinstance(x,list): return tuple(tupleize(v) for v in x)
    if isinstance(x,tuple): return tuple(tupleize(v) for v in x)
    return x
