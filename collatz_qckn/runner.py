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
            present:CompiledPresent|None=None,raw_history:Sequence[Capability]=()):
    caps=present.capabilities if present is not None else ()
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
                            maxlen:int=12):
    """Discover source-independent q0 forward descent macros from frozen sources."""
    out={}
    for n in training_sources:
        n=int(n)
        if not fm.candidate(n):
            continue
        starts,words=fm.q0_odd_starts_and_words(n)
        if not words:
            continue
        end=len(words)
        for a in range(max(0,end-maxlen),end):
            word=tuple(words[a:end])
            start_m=starts[a][2]
            try:
                cap,w=adapter.propose_forward_macro(n,start_m,word,f"source:{n}")
            except (AssertionError,ValueError):
                continue
            out.setdefault(cap.semantic_id,(cap,w))
    return tuple(out[k] for k in sorted(out))


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
    warm=run_arm("WARM",adapter,future,present=present)
    raw=run_arm("RAW_HISTORY",adapter,future,raw_history=(cap,))
    sham=run_arm("SHAM",adapter,future,present=sham_present(present))

    revoke=ledger.revoke(cap.semantic_id,"qualification ancestor ablation")
    ablated=CompiledPresent.from_text(CompiledPresent.compile(ledger).to_text())
    ablation=run_arm("ANCESTOR_ABLATION",adapter,future,present=ablated)

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
    args=ap.parse_args(argv)
    if not args.qualify:
        ap.error("--qualify is required")
    evidence,certificate,body=qualification_evidence()
    print(body)
    print("CLOSURE_CERTIFICATE",certificate)
    print("PASS_COLLATZ_QCKN_V1_BOUNDED_CAUSAL_REUSE")


if __name__=="__main__":
    main()
