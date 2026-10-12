#!/usr/bin/env python3
"""FLASH V14R: source-authenticated real MathGraph -> RealityGraph event reclosure.

The independent RealityGraph consumer is the authorization and semantic oracle.
The genuine MathGraph published route graph is compiled verbatim into the already
qualified FLASH V13 engine. Source-root admission and local trust revocation
change a scoped downstream RealityGraph research obligation, with replay,
revocation, restart, tamper rejection and matched complete consumer comparison.

Not a new Lean theorem, source requalification, third-party adoption, or newly
invented language. Revocation is a CONTROLLED LOCAL TRUST WITHDRAWAL.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

PRODUCER_SHA256 = "0a850b112cce200f2fa97f0d861db712f3752712a6326e62f4c0d56996a95d87"
HISTORY_SHA256 = "41c2a2d470014b3628695c7aabf5fd0c93f6f687621fca172062f22b59ed6a1e"
CONSUMER_GIT_BLOB = "c1e97c05acfe4bf57f880eabc9c079f3f2cf59ab"
TESTS_GIT_BLOB = "70c822163aed47895c90be35782e6483553ec261"
ENGINE_GIT_BLOB = "081d7599b7806dfd7d0de5e670cbf39d1ebda69a"
PRODUCER_COMMIT = "040456fc8862c79c8b384ce63846628274b678be"
CONSUMER_COMMIT = "9b3189a64825e2cb6ebc7b5c17f5f193bdf5cfe3"
OPENAI_COMMIT = "fd4aeeb2ee4fc729c18d98444fed42fd0529eeeb"
ENGINE_COMMIT = "90d167031bba230399a686252ae5573d57100b94"

def checked_sha256(path: Path, expected: str) -> bytes:
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise ValueError(("EXACT_SOURCE_BYTES_MISMATCH", str(path), actual, expected))
    return raw

def checked_git_blob(path: Path, expected: str) -> None:
    raw=path.read_bytes()
    data=b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw
    actual=hashlib.sha1(data).hexdigest()
    if actual != expected:
        raise ValueError(("SOURCE_CODE_GIT_BLOB_MISMATCH", str(path), actual, expected))

def load_qualified_engines(consumer_root: Path, flash_root: Path):
    checked_git_blob(consumer_root/"research/mathgraph_warrant_consumer_v1.py",CONSUMER_GIT_BLOB)
    checked_git_blob(consumer_root/"tests/test_mathgraph_warrant_consumer_v1.py",TESTS_GIT_BLOB)
    checked_git_blob(flash_root/"flash_engine.py",ENGINE_GIT_BLOB)
    sys.path.insert(0,str(consumer_root))
    sys.path.insert(0,str(flash_root))
    from research import mathgraph_warrant_consumer_v1 as reality
    from flash_engine import RecloseEngine,EventRejected,wire_json
    return reality,RecloseEngine,EventRejected,wire_json

def facts_from_pinned_graph(record:dict, reality) -> tuple[dict,dict,dict,list]:
    graph=record["derivation"]
    claims={q["id"]:q for q in graph["claims"]}
    receipts={q["id"]:q for q in graph["receipts"]}
    routes=reality._typed_routes(graph,claims,receipts)
    # Independently checked source has precisely one live external evidence root.
    live={r for r in receipts if r not in graph["withdrawn_evidence"]}
    if live!={reality.JPL_RECEIPT}:
        raise AssertionError(("NOT_THE_DECLARED_WARRANT_UNIVERSE",sorted(live)))
    if len(claims)!=7 or len(routes)!=4 or len(receipts)!=4:
        raise AssertionError("SOURCE_GRAPH_UNIVERSE_CHANGED")
    return graph,claims,receipts,routes

def generate_fixture(record,claims,receipts,routes,valid_root):
    # ONE-TO-ONE transport of the actual producer's typed AND/OR route edges.
    mapped=[{
        "id": "source-route:"+str(i),
        "when": ["receipt:"+e for e in r["evidence"]]
                + ["claim:"+p for p in r["premises"]],
        "then": "claim:"+r["conclusion"],
    } for i,r in enumerate(routes)]
    assert all(r["when"] and r["then"] not in r["when"] for r in mapped)
    fronts=[{
        "id":"resolve:"+c,
        "budget":0,
        "options":[{
            "id":"answer-from-verified-source:"+c,
            "when":["claim:"+c],
            "unless":[],
            "cost":0
        }]
    } for c in sorted(claims)]
    return {
      "version":"flash-v13-20261012",
      "scope":"real-crossrepo-mathgraph-to-realitygraph-original-routes-v1",
      "producer_commit":PRODUCER_COMMIT,
      "consumer_commit":CONSUMER_COMMIT,
      "source_record_id":record["id"],
      "producer_sha256":PRODUCER_SHA256,
      "base_facts":[],
      "allowed_events":{
        "promote":["receipt:"+valid_root],
        "revoke":["receipt:"+valid_root]
      },
      "rules":mapped,
      "frontiers":fronts,
      "events":[],
      "source_authorities":{
        "producer":PRODUCER_COMMIT,
        "consumer":CONSUMER_COMMIT,
        "publisher_notice":OPENAI_COMMIT,
        "source_root":"prior JPL 48-case receipt is a pinned premise, not a new Lean rerun",
        "no_cross_scope_edges":"derived route list only"
      }
    }

class ExactCrossRepoBridge:
    """No unguarded public raw event submission; source check before admission."""
    def __init__(self, reality, engine_type, event_error, raw_manifest, raw_history):
        self.reality=reality
        self.engine_type=engine_type
        self.event_error=event_error
        self.raw_manifest=raw_manifest
        self.raw_history=raw_history
        self.native=self._verify_sources(raw_manifest,raw_history)
        self.record=reality.read_strict_json(raw_manifest)
        self.graph,self.claims,self.receipts,self.routes=facts_from_pinned_graph(
            self.record,reality)
        self.source_root=reality.JPL_RECEIPT
        self.fixture=generate_fixture(self.record,self.claims,self.receipts,
                                     self.routes,self.source_root)
        self.engine=engine_type(self.fixture)
        self.admitted=set()
        self.event_notes=[]
        self.full_reclose_invocations=0
        self.compare("initial_withheld_source")

    def _verify_sources(self,manifest,history):
        if hashlib.sha256(manifest).hexdigest()!=PRODUCER_SHA256:
            raise self.reality.InvalidWarrant("UNTRUSTED_PUBLICATION_BYTES")
        if hashlib.sha256(history).hexdigest()!=HISTORY_SHA256:
            raise self.reality.InvalidWarrant("OPENAI_SOURCE_SHA256_MISMATCH")
        witness=self.reality.reclose_from_bytes(manifest,history)
        if witness["status"]!="WARRANTED_BOUNDED_CONSUMER_REPLAY":
            raise self.reality.InvalidWarrant("NATIVE_REPLAY_NOT_WARRANTED")
        if witness["independent_states"][self.reality.JPL_CLAIM]["after"]!="WARRANTED_BOUNDED":
            raise self.reality.InvalidWarrant("JPL_PREMISE_NO_LONGER_QUALIFIED")
        return witness

    def compare(self,label):
        # Independent source-consumer's complete fixed-point calculation;
        # withheld receipts are CONTROLLED LOCAL TRUST STATE, not publication.
        withheld=frozenset(set(self.receipts)-self.admitted)
        expected=self.reality.independently_close(self.claims,self.routes,withheld)
        self.full_reclose_invocations+=1
        actual={}
        for claim,verdict in expected.items():
            supported="claim:"+claim in self.engine.active
            active_status=("WARRANTED_BOUNDED" if self.claims[claim]["kind"]=="formal"
                            else "SOURCE_DOCUMENTED") if supported else "UNKNOWN"
            actual[claim]=active_status
            assert actual[claim]==verdict,(label,claim,verdict,actual[claim])
            frontier=self.engine.frontiers["resolve:"+claim]
            assert (frontier["status"]=="SELECTED")==supported,(label,claim,frontier)
        assert len(actual)==7
        return actual

    def admit_from_verified_source(self,manifest,history):
        # Authority comes from the independent consumer, NOT from a caller's
        # invented event status or from FLASH's synthetic_event label.
        self._verify_sources(manifest,history)
        root=self.source_root
        if root in self.graph["withdrawn_evidence"]:
            raise self.reality.InvalidWarrant("SOURCE_ROOT_WITHDRAWN")
        self.admitted.add(root)
        response=self.engine.apply({"kind":"promote","fact":"receipt:"+root,
                                    "authority":"synthetic_event"})
        self.event_notes.append({"kind":"source_validated_admission",
                                 "root":root,"simulation":False})
        self.compare("source_admitted")
        return response

    def locally_revoke_trust(self,reason):
        if reason!="TEST_ONLY_LOCAL_TRUST_WITHDRAWAL":
            raise self.event_error("NO_EXTERNAL_PUBLISHER_REVOCATION_RECORDED")
        self.admitted.discard(self.source_root)
        response=self.engine.apply({"kind":"revoke","fact":"receipt:"+self.source_root,
                                    "authority":"synthetic_revoker"})
        self.event_notes.append({"kind":"controlled_local_trust_revocation",
                                 "reason":reason,"simulation":True})
        self.compare("locally_revoked")
        return response

    def checkpoint_and_restore(self,manifest,history):
        # A checksum-only snapshot NEVER grants source authority.
        self._verify_sources(manifest,history)
        snapshot=self.engine.snapshot()
        restored=self.engine_type.restore(self.fixture,deepcopy(snapshot))
        assert restored.state()==self.engine.state()
        assert restored.event_count==self.engine.event_count
        self.engine=restored
        self.compare("source_revalidated_restart")
        return snapshot

def run(args):
    consumer_root=Path(args.consumer_root).resolve()
    flash_root=Path(args.flash_root).resolve()
    reality,engine_type,event_error,wire_json=load_qualified_engines(
        consumer_root,flash_root)
    manifest=checked_sha256(Path(args.manifest),PRODUCER_SHA256)
    history=checked_sha256(Path(args.history),HISTORY_SHA256)
    bridge=ExactCrossRepoBridge(reality,engine_type,event_error,manifest,history)

    initial=bridge.compare("baseline")
    claim=reality.JPL_CLAIM
    assert initial[claim]=="UNKNOWN"
    # Genuine cross-repo warrant root admitted after independent byte qualification.
    admission=bridge.admit_from_verified_source(manifest,history)
    admitted=bridge.compare("admitted")
    assert admitted[claim]=="WARRANTED_BOUNDED"
    assert [c for c in admitted if admitted[c]!=initial[c]]==[claim]
    assert "resolve:"+claim in admission["changed_frontiers"]

    # Exact compiled present survives restart; source MUST still independently check.
    saved=bridge.checkpoint_and_restore(manifest,history)
    assert bridge.compare("after_restart")==admitted

    def assert_unchanged_then_raises(callback, exception):
        before=bridge.engine.snapshot()
        try:callback()
        except exception:pass
        else:raise AssertionError("FORGED_OR_UNSUPPORTED_ACTION_ACCEPTED")
        assert bridge.engine.snapshot()==before

    assert_unchanged_then_raises(
        lambda:bridge.admit_from_verified_source(manifest+b" ",history),
        reality.InvalidWarrant)
    assert_unchanged_then_raises(
        lambda:bridge.admit_from_verified_source(manifest,history+b"\n# bad edit"),
        reality.InvalidWarrant)
    assert_unchanged_then_raises(
        lambda:bridge.checkpoint_and_restore(manifest,history+b"forged"),
        reality.InvalidWarrant)
    assert_unchanged_then_raises(
        lambda:bridge.locally_revoke_trust("NASA_REVOKED_IT"),
        event_error)
    # Forged graph/scope/claim event rejected by source-derived event whitelist.
    assert_unchanged_then_raises(
        lambda:bridge.engine.apply({"kind":"promote",
                                    "fact":"receipt:openai.original_publication_receipt.1",
                                    "authority":"synthetic_event"}),
        event_error)
    # Tampered locally compiled snapshot is not authoritative.
    broken=deepcopy(saved)
    broken["state"]["base"].append("receipt:FORGED")
    try:engine_type.restore(bridge.fixture,broken)
    except event_error:pass
    else:raise AssertionError("MUTATED_SNAPSHOT_ACCEPTED")

    # Controlled revocation, *not actual JPL/MathGraph withdrawal*.
    loss=bridge.locally_revoke_trust("TEST_ONLY_LOCAL_TRUST_WITHDRAWAL")
    withdrawn=bridge.compare("controlled_revocation")
    assert withdrawn==initial
    assert "resolve:"+claim in loss["changed_frontiers"]
    assert len(loss["changed_frontiers"])==1
    # RESTORE ONLY after independent requalification of the same original bytes.
    snapshot_revoked=bridge.checkpoint_and_restore(manifest,history)
    assert bridge.compare("revoked_restart")==initial
    recovery=bridge.admit_from_verified_source(manifest,history)
    recovered=bridge.compare("recover")
    assert recovered==admitted
    assert "resolve:"+claim in recovery["changed_frontiers"]
    assert len(recovery["changed_frontiers"])==1

    # Historical OpenAI publisher withdrawal remains STALE DOCUMENTARY SUPPORT,
    # not any claim that underlying mathematics has been refuted.
    native=bridge.native
    assert native["stale_documentary_paths"]==3
    assert native["unknown_mathematical_truths"]==3
    for i in (1,2,3):
        assert native["independent_states"]["openai.original_support.%d"%i]["after"]=="STALE"
        assert recovered["openai.theorem.%d"%i]=="UNKNOWN"
        assert recovered["openai.original_support.%d"%i]=="UNKNOWN"
    assert recovered[claim]=="WARRANTED_BOUNDED"

    report={
      "status":"PASS_FLASH_V14R_REAL_CROSS_REPO_WARRANT_RECLOSURE",
      "producer_commit":PRODUCER_COMMIT,
      "consumer_commit":CONSUMER_COMMIT,
      "publisher_source_commit":OPENAI_COMMIT,
      "flash_v13_engine_commit":ENGINE_COMMIT,
      "producer_bytes_sha256":PRODUCER_SHA256,
      "publisher_bytes_sha256":HISTORY_SHA256,
      "source_qualified_claim":claim,
      "scoped_results":{
          "withheld_before_source":initial,
          "qualified_source_admitted":admitted,
          "controlled_local_trust_revoked":withdrawn,
          "source_reverified_after_recovery":recovered,
          "publisher_documentary_states":{
              k:v["after"] for k,v in native["independent_states"].items()
              if k.startswith("openai.original_support.")
          }
      },
      "actual_deltas":{
        "initial_unknown_to_bounded_warrant":1,
        "controlled_revocation_retracted_warrant":1,
        "source_reverification_restored_warrant":1,
        "unaffected_claims":len(admitted)-1
      },
      "realitygraph_full_fixed_point_checks":bridge.full_reclose_invocations,
      "flash_rule_evaluations":bridge.engine.metrics["rule_evaluations"],
      "flash_frontier_evaluations":bridge.engine.metrics["frontier_evaluations"],
      "source_routes_compiled_without_extra_edges":len(bridge.routes),
      "bounded_source_universe":len(bridge.claims),
      "native_unmodified_target_tests":"required in the independent CI workflow",
      "source_attestation":"RealityGraph unmodified pin validator plus SHA256 & Git blobs",
      "event_notes":bridge.event_notes,
      "snapshot_source_revalidated_and_restored":True,
      "negative_controls":{
          "mutated_producer_rejected":True,
          "mutated_notice_rejected":True,
          "unsupported_scope_rejected":True,
          "tampered_snapshot_rejected":True,
          "publisher_withdrawn_receipts_never_admitted":True
      },
      "limitations":[
          "Historical JPL bounded 48-case qualification is a pinned premise, not a new Lean rerun",
          "Publisher withdrawal is actual documentary history; experimental JPL trust revocation is simulated",
          "Targets were previously supported by the independently qualified RealityGraph consumer",
          "Downstream change is a real evidence-resolution task, not a new theorem or solver capability",
          "Same broad ownership; not external third-party adoption",
          "Graph routes are source-supplied; no autonomous new grammar or independent semantics invented",
          "No strict speed/accuracy advantage over equally informed incremental target consumer"
      ]
    }
    output=Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],
      "source_qualified_claim":claim,"actual_deltas":report["actual_deltas"],
      "full_reference_checks":report["realitygraph_full_fixed_point_checks"],
      "incremental_metrics":{
          "rule_evaluations":report["flash_rule_evaluations"],
          "frontier_evaluations":report["flash_frontier_evaluations"]
      }},indent=2,sort_keys=True))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--consumer-root",required=True)
    p.add_argument("--flash-root",required=True)
    p.add_argument("--manifest",required=True)
    p.add_argument("--history",required=True)
    p.add_argument("--output",required=True)
    run(p.parse_args())

if __name__=="__main__":
    main()
