#!/usr/bin/env python3
"""V22 — verifier-induced witness type formation.

Question:
    Can the witness type used by V21 be induced from verifier-visible
    substitutability behavior rather than supplied as Theta_same/Theta_other?

No witness type labels are available to the learner.  Each opaque witness
mechanism can be inserted into a frozen finite family of developmental contexts.
The verifier returns exact behavioral outcomes.  The learner constructs the
coarsest quotient induced by equality in every declared substitution context,
then synthesizes a policy over the induced quotient classes.

The hidden semantic labels are used only for the final audit.  A held-out
positive mechanism contributes no action-labeled positive episode during
training; its class membership must be recovered from its verifier behavior.

Boundary: finite supplied substitution-context carrier, exact verifier, finite
policy grammar, and finite episode corpus.  V22 does not discover the adequacy
map or the context family itself.
"""
from __future__ import annotations
import argparse, itertools, json
from dataclasses import dataclass
from pathlib import Path

SAME_FRAME = "SAME_FRAME_REPAIR"
EXPAND = "EXPAND_CARRIER"
REJECT = "REJECT"

# Frozen developmental substitution contexts.  Names are not semantic type labels;
# they identify verifier experiments whose outcomes define substitutability.
CONTEXTS = ("CLOSE", "PRESERVE", "COMPOSE", "ABLATE", "RETAIN")

@dataclass(frozen=True)
class Mechanism:
    mid: str
    # Hidden oracle profile. The learner may query each coordinate only through
    # verifier_context(mid, ctx), never through a supplied type label.
    profile: tuple[int, ...]
    hidden_type: str

@dataclass(frozen=True)
class Episode:
    name: str
    mechanism: str
    nuisance: tuple[int, int, int]
    causal_ok: bool = True
    preserve_ok: bool = True
    action: str = EXPAND

# Four positive mechanisms are genuinely substitutable in all declared contexts.
# Five adversarial decoys differ from that class in exactly one context each,
# making every context necessary to recover the full quotient.  Two additional
# mechanisms share a non-target class to show that quotienting is not merely
# separating positives from negatives.
MECHANISMS = {
    "m_local":    Mechanism("m_local",    (1,1,1,1,1), "T_same"),
    "m_cover":    Mechanism("m_cover",    (1,1,1,1,1), "T_same"),
    "m_symbolic": Mechanism("m_symbolic", (1,1,1,1,1), "T_same"),
    "m_alt":      Mechanism("m_alt",      (1,1,1,1,1), "T_same"),
    "d_close":    Mechanism("d_close",    (0,1,1,1,1), "T_d_close"),
    "d_preserve": Mechanism("d_preserve",(1,0,1,1,1), "T_d_preserve"),
    "d_compose":  Mechanism("d_compose", (1,1,0,1,1), "T_d_compose"),
    "d_ablate":   Mechanism("d_ablate",  (1,1,1,0,1), "T_d_ablate"),
    "d_retain":   Mechanism("d_retain",  (1,1,1,1,0), "T_d_retain"),
    "m_other_a":  Mechanism("m_other_a",  (0,0,1,0,1), "T_other_shared"),
    "m_other_b":  Mechanism("m_other_b",  (0,0,1,0,1), "T_other_shared"),
}
POSITIVE_MECHS = ("m_local", "m_cover", "m_symbolic", "m_alt")


def verifier_context(mid: str, ctx: str) -> int:
    """Exact verifier-visible substitution result for one context."""
    m = MECHANISMS[mid]
    return m.profile[CONTEXTS.index(ctx)]


def semantic_profile(mid: str, contexts=CONTEXTS) -> tuple[int, ...]:
    return tuple(verifier_context(mid, c) for c in contexts)


def partition_for(contexts=CONTEXTS):
    groups = {}
    for mid in sorted(MECHANISMS):
        groups.setdefault(semantic_profile(mid, contexts), []).append(mid)
    # Canonical quotient class IDs depend only on the behavioral signature.
    keys = sorted(groups)
    class_of = {}
    classes = []
    for i, sig in enumerate(keys):
        cid = f"Q{i}"
        members = tuple(sorted(groups[sig]))
        classes.append({"class": cid, "signature": sig, "members": members})
        for m in members:
            class_of[m] = cid
    return class_of, classes


def same_partition(a, b):
    mids = sorted(MECHANISMS)
    return all((a[x] == a[y]) == (b[x] == b[y]) for x in mids for y in mids)


def minimum_context_bases():
    full, _ = partition_for(CONTEXTS)
    good = []
    for r in range(1, len(CONTEXTS)+1):
        for sub in itertools.combinations(CONTEXTS, r):
            p, _ = partition_for(sub)
            if same_partition(p, full):
                good.append(sub)
        if good:
            break
    return good


def corpus():
    eps = []
    # Pair nuisance values across positive/negative families to prevent trivial
    # surface summaries from identifying the induced type.
    nuisances = [(0,0,0),(0,1,1),(1,0,1),(1,1,0)]
    for i, m in enumerate(POSITIVE_MECHS):
        eps.append(Episode(f"{m}_positive", m, nuisances[i], action=SAME_FRAME))
    decoys = ["d_close","d_preserve","d_compose","d_ablate","d_retain","m_other_a","m_other_b"]
    for i, m in enumerate(decoys):
        eps.append(Episode(f"{m}_negative", m, nuisances[i % len(nuisances)], action=EXPAND))
    # Hostile controls: even a target-class witness cannot bypass independent
    # causal/preservation obligations.
    eps.append(Episode("hostile_noncausal", "m_local", (0,0,0), causal_ok=False, action=REJECT))
    eps.append(Episode("hostile_preservation", "m_cover", (0,1,1), preserve_ok=False, action=REJECT))
    return eps


def exact_action_verifier(e: Episode, proposed: str):
    m = MECHANISMS[e.mechanism]
    viable_same = (m.hidden_type == "T_same")
    if not e.causal_ok or not e.preserve_ok:
        admissible = []
    elif viable_same:
        admissible = [SAME_FRAME]
    else:
        admissible = [EXPAND]
    return proposed in admissible, admissible

# Policy language over induced quotient classes.  Importantly, policy candidates
# refer only to canonical quotient IDs, never to hidden type labels or mechanism names.
def synthesize_policy(train, class_of, classes):
    accepted = [e for e in train if e.action in (SAME_FRAME, EXPAND)]
    checked = 0
    # Size-1 programs: exists witness in quotient class Qk -> SAME else EXPAND.
    for cls in classes:
        checked += 1
        cid = cls["class"]
        ok = all((SAME_FRAME if class_of[e.mechanism] == cid else EXPAND) == e.action for e in accepted)
        if ok:
            return cid, checked
    return None, checked


def mechanism_holdouts(eps, class_of, classes):
    rows = []
    all_correct = all_verified = True
    for held in POSITIVE_MECHS:
        held_eps = [e for e in eps if e.mechanism == held and e.action == SAME_FRAME]
        train = [e for e in eps if e.action != REJECT and e not in held_eps]
        cid, checked = synthesize_policy(train, class_of, classes)
        preds = []
        for e in held_eps:
            pred = SAME_FRAME if cid is not None and class_of[e.mechanism] == cid else EXPAND
            verified, acts = exact_action_verifier(e, pred)
            preds.append({"episode": e.name, "pred": pred, "truth": e.action,
                          "correct": pred == e.action, "verified": verified,
                          "completecover_actions": acts})
        all_correct &= bool(preds and all(x["correct"] for x in preds))
        all_verified &= bool(preds and all(x["verified"] for x in preds))
        rows.append({
            "heldout_mechanism": held,
            "positive_action_example_absent_from_training": True,
            "induced_class": class_of[held],
            "policy_class": cid,
            "policy_candidates_checked": checked,
            "heldout": preds,
        })
    return rows, all_correct, all_verified


def type_erasure_ablation(eps):
    # Erasing verifier substitution behavior leaves only mechanism IDs + nuisance.
    # Require alpha-invariance to mechanism renaming, so names cannot carry policy.
    # Because nuisance marginals overlap across actions, no invariant classifier exists.
    natural = [e for e in eps if e.action in (SAME_FRAME, EXPAND)]
    nuisance_to_actions = {}
    for e in natural:
        nuisance_to_actions.setdefault(e.nuisance, set()).add(e.action)
    collisions = {str(k): sorted(v) for k,v in nuisance_to_actions.items() if len(v) > 1}
    no_invariant_policy = bool(collisions) and all(
        any(e2.nuisance == e.nuisance and e2.action != e.action for e2 in natural)
        for e in natural
    )
    return {"nuisance_action_collisions": collisions,
            "alpha_invariant_policy_exists": not no_invariant_policy,
            "transfer_collapses": no_invariant_policy}


def hidden_type_audit(class_of):
    mids = sorted(MECHANISMS)
    return all((class_of[a] == class_of[b]) ==
               (MECHANISMS[a].hidden_type == MECHANISMS[b].hidden_type)
               for a in mids for b in mids)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out-dir", required=True); args = ap.parse_args()
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    eps = corpus()
    class_of, classes = partition_for(CONTEXTS)
    bases = minimum_context_bases()
    folds, all_correct, all_verified = mechanism_holdouts(eps, class_of, classes)
    ablation = type_erasure_ablation(eps)

    # Full policy over induced types.
    natural = [e for e in eps if e.action in (SAME_FRAME, EXPAND)]
    policy_class, checked = synthesize_policy(natural, class_of, classes)

    hostile = []
    for e in eps:
        if e.action != REJECT: continue
        pred = SAME_FRAME if policy_class is not None and class_of[e.mechanism] == policy_class else EXPAND
        accepted, acts = exact_action_verifier(e, pred)
        hostile.append({"episode": e.name, "proposed": pred,
                        "verifier_accepts": accepted, "completecover_actions": acts})

    all_contexts_necessary = len(bases) == 1 and set(bases[0]) == set(CONTEXTS)
    gates = {
        "supplied_witness_type_labels_absent_from_learner": True,
        "verifier_induced_substitutability_quotient_constructed": len(classes) > 1,
        "induced_quotient_matches_hidden_semantic_types": hidden_type_audit(class_of),
        "all_declared_substitution_contexts_necessary_for_full_quotient": all_contexts_necessary,
        "minimum_policy_operates_on_induced_quotient_class": policy_class is not None,
        "leave_one_positive_mechanism_out_transfer_100pct": all_correct,
        "all_heldout_actions_completecover_verified": all_verified,
        "type_erasure_breaks_alpha_invariant_transfer": ablation["transfer_collapses"],
        "hostile_causal_and_preservation_controls_rejected": bool(hostile and all(not x["verifier_accepts"] for x in hostile)),
    }
    gates["VERIFIER_INDUCED_WITNESS_TYPE_FORMATION_GATE"] = all(gates.values())

    result = {
        "status": "VERIFIER_INDUCED_WITNESS_TYPE_FORMATION_V22",
        "claim_scope": "finite supplied substitution-context carrier, exact verifier, finite policy grammar/corpus; witness type labels hidden from learner; not automatic adequacy-map/context discovery",
        "definition": "w_i ~_dev w_j iff verifier_context(w_i,c)=verifier_context(w_j,c) for every frozen developmental substitution context c",
        "contexts": CONTEXTS,
        "minimum_context_bases": bases,
        "induced_classes": classes,
        "full_policy": {"form": "exists_verified[induced_class]", "class": policy_class, "checked": checked},
        "mechanism_holdout_folds": folds,
        "type_erasure_ablation": ablation,
        "hostile_controls": hostile,
        "gates": gates,
    }
    (out / "RESULT.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
