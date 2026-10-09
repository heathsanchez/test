#!/usr/bin/env python3
"""Collatz ROS V123: source-indexed, phase-aware warranted-future controller.

A *research-state* machine, NOT a termination oracle.

Only an independently replayable LowerClassMerge (n,p,a,b), with 0<p<n
and T^a(n)=T^b(p), changes a protected positive source obligation.
A failed grammar search is always UNKNOWN (or a certified impossibility
for that specific grammar/target), never a Collatz counterexample.

A recorded family law may be promoted to formal warrant ONLY after an
external kernel run at its exact SHA. This process checks integer
instances, provenance shape, and its own replay invariants; it cannot
substitute for a Lean kernel.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path

SCHEMA = "COLLATZ_ROS_LAWFUL_FUTURE_V123"
GOAL = "exclude_second_positive_future_coalescence_class"
BASE_RUNS = {
    "v66_future_quotient": {
        "run": 36840670599, "sha": "1d23ed2a87465fd968db7b333103b6f558d0a433",
        "status": "WARRANTED_FORMAL",
        "scope": "future-coalescence equivalence, quotient stationarity"},
    "v120_phase_schema": {
        "run": 37974704309, "sha": "11f8742f2f84e686845beb080fafb2d113bd183a",
        "status": "WARRANTED_FORMAL",
        "scope": "generic guarded phase merger, refined source27 family"},
    "v121_no_fixed_F27": {
        "run": 37975109424, "sha": "1973d853a3b6d2e50ce59888dd39fcdf5767d43e",
        "status": "WARRANTED_FORMAL",
        "scope": "no positive p<27 reaches F(27)=83 at any clock"},
    "v122_exact_first_join_27": {
        "run": 37975443683, "sha": "f6dec5d5ae9ae681868e1f0f29bbd494267c8bfd",
        "status": "WARRANTED_FORMAL",
        "scope": "27 first joins any smaller positive future at source clock 59"},
    "v123_bounded_arithmetic": {
        "run": None, "sha": None, "status": "BOUNDED_EXACT",
        "scope": "exact arithmetic replay of 11->3 and 3->2 and composition"},
}

def shortcut(n: int) -> int:
    if type(n) is not int or n <= 0:
        raise ValueError("shortcut domain is positive natural numbers")
    return n // 2 if n % 2 == 0 else (3 * n + 1) // 2

def iterate(n: int, clock: int) -> int:
    if type(clock) is not int or clock < 0 or clock > 10000:
        raise ValueError("invalid exact finite clock")
    for _ in range(clock):
        n = shortcut(n)
    return n

def canonical(data) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def digest(data) -> str:
    return hashlib.sha256(canonical(data).encode()).hexdigest()

def verify_join(join: dict) -> int:
    n, p, a, b = (join[k] for k in ("source", "earlier", "source_clock", "earlier_clock"))
    if any(type(x) is not int for x in (n, p, a, b)):
        raise ValueError("join contains a noninteger coordinate")
    if not (0 < p < n):
        raise ValueError("join does not strictly reduce ORIGINAL positive source")
    actual_n, actual_p = iterate(n, a), iterate(p, b)
    if actual_n != actual_p:
        raise ValueError("actual two-clock trajectories do not coalesce")
    if join.get("common") != actual_n:
        raise ValueError("recorded common endpoint does not match replay")
    return actual_n

def make_join(n: int, p: int, a: int, b: int, support: str,
              origin: str, parents=()) -> dict:
    raw = {"source": n, "earlier": p, "source_clock": a, "earlier_clock": b,
           "common": iterate(n, a), "support": support, "origin": origin,
           "parents": list(parents)}
    verify_join(raw)
    raw["id"] = digest({k: raw[k] for k in
       ("source", "earlier", "source_clock", "earlier_clock", "support", "origin", "parents")})[:20]
    return raw

def compose(first: dict, second: dict, support: str = "v123_bounded_arithmetic") -> dict:
    verify_join(first)
    verify_join(second)
    if first["earlier"] != second["source"]:
        raise ValueError("the actual INTERMEDIATE original source is not shared")
    # Source n->p at clocks (a,b), and p->q at (c,d):
    # n->q at clocks (a+c,d+b), NOT necessarily equal clocks.
    return make_join(first["source"], second["earlier"],
        first["source_clock"] + second["source_clock"],
        second["earlier_clock"] + first["earlier_clock"],
        support, "CERTIFIED_RECOMPOSITION",
        [first["id"], second["id"]])

def fixed_F27_no_smaller_preimage() -> dict:
    """Exact finite invariant, the same protected fact Lean checked in V121."""
    envelope = set(range(1, 27)) | {29, 32, 35, 38, 40, 44, 53, 80}
    if len(envelope) != 34 or max(envelope) != 80:
        raise AssertionError("wrong frozen envelope")
    if any(shortcut(x) not in envelope for x in envelope):
        raise AssertionError("envelope is not forward invariant")
    if 83 in envelope:
        raise AssertionError("the protected F(27) separator is lost")
    return {"source": 27, "target": 83, "grammar": "FIXED_F_SOURCE",
       "verdict": "EXCLUDED_ONLY_FOR_THIS_FIXED_ENDPOINT",
       "support": "v121_no_fixed_F27", "closed_set_size": len(envelope),
       "max_reachable_from_any_smaller_source": max(envelope)}

def verify_earliest_source27() -> None:
    env = set(range(1, 27)) | {29, 32, 35, 38, 40, 44, 53, 80}
    v = 27
    for t in range(59):
        if v in env:
            raise AssertionError(f"earlier-source future touched prematurely at clock {t}")
        v = shortcut(v)
    if v != 23 or v not in env:
        raise AssertionError("clock 59 is not the verified first actual earlier-source join")

def ghost_prefix(k: int) -> dict:
    """The negative 2-adic -1 shadow is a finite word, NEVER a natural counterexample."""
    if type(k) is not int or not 1 <= k <= 512:
        raise ValueError("ghost horizon must be finite and positive")
    n = (1 << k) - 1
    x = n
    for j in range(k + 1):
        if x != 3 ** j * (1 << (k - j)) - 1:
            raise AssertionError("purported negative 2-adic shadow is not an actual prefix")
        if j < k:
            x = shortcut(x)
    # A fixed positive natural N cannot satisfy 2^j | (N+1) for ALL j.
    bound = (n + 1).bit_length() + 1
    assert (n + 1) % (1 << bound) != 0
    return {"horizon": k, "changing_source": n,
       "type": "FINITE_POSITIVE_SHADOW_OF_NEGATIVE_2ADIC_FIXED_POINT",
       "cannot_infer_positive_infinite_survivor": True,
       "fixed_natural_nondivisibility_witness_exponent": bound}

def initial_state() -> dict:
    state = {
       "schema": SCHEMA, "objective": GOAL,
       "global_collatz": "UNKNOWN", "qed": False,
       "universal_event_producer_proved": False,
       "grammar": {"active": "FIXED_F_SOURCE", "revision": 0,
          "constructors": ["fixed_F_endpoint_reverse"],
          "rejected_as_complete": []},
       "support": deepcopy(BASE_RUNS),
       "joins": [], "archived_joins": [],
       "rejected_candidates": [fixed_F27_no_smaller_preimage()],
       "residuals": [
           {"source": 27, "status": "UNKNOWN_IN_GRAMMAR",
            "grammar": "FIXED_F_SOURCE",
            "reason": "F(27)=83 has NO smaller positive preimage at any clock"},
           {"source_family": "V120_old_CRT_partition",
            "status": "UNKNOWN_IN_GRAMMAR",
            "remaining_classes": 159938,
            "reason": "grammar-relative remainder; not 159938 counterexamples"}],
       "negative_controls": [
          {"type": "opposite_phase", "n": 3, "F_n": 11,
           "assertion": "no_equal_clock_collision; asymmetric two-clock join exists",
           "support": "v66_future_quotient"},
          ghost_prefix(24), ghost_prefix(80)],
       "history": [], "retired_hypotheses": [
          "fixed_f_target_complete",
          "fixed_bounded_delay_implies_nonconvergence",
          "finite_2adic_shadow_is_natural_bad_source"],
    }
    return state

class Controller:
    def __init__(self, state: dict):
        self.state = deepcopy(state)
        self.audit()

    def audit(self) -> None:
        s = self.state
        if s.get("schema") != SCHEMA or s.get("objective") != GOAL:
            raise ValueError("different or stale protected objective")
        if s.get("qed") is not False or s.get("global_collatz") != "UNKNOWN":
            raise ValueError("universal theorem cannot be promoted from this ledger")
        if s.get("universal_event_producer_proved") is not False:
            raise ValueError("no qualified universal event producer is present")
        ids = set()
        for join in s["joins"] + s["archived_joins"]:
            verify_join(join)
            if join["id"] in ids:
                raise ValueError("duplicate or colliding join ID")
            ids.add(join["id"])
            if join["support"] not in s["support"]:
                raise ValueError("unknown warrant support")
        for join in s["joins"]:
            if s["support"][join["support"]]["status"] in ("REVOKED", "UNKNOWN"):
                raise ValueError("revoked or unknown support cannot authorize an active claim")
        for neg in s["rejected_candidates"]:
            if neg["verdict"] != "EXCLUDED_ONLY_FOR_THIS_FIXED_ENDPOINT":
                raise ValueError("invalid strengthening of grammar-relative negative result")
        fixed_F27_no_smaller_preimage()
        verify_earliest_source27()
        for x in s["negative_controls"]:
            if x.get("type") == "FINITE_POSITIVE_SHADOW_OF_NEGATIVE_2ADIC_FIXED_POINT":
                if x != ghost_prefix(x["horizon"]):
                    raise ValueError("corrupted finite shadow or naturalness claim")

    def add(self, join: dict) -> bool:
        verify_join(join)
        if join["support"] not in self.state["support"]:
            raise ValueError("no named live support")
        if self.state["support"][join["support"]]["status"] in ("REVOKED", "UNKNOWN"):
            raise ValueError("support not live")
        if any(x["id"] == join["id"] for x in self.state["joins"] + self.state["archived_joins"]):
            return False
        self.state["joins"].append(deepcopy(join))
        self.state["history"].append({
           "op": "WARRANTED_BOUNDED_CONSEQUENCE",
           "source": join["source"], "join_id": join["id"],
           "support": join["support"]})
        self.audit()
        return True

    def refine(self) -> bool:
        s = self.state
        if s["grammar"]["active"] == "SOURCE_INDEXED_TWO_CLOCK":
            return False
        if s["grammar"]["active"] != "FIXED_F_SOURCE":
            raise ValueError("unexpected predecessor grammar")
        old = s["grammar"]["active"]
        s["grammar"] = {"active": "SOURCE_INDEXED_TWO_CLOCK",
            "revision": 1, "constructors": [
                "actual_source_to_earlier_two_clock_join",
                "monotone_warranted_join_composition",
                "finite_negative_2adic_naturalness_guard"],
            "rejected_as_complete": ["FIXED_F_SOURCE"]}
        s["residuals"][0] = {
            "source": 27, "status": "REFINED_GRAMMAR_SEPARATED",
            "grammar": old,
            "reason": "all-clock fixed F impossibility, not a nonconvergent integer"}
        s["history"].append({"op": "REFINE_FROM_PROTECTED_SEPARATOR",
            "old_grammar": old, "new_grammar": "SOURCE_INDEXED_TWO_CLOCK",
            "separator": "V121_SOURCE_27_F83_NO_SMALLER_PREIMAGE",
            "proof_run": 37975109424})
        self.audit()
        return True

    def reclose(self) -> int:
        """Derive implied source class-merger consequences without new searches."""
        if self.state["grammar"]["active"] != "SOURCE_INDEXED_TWO_CLOCK":
            return 0
        added = 0
        while True:
            found = False
            joins = list(self.state["joins"])
            for x in joins:
                for y in joins:
                    if x["earlier"] != y["source"] or x["source"] == y["earlier"]:
                        continue
                    derived = compose(x, y)
                    # Ignore equivalent or weaker alternate representations of
                    # an already protected source->earlier consequence.
                    if any(j["source"] == derived["source"] and
                           j["earlier"] == derived["earlier"]
                           for j in self.state["joins"]):
                        continue
                    if self.add(derived):
                        added += 1
                        found = True
                        break
                if found:
                    break
            if not found:
                return added
            # A finite initial ledger can grow, but never invent larger
            # predecessors: sources form a well-founded strict order.

    def revoke(self, support_id: str) -> int:
        if support_id not in self.state["support"]:
            raise ValueError("unknown support")
        s = self.state
        if s["support"][support_id]["status"] == "REVOKED":
            return 0
        s["support"][support_id]["status"] = "REVOKED"
        # Transitive dependency closure: composed entries depend on parents
        # even when the immediate new entry has a different support label.
        removed_ids = set()
        archive = []
        while True:
            new = [w["id"] for w in s["joins"] if
                   (w["support"] == support_id or
                    any(k in removed_ids for k in w.get("parents", [])))]
            if set(new).issubset(removed_ids):
                break
            removed_ids.update(new)
        retained = []
        for w in s["joins"]:
            if w["id"] in removed_ids:
                archive.append(w)
            else:
                retained.append(w)
        s["joins"] = retained
        s["archived_joins"].extend(archive)
        s["history"].append({"op": "REVOKE_SUPPORT_AND_DEPENDENTS",
            "support": support_id, "archived_joins": len(archive)})
        if any(w["source"] == 27 for w in archive):
            s["residuals"].append({"source": 27, "status": "REOPENED_AFTER_REVOCATION",
                "support": support_id, "reason": "former join cannot be used without live proof"})
        self.audit()
        return len(archive)

    def status(self, source: int) -> dict:
        options = [w for w in self.state["joins"] if w["source"] == source]
        if options:
            w = min(options, key=lambda j: (j["source_clock"], j["earlier"], j["earlier_clock"]))
            return {"source": source, "status": "WARRANTED_BOUNDED_LOWER_MERGE",
                    "earlier": w["earlier"], "source_clock": w["source_clock"],
                    "earlier_clock": w["earlier_clock"], "common": w["common"]}
        return {"source": source, "status": "UNKNOWN_UNDER_CURRENT_WARRANTS"}

def bootstrap() -> Controller:
    c = Controller(initial_state())
    c.refine()
    c.add(make_join(27, 23, 59, 0, "v122_exact_first_join_27",
                    "LEAN_FORMAL_SOURCE27_EXACT_FIRST_CLOCK"))
    c.add(make_join(11, 3, 6, 1, "v123_bounded_arithmetic", "EXACT_ASYNCHRONOUS_ORBIT"))
    c.add(make_join(3, 2, 4, 0, "v123_bounded_arithmetic", "EXACT_SMALLER_SOURCE"))
    assert c.reclose() == 1
    assert c.status(27)["source_clock"] == 59
    assert c.status(11)["status"] == "WARRANTED_BOUNDED_LOWER_MERGE"
    c.audit()
    return c

def from_file(path: Path) -> Controller:
    return Controller(json.loads(path.read_text()))

def dump(c: Controller, path: Path) -> str:
    c.audit()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(c.state, sort_keys=True, indent=2) + "\n")
    return digest(c.state)

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", action="store_true")
    ap.add_argument("--input", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--revoke-support")
    opt = ap.parse_args()
    if opt.bootstrap == bool(opt.input):
        ap.error("choose exactly one of --bootstrap or --input")
    c = bootstrap() if opt.bootstrap else from_file(opt.input)
    archived = c.revoke(opt.revoke_support) if opt.revoke_support else 0
    checksum = dump(c, opt.output) if opt.output else digest(c.state)
    print(json.dumps({"schema": SCHEMA, "active_grammar": c.state["grammar"]["active"],
      "active_joins": len(c.state["joins"]), "archived": archived,
      "source27": c.status(27), "source11": c.status(11),
      "global_collatz": "UNKNOWN", "qed": False,
      "state_sha256": checksum}, sort_keys=True))

if __name__ == "__main__":
    main()
