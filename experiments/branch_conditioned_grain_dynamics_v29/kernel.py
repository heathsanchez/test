#!/usr/bin/env python3
from __future__ import annotations
from typing import Any,Dict,Optional
from basis import BranchWorld,all_partitions,sufficient,partition_from_signatures,refines,incomparable,block_sizes

class Kernel:
    @staticmethod
    def _auth(w):
        if not w.complete:return {"status":"UNKNOWN_AUTHORITY"}
        return None

    def _coarsest(self,w,sigs,consequence_enabled=True):
        a=self._auth(w)
        if a:return a
        if not consequence_enabled:return {"status":"UNKNOWN_NO_CONSEQUENCE_AUTHORITY"}
        parts=tuple(all_partitions(w.state_count))
        good=[p for p in parts if sufficient(p,sigs)]
        m=min(len(p) for p in good)
        mins=tuple(sorted(p for p in good if len(p)==m))
        return {"status":"VERIFIED","tested_partition_count":len(parts),"minimum_block_count":m,
                "minimum_partitions":[[list(b) for b in p] for p in mins],"_minimum":mins}

    def prebranch(self,w,consequence_enabled=True):
        joint=tuple(tuple(v for h in range(len(w.histories)) for v in w.future_signatures[h][x])
                    for x in range(w.state_count))
        return self._coarsest(w,joint,consequence_enabled)

    def postbranch(self,w,history,consequence_enabled=True):
        a=self._auth(w)
        if a:return a
        if history not in w.histories:return {"status":"UNKNOWN_BRANCH_RECORD"}
        i=w.histories.index(history)
        row=self._coarsest(w,w.future_signatures[i],consequence_enabled)
        if row.get("status")=="VERIFIED": row["history_index"]=i
        return row

    def analyze(self,w,consequence_enabled=True):
        a=self._auth(w)
        if a:return a
        pre=self.prebranch(w,consequence_enabled)
        if pre.get("status")!="VERIFIED":return pre
        posts=[self.postbranch(w,h,consequence_enabled) for h in w.histories]
        if any(r.get("status")!="VERIFIED" for r in posts):return {"status":"UNKNOWN_BRANCH_ANALYSIS"}
        pre_p=pre["_minimum"][0]
        post_p=[r["_minimum"][0] for r in posts]
        grains={}
        for i,p in enumerate(post_p):grains.setdefault(p,[]).append(i)
        pair=[]
        for i in range(len(post_p)):
            for j in range(i+1,len(post_p)):
                pair.append({"branches":[i,j],"incomparable":incomparable(post_p[i],post_p[j])})
        return {"status":"VERIFIED",
                "pre":{"tested_partition_count":pre["tested_partition_count"],"minimum_block_count":pre["minimum_block_count"],
                       "minimum_partitions":pre["minimum_partitions"]},
                "posts":[{"tested_partition_count":r["tested_partition_count"],"minimum_block_count":r["minimum_block_count"],
                          "minimum_partitions":r["minimum_partitions"],"history_index":r["history_index"]} for r in posts],
                "grain_count":len(grains),"pairwise":pair,
                "pre_block_sizes":list(block_sizes(pre_p)),
                "post_block_sizes":[list(block_sizes(p)) for p in post_p],
                "_pre":pre_p,"_posts":post_p}

    def observe(self,w,history,consequence_enabled=True):
        pre=self.prebranch(w,consequence_enabled)
        if pre.get("status")!="VERIFIED":return pre
        post=self.postbranch(w,history,consequence_enabled)
        if post.get("status")!="VERIFIED":
            return {"status":post.get("status"),"active_partition":pre.get("minimum_partitions",[None])[0],
                    "active_block_count":pre.get("minimum_block_count")}
        pre_p=pre["_minimum"][0]; post_p=post["_minimum"][0]
        return {"status":"VERIFIED","history_known":True,
                "pre_block_count":len(pre_p),"post_block_count":len(post_p),
                "contracted":refines(pre_p,post_p) and pre_p!=post_p,
                "active_partition":[list(b) for b in post_p],
                "_post":post_p}

    def perturb_one(self,old,new,branch_index):
        a=self.analyze(old); b=self.analyze(new)
        if a.get("status")!="VERIFIED" or b.get("status")!="VERIFIED":return {"status":"UNKNOWN_UPDATE"}
        changed=a["_posts"][branch_index]!=b["_posts"][branch_index]
        others=all(a["_posts"][i]==b["_posts"][i] for i in range(len(a["_posts"])) if i!=branch_index)
        return {"status":"VERIFIED","changed":changed,"unrelated_preserved":others}
