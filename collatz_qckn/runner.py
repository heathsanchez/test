"""Bounded QCKN generation and matched-control harness for Collatz."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import argparse
import json
import sys
from typing import Iterable, Sequence

from .adapter import CollatzAdapter
from .authority import Authority
from .compiled_present import CompiledPresent
from .ledger import CausalLedger
from .types import Capability, CostRecord, canonical_json, digest_payload

_EXPERIMENTS=str(Path(__file__).resolve().parent.parent / "experiments")
if _EXPERIMENTS not in sys.path:
    sys.path.insert(0,_EXPERIMENTS)
import collatz_forward_descent_macro_transfer as fm


@dataclass(frozen=True)
class ArmResult:
    name:str
    obligations:int
    active_capabilities:int
    capability_attempts:int
    authoritative_hits:int
    residuals:int
    discovery_calls:int
    search_expansions:int=0
    verifications:int=0

    def to_canonical(self):
        return asdict(self)


def run_arm(name:str,adapter:CollatzAdapter,obligations:Sequence[dict],
            present:CompiledPresent|None=None,raw_history:Sequence[Capability]=(),
            required_authority_digest:str|None=None):
    authority_ok=(required_authority_digest is None or
                  (present is not None and required_authority_digest in present.authority_digests))
    caps=present.capabilities if present is not None and authority_ok else ()
    attempts=0; hits=0
    for ob in obligations:
        source=int(ob["source"]); start_m=int(ob["start_m"])
        closed=False
        for cap in caps:
            attempts+=1
            if "prefix_steps" in ob:
                y=source
                for _ in range(int(ob["prefix_steps"])):
                    y=fm.base.T(y)
                expected=(1<<cap.start_anchor)*start_m-1
                if y!=expected:
                    continue
            z=adapter.apply_capability(cap,source,start_m)
            if z.get("applicable") and z.get("lower_merge"):
                hits+=1;closed=True;break
    return ArmResult(name,len(obligations),len(caps),attempts,hits,
                     len(obligations)-hits,0)


def sham_present(present:CompiledPresent)->CompiledPresent:
    sham=[]
    for cap in present.capabilities:
        d=cap.as_dict()
        d["contract_digest"]="SHAM:"+cap.contract_digest
        sham.append(Capability(**d))
    return CompiledPresent(tuple(sham),"SHAM:"+present.contract_digest,
                           present.authority_digests)


def discover_forward_macros(adapter:CollatzAdapter,training_sources:Iterable[int],
                            maxlen:int=12,with_metrics:bool=False):
    """Discover source-independent q0 forward descent macros from frozen sources."""
    out={}
    metrics={"sources_scanned":0,"eligible_sources":0,"construction_attempts":0,
             "valid_constructions":0,"deduplicated_capabilities":0}
    for n in training_sources:
        n=int(n); metrics["sources_scanned"]+=1
        if not fm.candidate(n):
            continue
        starts,words=fm.q0_odd_starts_and_words(n)
        if not words:
            continue
        metrics["eligible_sources"]+=1
        end=len(words)
        for a in range(max(0,end-maxlen),end):
            metrics["construction_attempts"]+=1
            word=tuple(words[a:end])
            start_m=starts[a][2]
            try:
                cap,w=adapter.propose_forward_macro(n,start_m,word,f"source:{n}")
            except (AssertionError,ValueError):
                continue
            metrics["valid_constructions"]+=1
            out.setdefault(cap.semantic_id,(cap,w))
    proposals=tuple(out[k] for k in sorted(out))
    metrics["deduplicated_capabilities"]=len(proposals)
    return (proposals,metrics) if with_metrics else proposals


def promote_verified(proposals,authority:Authority):
    ledger=CausalLedger()
    verified=0
    for cap,witness in proposals:
        ev=authority.verify(cap,witness)
        if not ev.valid:
            continue
        ledger.promote(cap,ev); verified+=1
    return ledger,verified


def obligations_from_sources(sources:Iterable[int],K:int=96):
    """Return exact q0 RIGID episode-start obligations for a frozen source set."""
    obs=[]
    for n in sources:
        ss,bs=fm.ra.rigid_episode_segment(int(n),K)
        if not bs:
            continue
        for k,r,m,x in ss:
            obs.append({"source":int(n),"k":k,"anchor":r,"start_m":m})
    return tuple(obs)



def run_source_arm(name:str,adapter:CollatzAdapter,sources:Iterable[int],
                   present:CompiledPresent|None=None,K:int=96,
                   required_authority_digest:str|None=None):
    """Prospective source-level reuse on the exact q0 RIGID population."""
    authority_ok=(required_authority_digest is None or
                  (present is not None and required_authority_digest in present.authority_digests))
    caps=present.capabilities if present is not None and authority_ok else ()
    attempts=0;hits=0;eligible=0
    by_anchor={}
    for cap in caps:
        by_anchor.setdefault(cap.start_anchor,[]).append(cap)
    for n0 in sources:
        n=int(n0)
        if not fm.candidate(n):
            continue
        ss,bs=fm.ra.rigid_episode_segment(n,K)
        if not bs:
            continue
        eligible+=1;closed=False
        for k,r,m,x in ss:
            for cap in by_anchor.get(r,()):
                attempts+=1
                z=adapter.apply_capability(cap,n,m)
                if z.get("applicable") and z.get("lower_merge"):
                    hits+=1;closed=True;break
            if closed:break
    return ArmResult(name,eligible,len(caps),attempts,hits,eligible-hits,0)


def research_qualification(train_hi:int=8191,future_hi:int=16383,K:int=96,maxlen:int=12):
    """Reproduce the forward-macro transfer experiment through QCKN causal memory."""
    contract=digest_payload({
        "adapter":"COLLATZ_QCKN_V1",
        "training":[3,train_hi],
        "future":[train_hi+2,future_hi],
        "K":K,"maxlen":maxlen,
    })
    adapter=CollatzAdapter(contract)
    authority=Authority(contract,"collatz-exact-replay-v1")
    training=range(3,train_hi+1,2)
    future=range(train_hi+2,future_hi+1,2)
    proposals,discovery=discover_forward_macros(adapter,training,maxlen=maxlen,with_metrics=True)
    ledger,verified=promote_verified(proposals,authority)
    compiled=CompiledPresent.compile(ledger)
    present=CompiledPresent.from_text(compiled.to_text())

    cold=run_source_arm("COLD",adapter,future,K=K)
    warm=run_source_arm("WARM",adapter,future,present=present,K=K,required_authority_digest=authority.digest)
    raw=run_source_arm("RAW_HISTORY",adapter,future,K=K)
    sham=run_source_arm("SHAM",adapter,future,present=sham_present(present),K=K,required_authority_digest=authority.digest)

    revoke_ids=[]
    for cap in tuple(ledger.active_capabilities()):
        revoke_ids.append(ledger.revoke(cap.semantic_id,"forward macro family ablation").event_id)
    ablated=CompiledPresent.from_text(CompiledPresent.compile(ledger).to_text())
    ablation=run_source_arm("ANCESTOR_ABLATION",adapter,future,present=ablated,K=K,required_authority_digest=authority.digest)

    evidence={
        "schema":"COLLATZ_QCKN_V1_RESEARCH_QUALIFICATION",
        "claim":"Bounded causal reuse of independently verified q0 forward descent macros on the declared sealed future shell; Collatz remains unproved.",
        "contract_digest":contract,
        "authority_digest":authority.digest,
        "training_range":[3,train_hi],
        "future_range":[train_hi+2,future_hi],
        "maxlen":maxlen,"K":K,
        "candidate_capabilities":len(proposals),
        "verified_promotions":verified,
        "acquisition_cost":{
            **discovery,
            "independent_verifications":len(proposals),
            "verified_promotions":verified,
        },
        "compiled_present_digest":present.digest,
        "revocation_digest":digest_payload(sorted(revoke_ids)),
        "arms":{x.name:x.to_canonical() for x in (cold,warm,raw,sham,ablation)},
    }
    assert verified==len(proposals)>0
    assert warm.authoritative_hits>0 and warm.discovery_calls==0
    assert cold.authoritative_hits==0
    assert raw.authoritative_hits==0
    assert sham.authoritative_hits==0
    assert ablation.authoritative_hits==cold.authoritative_hits
    assert ablation.active_capabilities==0
    return evidence

def _fixture_qualification():
    """Fast sealed causal fixture used by CI; same authority path as research runs."""
    contract="collatz-qckn-v1-fixture"
    adapter=CollatzAdapter(contract)
    authority=Authority(contract,"collatz-exact-replay-v1")
    # Source 7 teaches the exact episode 13 -> 5. Source 11 reaches the same
    # episode start after 11 -> 17 -> 26 -> 13, so reuse is genuinely cross-source.
    cap,w=adapter.propose_forward_macro(7,7,((1,2,1),),"fixture-training")
    ledger,verified=promote_verified(((cap,w),),authority)
    present0=CompiledPresent.compile(ledger)
    present=CompiledPresent.from_text(present0.to_text())
    future=({"source":11,"start_m":7,"prefix_steps":3},)

    cold=run_arm("COLD",adapter,future)
    warm=run_arm("WARM",adapter,future,present=present,required_authority_digest=authority.digest)
    raw=run_arm("RAW_HISTORY",adapter,future,raw_history=(cap,))
    sham=run_arm("SHAM",adapter,future,present=sham_present(present),required_authority_digest=authority.digest)

    revoke=ledger.revoke(cap.semantic_id,"qualification ancestor ablation")
    ablated=CompiledPresent.from_text(CompiledPresent.compile(ledger).to_text())
    ablation=run_arm("ANCESTOR_ABLATION",adapter,future,present=ablated,required_authority_digest=authority.digest)

    evidence={
        "schema":"COLLATZ_QCKN_V1_QUALIFICATION",
        "claim":"Bounded causal reuse of independently verified Collatz descent capabilities on the declared sealed future obligation; Collatz remains unproved.",
        "contract_digest":contract,
        "authority_digest":authority.digest,
        "training_sources_digest":digest_payload([7]),
        "future_sources_digest":digest_payload([11]),
        "verified_promotions":verified,
        "compiled_present_digest":present.digest,
        "revocation_event_digest":revoke.event_id,
        "arms":{x.name:x.to_canonical() for x in (cold,warm,raw,sham,ablation)},
    }
    # Qualification gates.
    assert verified==1
    assert warm.authoritative_hits==1 and warm.discovery_calls==0
    assert cold.authoritative_hits==0
    assert raw.authoritative_hits==0
    assert sham.authoritative_hits==0
    assert ablation.authoritative_hits==cold.authoritative_hits
    assert ablation.active_capabilities==0
    return evidence


def qualification_evidence():
    evidence=_fixture_qualification()
    body=canonical_json(evidence)
    return evidence,digest_payload(evidence),body


def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--qualify",action="store_true")
    ap.add_argument("--research-qualify",action="store_true")
    ap.add_argument("--train-hi",type=int,default=8191)
    ap.add_argument("--future-hi",type=int,default=16383)
    ap.add_argument("--K",type=int,default=96)
    ap.add_argument("--maxlen",type=int,default=12)
    args=ap.parse_args(argv)
    if args.research_qualify:
        evidence=research_qualification(args.train_hi,args.future_hi,args.K,args.maxlen)
        print(canonical_json(evidence))
        print("CLOSURE_CERTIFICATE",digest_payload(evidence))
        print("PASS_COLLATZ_QCKN_V1_RESEARCH_CAUSAL_REUSE")
        return
    if args.qualify:
        evidence,certificate,body=qualification_evidence()
        print(body)
        print("CLOSURE_CERTIFICATE",certificate)
        print("PASS_COLLATZ_QCKN_V1_BOUNDED_CAUSAL_REUSE")
        return
    ap.error("--qualify or --research-qualify is required")


if __name__=="__main__":
    main()
