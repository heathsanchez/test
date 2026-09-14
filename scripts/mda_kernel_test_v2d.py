#!/usr/bin/env python3
"""
MDA Kernel Test v2d — solvent's necessity claim disciplined to its one sound
evidence source (genesis signature); UNKNOWN elsewhere, proven not assumed.

Changes from v2b:
  - solvent() now does real duplicate-transition-row detection (structural
    clone redundancy) instead of unconditionally labeling every state
    "necessary_given_current". Scope note: without a separate output
    alphabet at the Present layer, this catches *structural* clones
    (identical transition rows) — not full language-equivalence merging.
    That's a real but bounded notion of necessity, stated honestly.
  - genesis() now records which k values were tried and rejected on
    right-congruence grounds (congruence_retries), and collects Pareto
    candidates for a genuinely-computed frontier instead of the test
    hand-assigning present.frontier.
  - meta_obstruct() now REFUSES to escalate change_lang unless there is
    actual evidence basic_quotient was insufficient (a congruence retry
    occurred, or solvent found a structural contradiction). Previously it
    escalated unconditionally on any call.
  - Added negative-control checks (C3, E3, F2) that exercise the failure
    path of each repaired function, not just the happy path — a check
    that can only ever pass isn't verification.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, FrozenSet
from collections import defaultdict
import itertools
import hashlib
import json
import copy

# ============================================================
# Hidden 4-state shift register (last two bits)
# k=1 -> 2 classes (rejected on right-congruence grounds, not instability);
# k>=2 -> 4 classes (exact minimal, right-congruent, stable).
# ============================================================

HIDDEN = {
    0: {0: (0, 0), 1: (1, 1)},  # 00
    1: {0: (2, 0), 1: (3, 1)},  # 01
    2: {0: (0, 1), 1: (1, 0)},  # 10
    3: {0: (2, 1), 1: (3, 0)},  # 11
}

def run_hidden(history: str) -> int:
    s = 0
    for b in history:
        s, _ = HIDDEN[s][int(b)]
    return s

def future_vector(history: str, k: int) -> str:
    if k == 0:
        return "eps"
    state = run_hidden(history)
    vecs = []
    for fut in itertools.product("01", repeat=k):
        s = state
        outs = []
        for b in fut:
            s, o = HIDDEN[s][int(b)]
            outs.append(str(o))
        vecs.append("".join(outs))
    return "|".join(vecs)

def true_n_classes(k: int, prefixes: List[str]) -> int:
    return len({future_vector(h, k) for h in prefixes})

# ============================================================
# Kernel objects
# ============================================================

@dataclass
class Evidence:
    obs: Dict[str, str] = field(default_factory=dict)
    closed: Set[str] = field(default_factory=set)
    horizon: int = 0

@dataclass
class Present:
    states: FrozenSet[str] = field(default_factory=frozenset)
    state_of: Dict[str, str] = field(default_factory=dict)
    transitions: Dict[Tuple[str, str], str] = field(default_factory=dict)
    compiled: List[Dict] = field(default_factory=list)
    change_lang: str = "basic_quotient"
    provenance: List[str] = field(default_factory=list)
    cost: int = 0
    frontier: List[str] = field(default_factory=list)
    necessity: Dict[str, str] = field(default_factory=dict)
    # NEW: evidence fields the repaired functions actually consult
    congruence_retries: List[int] = field(default_factory=list)
    solvent_contradiction: bool = False
    solvent_uncertain: bool = False
    signature: Dict[str, str] = field(default_factory=dict)  # state -> distinguishing witness

    def fp(self) -> str:
        blob = json.dumps({
            "states": sorted(self.states),
            "n_trans": len(self.transitions),
            "lang": self.change_lang,
            "n_comp": len(self.compiled),
        }, sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:10]

# ============================================================
# Behavioral floor
# ============================================================

def induce_quotient(prefixes: List[str], k: int):
    """Returns (state_of, states, signature) where signature[state] is the
    k-horizon future-vector that DEFINED that quotient class -- the evidence
    that made the class distinct in the first place. Downstream code must
    carry this forward or it loses the ability to verify necessity later."""
    groups: Dict[str, List[str]] = defaultdict(list)
    for h in prefixes:
        groups[future_vector(h, k)].append(h)
    state_of = {}
    signature = {}
    for i, (sig, hs) in enumerate(sorted(groups.items())):
        sid = f"S{i}"
        signature[sid] = sig
        for h in hs:
            state_of[h] = sid
    return state_of, frozenset(state_of.values()), signature

def is_right_congruent(state_of: Dict[str, str], prefixes: List[str]) -> bool:
    """Only require congruence on histories whose one-step extensions are also present."""
    by_state: Dict[str, List[str]] = defaultdict(list)
    for h, s in state_of.items():
        by_state[s].append(h)
    for s, hs in by_state.items():
        for a in "01":
            images = set()
            covered = 0
            for h in hs:
                ha = h + a
                if ha in state_of:
                    images.add(state_of[ha])
                    covered += 1
            if covered == 0:
                continue
            if len(images) > 1:
                return False
    return True

def is_stable(so_k: Dict[str, str], so_kp1: Dict[str, str], prefixes: List[str]) -> bool:
    mapping: Dict[str, Set[str]] = defaultdict(set)
    for h in prefixes:
        if h in so_k and h in so_kp1:
            mapping[so_k[h]].add(so_kp1[h])
    return all(len(v) <= 1 for v in mapping.values())

def find_first_stable(prefixes: List[str], max_k: int):
    """
    Returns (k, state_of, states, status, congruence_retries, candidates)
      congruence_retries: k values whose quotient FAILED right-congruence
                           (real evidence basic partitioning needed search)
      candidates: [(k, n_states, n_trans)] for every k that WAS right-congruent,
                  whether or not it was chosen -- used to build a real frontier
    """
    retries = []
    candidates = []
    for k in range(0, max_k + 1):
        so, st, sig = induce_quotient(prefixes, k)
        if not is_right_congruent(so, prefixes):
            retries.append(k)
            continue
        trans_k = {}
        for h, s in so.items():
            for a in "01":
                ha = h + a
                if ha in so:
                    trans_k[(s, a)] = so[ha]
        candidates.append((k, len(st), len(trans_k)))
        if k + 1 <= max_k:
            so1, _, _ = induce_quotient(prefixes, k + 1)
            if is_stable(so, so1, prefixes):
                return k, so, st, sig, "VERIFIED_STABLE", retries, candidates
        else:
            return k, so, st, sig, "VERIFIED_PROVISIONAL", retries, candidates
    return None, {}, frozenset(), {}, "UNKNOWN_SEARCH_OR_HORIZON", retries, candidates

# ============================================================
# Diagnosis, genesis, solvent, compile, transfer, meta
# ============================================================

def diagnose(ev: Evidence, want_k: int) -> str:
    if ev.horizon < want_k:
        return "UNKNOWN_WARRANT_HORIZON"
    if any(h not in ev.closed for h in ev.obs):
        return "UNKNOWN_IDENTIFIABILITY"
    return "AUTHORITY_ADEQUATE"

def pareto_frontier(candidates: List[Tuple[int, int, int]]) -> List[str]:
    """Real Pareto frontier over (n_states, n_trans), minimizing both."""
    pts = [(ns, nt, k) for (k, ns, nt) in candidates]
    frontier_pts = []
    for p in pts:
        dominated = any(
            (q[0] <= p[0] and q[1] <= p[1] and q != p and (q[0] < p[0] or q[1] < p[1]))
            for q in pts
        )
        if not dominated:
            frontier_pts.append(p)
    # dedupe
    frontier_pts = sorted(set(frontier_pts))
    return [f"k={k}:states={ns}:trans={nt}" for (ns, nt, k) in frontier_pts]

def genesis(present: Present, prefixes: List[str], max_k: int) -> Present:
    new = copy.deepcopy(present)
    new.cost += 15
    k, so, st, sig, status, retries, candidates = find_first_stable(prefixes, max_k)
    new.congruence_retries = retries
    if k is None:
        new.provenance.append(f"genesis failed: {status}")
        return new
    new.state_of = so
    new.states = st
    new.signature = sig  # carry the distinguishing witness forward -- this was the bug
    trans = {}
    for h, s in so.items():
        for a in "01":
            ha = h + a
            if ha in so:
                trans[(s, a)] = so[ha]
    new.transitions = trans
    new.frontier = pareto_frontier(candidates)
    new.provenance.append(
        f"genesis k={k} status={status} n_states={len(st)} "
        f"congruence_retries={retries} frontier={new.frontier}"
    )
    return new

def solvent(present: Present) -> Present:
    """
    Necessity evidence has exactly ONE sound source in this system: genesis's
    signature (the k-horizon future-vector that DEFINED each state). This is
    not an assumption -- it was tested against three alternatives, all
    falsified:
      1. one-step exact-transition-row match: iterated to a genuine fixed
         point, collapses ALL states to ONE class (verified empirically --
         see dev notes). Matches the general theorem that a deterministic
         automaton with no output/label channel is trivially bisimilar to
         itself everywhere; any non-trivial answer from this method is an
         artifact of stopping early, not a real invariant.
      2. structural seeds (self-loop pattern, in-degree) computed purely from
         (states, transitions): falsified by an adversarial disconnected-
         2-cycle construction where two structurally-identical subgraphs are
         genuinely distinct per ground truth -- the seed cannot see this,
         because it's blind by construction to anything outside the local
         transition graph.
      3. full Moore/Hopcroft fixed-point refinement from a single seed block:
         a no-op by definition (refinement only ever splits an existing
         partition; a label-less automaton has no seed to split from).

    So: if present.signature is available, redundancy is certified by an
    EXACT signature match (which, by genesis's own construction, should
    never fire for a correctly-built Present -- see C4 for a deliberately
    broken probe that proves this guard is a real discriminator, not a
    tautology). If no signature is available, this function makes NO
    necessity claim in either direction -- it reports UNKNOWN, because no
    sound signature-free method exists.
    """
    new = copy.deepcopy(present)
    new.cost += 8
    if len(present.states) <= 1:
        new.provenance.append("solvent: trivial")
        new.necessity = {s: "necessary_given_current" for s in present.states}
        new.solvent_contradiction = False
        new.solvent_uncertain = False
        return new

    if not present.signature:
        new.necessity = {s: "UNKNOWN_no_signature" for s in present.states}
        new.solvent_contradiction = False
        new.solvent_uncertain = True
        new.provenance.append(
            "solvent: UNKNOWN for all states -- no signature available and "
            "no sound signature-free necessity method exists (see docstring)"
        )
        return new

    nec: Dict[str, str] = {}
    redundant = []
    for s in present.states:
        dups = sorted(
            t for t in present.states
            if t != s and present.signature.get(t) == present.signature.get(s)
        )
        if dups:
            nec[s] = f"redundant_duplicate_of:{','.join(dups)}"
            redundant.append(s)
        else:
            nec[s] = "necessary_given_current"
    new.necessity = nec
    new.solvent_contradiction = len(redundant) > 0
    new.solvent_uncertain = False
    new.provenance.append(
        f"solvent: {len(present.states) - len(redundant)} necessary, "
        f"{len(redundant)} certified redundant (signature collision -- "
        f"should never fire for correctly-built genesis output; a hit here "
        f"means genesis has a construction bug)"
    )
    return new

def compile_rule(present: Present, name: str, scope: str, benefit: int) -> Present:
    new = copy.deepcopy(present)
    new.compiled.append({"name": name, "scope": scope, "benefit": benefit})
    new.cost += 4
    new.provenance.append(f"compile {name} scope={scope}")
    return new

def transfer(present: Present, scope: str, n_tasks: int) -> Tuple[Present, Dict]:
    new = copy.deepcopy(present)
    used = rejected = saved = 0
    for i in range(n_tasks):
        matched = any(r["scope"] == scope for r in present.compiled)
        if matched:
            used += 1
            saved += next(r["benefit"] for r in present.compiled if r["scope"] == scope)
        else:
            rejected += 1
            new.provenance.append(f"SCOPE_FAILURE scope={scope} task={i}")
    return new, {
        "used": used,
        "rejected": rejected,
        "saved": saved,
        "status": "TRANSFER_OK" if rejected == 0 else "SCOPE_FAILURE",
    }

def meta_obstruct(present: Present) -> Present:
    """
    Only escalates change_lang if there is real evidence basic_quotient was
    insufficient: either genesis had to retry past a right-congruence
    failure, or solvent found a structural contradiction (redundant
    duplicate states). Absent both, refuses to escalate.
    """
    if present.change_lang != "basic_quotient":
        return present
    new = copy.deepcopy(present)
    has_evidence = bool(present.congruence_retries) or present.solvent_contradiction
    if not has_evidence:
        new.provenance.append(
            "OBSTRUCTION_NOT_WARRANTED: no congruence retries, no solvent "
            "contradiction -> basic_quotient retained"
        )
        return new
    new.change_lang = "quotient_plus_relation"
    new.cost += 25
    reasons = []
    if present.congruence_retries:
        reasons.append(f"congruence_retries={present.congruence_retries}")
    if present.solvent_contradiction:
        reasons.append("solvent_contradiction=True")
    new.provenance.append(
        f"CERTIFIED_OBSTRUCTION of change_lang -> quotient_plus_relation ({'; '.join(reasons)})"
    )
    return new

# ============================================================
# Test runner
# ============================================================

def run():
    results = {"checks": []}

    def chk(name, cond, detail=""):
        results["checks"].append({"name": name, "pass": bool(cond), "detail": detail})
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

    print("=" * 70)
    print("MDA KERNEL TEST v2d — necessity claims disciplined to sound evidence")
    print("=" * 70)

    prefixes = [""] + [
        "".join(p) for r in range(1, 5) for p in itertools.product("01", repeat=r)
    ]
    print(f"prefixes: {len(prefixes)} (len 0..4)")

    # A. Short / open -> UNKNOWN
    print("\n--- A. Short horizon & open supports ---")
    ev = Evidence(horizon=1)
    for h in prefixes:
        ev.obs[h] = future_vector(h, 1)
    chk("A1 UNKNOWN_WARRANT_HORIZON", diagnose(ev, 2) == "UNKNOWN_WARRANT_HORIZON")

    ev.horizon = 2
    for h in prefixes:
        ev.obs[h] = future_vector(h, 2)
    chk("A2 UNKNOWN_IDENTIFIABILITY", diagnose(ev, 2) == "UNKNOWN_IDENTIFIABILITY")

    # B. Close + adequate -> recover exact 4 states
    print("\n--- B. Closed authority, recover minimal predictive states ---")
    ev.horizon = 3
    for h in prefixes:
        ev.obs[h] = future_vector(h, 3)
    ev.closed = set(prefixes)
    chk("B1 AUTHORITY_ADEQUATE", diagnose(ev, 2) == "AUTHORITY_ADEQUATE")

    present = Present()
    present = genesis(present, prefixes, max_k=3)
    n = len(present.states)
    k_used = None
    for p in present.provenance:
        if p.startswith("genesis k="):
            k_used = int(p.split()[1].split("=")[1])
            break
    true_n = true_n_classes(k_used, prefixes) if k_used is not None else -1
    chk("B2 recovered exact minimal state count", n == true_n and n == 4,
        f"got {n}, true@{k_used}={true_n}")
    chk("B3 k=1 correctly rejected on right-congruence grounds (real evidence, not vacuous)",
        present.congruence_retries == [1], f"congruence_retries={present.congruence_retries}")
    chk("B4 transitions induced", len(present.transitions) >= 4, f"n_trans={len(present.transitions)}")

    # C. Solvent — now with a real negative control
    print("\n--- C. Solvent & contextual necessity (repaired) ---")
    present = solvent(present)
    chk("C1 necessity recorded for all states", len(present.necessity) == n)
    chk("C2 genuinely-minimal genesis output has zero redundant duplicates",
        present.solvent_contradiction is False, str(present.necessity))

    # C3 [negative control, REVISED]: no-signature Present, even one that
    # LOOKS obviously redundant to a human (both states go to the same
    # target on every symbol) -- solvent must report UNKNOWN, not guess.
    # This looked like it "should" pass as redundant in v2c; that guess
    # would have been right here by luck and wrong on the adversarial
    # disconnected-cycle case above. Consistency, not case-by-case luck,
    # is what's being verified.
    no_sig_probe = Present(
        states=frozenset({"S0", "S1"}),
        transitions={("S0", "0"): "S0", ("S0", "1"): "S0",
                     ("S1", "0"): "S0", ("S1", "1"): "S0"},
    )
    no_sig_probe = solvent(no_sig_probe)
    chk("C3 [negative control] solvent reports UNKNOWN (not a guess) with no signature, even on an 'obvious' case",
        all(v == "UNKNOWN_no_signature" for v in no_sig_probe.necessity.values())
        and no_sig_probe.solvent_uncertain is True
        and no_sig_probe.solvent_contradiction is False,
        str(no_sig_probe.necessity))

    # C4 [negative control]: deliberately broken signature (simulating a
    # genesis construction bug: two different state IDs sharing one
    # signature) -- proves the signature-match guard is a real discriminator,
    # not a tautology that can only ever say "necessary".
    broken_sig_probe = Present(
        states=frozenset({"S0", "S1"}),
        transitions={("S0", "0"): "S0", ("S0", "1"): "S1",
                     ("S1", "0"): "S1", ("S1", "1"): "S0"},
        signature={"S0": "same_sig", "S1": "same_sig"},
    )
    broken_sig_probe = solvent(broken_sig_probe)
    chk("C4 [negative control] solvent DOES certify redundancy when genesis's own signature invariant is violated",
        broken_sig_probe.necessity["S0"].startswith("redundant_duplicate_of")
        and broken_sig_probe.solvent_contradiction is True,
        str(broken_sig_probe.necessity))

    # C5 [permanent regression guard]: the adversarial disconnected-2-cycle
    # case that falsified the structural-seed heuristic during development.
    # No signature is available; the correct answer is UNKNOWN. If someone
    # later reintroduces a signature-free structural heuristic into solvent,
    # this is the case that will catch it wrongly claiming "redundant".
    cycle_probe = Present(
        states=frozenset({"A", "B", "C", "D"}),
        transitions={("A", "0"): "B", ("A", "1"): "B",
                     ("B", "0"): "A", ("B", "1"): "A",
                     ("C", "0"): "D", ("C", "1"): "D",
                     ("D", "0"): "C", ("D", "1"): "C"},
    )
    cycle_probe = solvent(cycle_probe)
    chk("C5 [permanent regression guard] graph-symmetric-but-distinct case stays UNKNOWN, never falsely merged",
        all(v == "UNKNOWN_no_signature" for v in cycle_probe.necessity.values()),
        str(cycle_probe.necessity))

    # D. Transfer economics
    print("\n--- D. Held-out transfer economics ---")
    present = compile_rule(present, "pred_step", "horizon<=3", benefit=12)
    present, rep = transfer(present, "horizon<=3", 3)
    chk("D1 useful transfer reduces work", rep["used"] == 3 and rep["status"] == "TRANSFER_OK", str(rep))
    cost_before = present.cost
    present, rep2 = transfer(present, "horizon<=9", 3)
    chk("D2 scope failure rejected", rep2["rejected"] == 3 and rep2["status"] == "SCOPE_FAILURE")
    chk("D3 zero redevelopment cost (DIC-1)", present.cost == cost_before, f"delta={present.cost - cost_before}")

    # E. Meta-obstruction — now evidence-gated, with a real negative control
    print("\n--- E. Meta-obstruction of change language (repaired) ---")
    lang_before = present.change_lang
    present = meta_obstruct(present)
    chk("E1 change_lang escalates WHEN real evidence exists (congruence retry at k=1)",
        present.change_lang == "quotient_plus_relation" and lang_before == "basic_quotient")
    chk("E2 provenance cites the actual evidence, not a bare assertion",
        any("CERTIFIED_OBSTRUCTION" in p and "congruence_retries=[1]" in p for p in present.provenance),
        [p for p in present.provenance if "OBSTRUCTION" in p])

    clean_probe = Present(change_lang="basic_quotient")  # no retries, no contradiction
    clean_probe = meta_obstruct(clean_probe)
    chk("E3 [negative control] meta_obstruct REFUSES to escalate with no evidence",
        clean_probe.change_lang == "basic_quotient"
        and any("OBSTRUCTION_NOT_WARRANTED" in p for p in clean_probe.provenance),
        clean_probe.provenance)

    # F. Identity — now with a real negative control
    print("\n--- F. Identity continuation (repaired) ---")
    fp0 = present.fp()
    chk("F1 identity preserves fingerprint under no-op copy", copy.deepcopy(present).fp() == fp0)

    mutated = copy.deepcopy(present)
    mutated.states = frozenset(present.states) | {"S99"}
    chk("F2 [negative control] fingerprint CHANGES when structure actually changes",
        mutated.fp() != fp0, f"{mutated.fp()} vs {fp0}")

    # G. Frontier — now genuinely computed by genesis, not hand-assigned by the test
    print("\n--- G. Frontier (repaired: computed by kernel, not injected by test) ---")
    frontier = present.frontier
    chk("G1 frontier is non-empty and kernel-computed", len(frontier) >= 1, frontier)

    # Summary
    print("\n--- Final present ---")
    print(f"  states        : {sorted(present.states)}")
    print(f"  n_transitions : {len(present.transitions)}")
    print(f"  change_lang   : {present.change_lang}")
    print(f"  cost          : {present.cost}")
    print(f"  necessity     : {present.necessity}")
    print(f"  frontier      : {present.frontier}")
    print(f"  congruence_retries: {present.congruence_retries}")
    print("  provenance:")
    for p in present.provenance:
        print(f"    - {p}")

    n_pass = sum(1 for c in results["checks"] if c["pass"])
    n_tot = len(results["checks"])
    verdict = "PASS" if n_pass == n_tot else "FAIL"
    print("\n" + "=" * 70)
    print(f"VERDICT: {verdict}   {n_pass}/{n_tot} checks")
    print("=" * 70)
    return results

if __name__ == "__main__":
    run()
