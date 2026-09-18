#!/usr/bin/env python3
"""Test universal reverse-episode calculus on explicit long C9 RIGID families.

Cases:
  R=397: n=2^R-1, q0 exit enters one C9 block and remains Complete-O RIGID.
  R=19853: analogous construction entering two C9 blocks.

For each source, enumerate its q=0 RIGID episode starts over a small post-q0
window and run the optimized universal reverse-episode lower-merge search at
each endpoint.
"""
from __future__ import annotations
import argparse
import collatz_q0_rigid_recharge_audit as ra
import collatz_universal_reverse_episode_bfs_v2 as bfs

def run(R:int,extra:int,L:int,B:int):
    n=(1<<R)-1
    K=R+extra
    starts,branches=ra.rigid_episode_segment(n,K)
    print("R",R,"BITLEN",n.bit_length(),"K",K,
          "EPISODES",len(branches),"STARTS",len(starts))
    pow3=[1]*(B+1)
    for i in range(1,B+1):pow3[i]=pow3[i-1]*3
    total_legal=0;best=None
    for k,r,m,x in starts:
        row,legal,states=bfs.search_endpoint(n,r,m,L,B,B,pow3)
        total_legal+=legal
        if row is not None:
            full=(row[0],k,r,m)+row[2:]
            if best is None or full<best:best=full
            print("ENDPOINT_SEARCH",k,r,m,"gap",row[0],
                  "legal",legal,"states",states,
                  "word",row[5] if len(row)>5 else None)
            if row[0]<0:
                print("LOWER_MERGE_CERT",full)
                print("STATUS CONSTRUCTED_C9_CLOSED_BY_REVERSE_EPISODES")
                return
    print("TOTAL_LEGAL",total_legal)
    print("BEST",best)
    print("STATUS CONSTRUCTED_C9_SURVIVES_REVERSE_EPISODES")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--R",type=int,required=True)
    ap.add_argument("--extra",type=int,default=30)
    ap.add_argument("--L",type=int,default=5)
    ap.add_argument("--B",type=int,default=14)
    a=ap.parse_args();run(a.R,a.extra,a.L,a.B)
