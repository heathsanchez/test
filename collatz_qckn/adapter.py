"""Collatz-domain adapter over the existing exact episode engines."""
from __future__ import annotations

from typing import Iterable, Mapping, Sequence, Tuple

from experiments import collatz_q0_coalescence_component_audit as base
from experiments import collatz_q0_rigid_recharge_audit as ra

from .types import Capability, CapabilityKind, CostRecord, digest_payload


def fragment_certificate(word: Sequence[Sequence[int]]) -> dict:
    word=tuple(tuple(int(v) for v in z) for z in word)
    if not word or not all(len(z)==3 and min(z)>=1 for z in word):
        raise ValueError("invalid episode word")
    if not all(a[2]==b[0] for a,b in zip(word,word[1:])):
        raise ValueError("anchor mismatch")
    A,B,D=1,0,0
    for r,s,rp in word:
        A,B,D=3**r*A,3**r*B+((1<<s)-1)*(1<<D),D+s+rp
    return {"word":word,"r0":word[0][0],"r1":word[-1][2],
            "A":A,"B":B,"D":D,"steps":sum(r+s for r,s,rp in word)}


def replay_fragment(cert: Mapping, start_m: int) -> dict:
    x=(1<<int(cert["r0"]))*start_m-1
    start_x=x
    path_min=x
    argmin=0
    steps=0
    for expected in cert["word"]:
        r,m,s,rp,mp,y=ra.episode(x)
        if (r,s,rp)!=tuple(expected):
            raise ValueError("episode guard mismatch")
        for _ in range(r+s):
            x=base.T(x)
            steps+=1
            if x<path_min:
                path_min=x
                argmin=steps
        if x!=y:
            raise ValueError("episode replay mismatch")
    end_m=(x+1)>>int(cert["r1"])
    return {"start_x":start_x,"end_x":x,"end_m":end_m,
            "path_min":path_min,"argmin":argmin,"steps":steps}


class CollatzAdapter:
    def __init__(self,contract_digest:str):
        self.contract_digest=contract_digest

    def propose_forward_macro(self,source:int,start_m:int,word,provenance:str):
        cert=fragment_certificate(word)
        replay=replay_fragment(cert,start_m)
        if replay["path_min"]>=source:
            raise ValueError("training witness does not descend below source")
        guard={"word":[list(z) for z in cert["word"]],
               "start_anchor":cert["r0"],"end_anchor":cert["r1"]}
        payload={
            "word":[list(z) for z in cert["word"]],
            "witness_source":source,
            "witness_start_m":start_m,
            "witness_end_m":replay["end_m"],
            "witness_path_min":replay["path_min"],
            "witness_argmin":replay["argmin"],
        }
        cap=Capability(
            kind=CapabilityKind.FORWARD_DESCENT_MACRO,
            start_anchor=cert["r0"],end_anchor=cert["r1"],
            affine_a=cert["A"],affine_b=cert["B"],affine_d=cert["D"],
            guard_digest=digest_payload(guard),
            contract_digest=self.contract_digest,
            payload=payload,
            dependencies=(),
            provenance=provenance,
            cost=CostRecord(constructions=1),
        )
        witness={"source":source,"start_m":start_m,**replay}
        return cap,witness

    def apply_capability(self,cap:Capability,source:int,start_m:int):
        if cap.contract_digest!=self.contract_digest:
            return {"applicable":False,"reason":"contract mismatch"}
        try:
            cert=fragment_certificate(cap.payload["word"])
        except (KeyError,TypeError,ValueError):
            return {"applicable":False,"reason":"invalid payload"}
        if (cert["r0"],cert["r1"],cert["A"],cert["B"],cert["D"]) != (
            cap.start_anchor,cap.end_anchor,cap.affine_a,cap.affine_b,cap.affine_d
        ):
            return {"applicable":False,"reason":"payload/affine mismatch"}
        guard={"word":[list(z) for z in cert["word"]],
               "start_anchor":cert["r0"],"end_anchor":cert["r1"]}
        if digest_payload(guard)!=cap.guard_digest:
            return {"applicable":False,"reason":"guard mismatch"}
        try:
            replay=replay_fragment(cert,start_m)
        except (AssertionError,ValueError):
            return {"applicable":False,"reason":"episode guard mismatch"}
        return {"applicable":True,**replay,
                "lower_merge":replay["path_min"]<source}
