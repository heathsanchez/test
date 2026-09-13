#!/usr/bin/env python3
"""Frozen V19 stochastic temporal readout learner."""
from __future__ import annotations
from dataclasses import dataclass, field
import itertools, math
from typing import Any, Dict, List, Optional, Sequence, Tuple
from basis import Accessor, TemporalWorld, generated_accessors, partition, readout_digest

@dataclass(frozen=True)
class ReadoutCode:
    code_id:str
    interface_key:Tuple[Any,...]
    accessors:Tuple[Accessor,...]
    provenance:Tuple[str,...]
    def data(self): return {"code_id":self.code_id,"accessors":[list(a) for a in self.accessors],"provenance":list(self.provenance)}

@dataclass
class Usage:
    accessors:Tuple[Accessor,...]
    origins:List[str]=field(default_factory=list)

class Kernel:
    def __init__(self):
        self.compiled={}
        self.usage={}

    @staticmethod
    def _auth(world):
        if not world.complete: return {"status":"UNKNOWN_AUTHORITY","reason":"count_authority_incomplete"}
        return None

    @staticmethod
    def _kt(n0,n1):
        n0=int(n0); n1=int(n1); n=n0+n1
        le=(math.lgamma(1.0)-math.lgamma(n+1.0)+math.lgamma(n0+.5)-math.lgamma(.5)+math.lgamma(n1+.5)-math.lgamma(.5))
        return -le/math.log(2.0)

    def score(self,world,accessors,statistical_enabled=True):
        a=self._auth(world)
        if a:return a
        if not statistical_enabled:return {"status":"UNKNOWN_NO_STATISTICAL_AUTHORITY"}
        aa=tuple(sorted(set((int(x[0]),int(x[1])) for x in accessors)))
        cells=partition(world,aa)
        data=0.0
        for cls in cells:
            for t in range(len(world.future_tests)):
                n0=sum(world.counts[i][t][0] for i in cls); n1=sum(world.counts[i][t][1] for i in cls)
                data += self._kt(n0,n1)
        struct=sum(world.accessor_cost(x) for x in aa)
        return {"status":"VERIFIED","accessors":[list(x) for x in aa],"data_bits":data,"structural_bits":float(struct),"total_bits":data+struct,"cell_count":len(cells)}

    def search_at_depth(self,world,depth,statistical_enabled=True,historical_enabled=True):
        a=self._auth(world)
        if a:return a
        if not statistical_enabled:return {"status":"UNKNOWN_NO_STATISTICAL_AUTHORITY"}
        eff_depth=int(depth) if historical_enabled else 0
        acc=generated_accessors(world,eff_depth)
        rows=[]
        for k in range(len(acc)+1):
            for s in itertools.combinations(acc,k):
                rows.append(self.score(world,s,True))
        best=min(r["total_bits"] for r in rows); eps=1e-9
        mins=[r for r in rows if abs(r["total_bits"]-best)<=eps]
        mins.sort(key=lambda r:(len(r["accessors"]),r["accessors"]))
        return {"status":"VERIFIED","authorized_lag":eff_depth,"tested_subset_count":len(rows),"best_total_bits":best,"minimum_codes":[{"accessors":r["accessors"],"total_bits":r["total_bits"],"data_bits":r["data_bits"],"structural_bits":r["structural_bits"]} for r in mins]}

    def develop(self,world,statistical_enabled=True,historical_enabled=True):
        a=self._auth(world)
        if a:return a
        if not statistical_enabled:return {"status":"UNKNOWN_NO_STATISTICAL_AUTHORITY","selected_lag":0,"generations":[]}
        base=self.search_at_depth(world,0,True,historical_enabled)
        gens=[base]
        selected=base
        selected_lag=0
        if historical_enabled:
            for d in range(1,world.max_lag+1):
                nxt=self.search_at_depth(world,d,True,True)
                gens.append(nxt)
                if nxt["best_total_bits"] + 1e-9 < selected["best_total_bits"]:
                    selected=nxt; selected_lag=d
                else:
                    break
        return {"status":"VERIFIED","initial_class_count":1,"selected_lag":selected_lag,"minimum_search":selected,"generations":gens}

    def _record(self,request_id,world,code):
        aa=tuple(sorted(set((int(x[0]),int(x[1])) for x in code))); key=(world.interface_key(),aa)
        u=self.usage.get(key)
        if u is None:u=Usage(aa); self.usage[key]=u
        if request_id not in u.origins:u.origins.append(request_id)
        if len(u.origins)<2:return None
        c=ReadoutCode("tr_"+readout_digest(world,aa)[:16],world.interface_key(),aa,tuple(u.origins))
        self.compiled[world.interface_key()]=c
        return c

    def ablate(self,world): return self.compiled.pop(world.interface_key(),None) is not None

    def replay(self,request_id,world,code):
        a=self._auth(world)
        if a:return {"request_id":request_id,**a,"route":"STOP"}
        if code.interface_key!=world.interface_key():return {"request_id":request_id,"status":"TYPE_MISMATCH","route":"STOP"}
        full=self.score(world,code.accessors); empty=self.score(world,())
        dels=[]
        for a0 in code.accessors:
            sub=tuple(x for x in code.accessors if x!=a0); s=self.score(world,sub); dels.append(s["total_bits"])
        ok=full["total_bits"]+1e-9<empty["total_bits"] and all(full["total_bits"]+1e-9<x for x in dels)
        return {"request_id":request_id,"status":"VERIFIED" if ok else "REPLAY_FAILED","route":"REPLAY_TEMPORAL_READOUT","accessors":[list(a) for a in code.accessors],"acquisition_search_count":0,"total_bits":full["total_bits"],"code":code.data()}

    def solve(self,request_id,world,allow_acquisition_search=True,statistical_enabled=True,historical_enabled=True):
        a=self._auth(world)
        if a:return {"request_id":request_id,**a,"route":"STOP"}
        retained=self.compiled.get(world.interface_key()); failed=None
        if retained is not None:
            rp=self.replay(request_id,world,retained)
            if rp["status"]=="VERIFIED":
                self._record(request_id,world,retained.accessors); return {**rp,"route":"REUSE_COMPILED_READOUT","failed_reuse":None}
            failed=rp
        if not allow_acquisition_search:return {"request_id":request_id,"status":"UNKNOWN_READOUT","route":"STOP","acquisition_search_count":0,"failed_reuse":failed}
        dev=self.develop(world,statistical_enabled,historical_enabled)
        if dev["status"]!="VERIFIED":return {"request_id":request_id,"status":dev["status"],"route":"DEVELOP","developmental":dev,"acquisition_search_count":1,"failed_reuse":failed}
        mins=dev["minimum_search"]["minimum_codes"]
        if len(mins)!=1:return {"request_id":request_id,"status":"VERIFIED_FRONTIER","route":"DEVELOP","selected_frontier":[r["accessors"] for r in mins],"selected_lag":dev["selected_lag"],"developmental":dev,"acquisition_search_count":1,"failed_reuse":failed}
        code=tuple((int(a[0]),int(a[1])) for a in mins[0]["accessors"])
        promoted=self._record(request_id,world,code)
        return {"request_id":request_id,"status":"VERIFIED","route":"DEVELOP","accessors":[list(a) for a in code],"selected_lag":dev["selected_lag"],"developmental":dev,"promoted_code":promoted.data() if promoted else None,"acquisition_search_count":1,"failed_reuse":failed}
