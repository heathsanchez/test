#!/usr/bin/env python3
"""Consequence-governed controller for Andrews-Curtis development.

Implements the Minimal Developmental Algorithm as a conservative transition gate:
construct -> verify -> type residual -> retain/contract/UNKNOWN -> only authorize
repair-frontier construction when separate completeness and non-resolution authority
already exist in the supplied evidence.

This controller never promotes its own proposal. It only emits the transition that
is licensed by external/verifier-backed evidence.
"""
import argparse
import json
from pathlib import Path
from collections import Counter


def load(path, default=None):
    if not path:
        return default
    p = Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text())


def save(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def evidence_signature(row):
    """Existing observables only; no invented representation features."""
    out = []
    for e in row.get("evidence", []):
        out.append({
            "capability": e.get("capability"),
            "verified": bool(e.get("verified")),
            "quotient_found": bool(e.get("quotient_found")),
            "compile_code": e.get("compile_code"),
            "length": e.get("length"),
            "nodes": e.get("nodes"),
            "max_nodes": e.get("max_nodes"),
            "saturated": bool(
                isinstance(e.get("nodes"), int)
                and isinstance(e.get("max_nodes"), int)
                and e["nodes"] >= e["max_nodes"]
            ),
        })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--typed-results", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--fresh-wins")
    ap.add_argument("--protected-wins")
    ap.add_argument("--protected-mechanisms")
    ap.add_argument("--authority-label", default="official ACC verifier + frozen/live leaderboard consequence")
    args = ap.parse_args()

    report = load(args.report, {}) or {}
    rows = load(args.typed_results, []) or []
    protected_wins = load(args.protected_wins, []) or []
    protected_mechanisms = load(args.protected_mechanisms, []) or []
    fresh_wins = load(args.fresh_wins, None)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    caps = report.get("declared_capabilities", [])
    portfolio_complete = bool(report.get("declared_portfolio_complete"))
    expressive_inadequacy = bool(report.get("expressive_inadequacy_certified"))
    growth_authorized = bool(report.get("growth_authorized"))
    frozen_strict = report.get("strict_verified_wins", []) or []
    # Fresh live consequence supersedes the frozen strict comparison when supplied.
    strict = fresh_wins if isinstance(fresh_wins, list) else frozen_strict

    typed = Counter(r.get("typed_result", "UNCLASSIFIED") for r in rows)

    protected = []
    for x in protected_wins:
        protected.append(x if isinstance(x, dict) else {"challenge_id": str(x)})
    for w in strict:
        protected.append({
            "challenge_id": w.get("challenge_id"),
            "candidate_length": w.get("candidate_length"),
            "live_best": w.get("fresh_live_best", w.get("live_best")),
            "margin": w.get("fresh_margin", w.get("margin")),
            "authority": "verified strict record witness under fresh leaderboard consequence",
        })

    retained = []
    for x in protected_mechanisms:
        retained.append(x if isinstance(x, dict) else {"mechanism": str(x)})

    if strict:
        transition = "RETAIN_VERIFIED_WINS"
        next_action = "Retain verifier-clean strict witnesses and provenance; continue resolving with the unchanged present before any growth."
        permission = "NO_EXPANSION_LICENSE"
    elif not portfolio_complete:
        transition = "UNKNOWN_SEARCH"
        next_action = "Complete or repair the declared search qualification. Do not infer capability inadequacy and do not add a mechanism."
        permission = "NO_EXPANSION_LICENSE"
    elif not expressive_inadequacy or not growth_authorized:
        transition = "UNKNOWN_SEARCH"
        next_action = "The declared bounded portfolio is exhausted, but expressive inadequacy is not certified. Preserve the residual; continue only inside admitted means or strengthen the completeness/non-resolution proof."
        permission = "NO_EXPANSION_LICENSE"
    else:
        transition = "REPAIR_FRONTIER_AUTHORIZED"
        next_action = "Construct the smallest reachable repair frontier that removes the certified residual while replaying all protected consequences. If multiple minima survive, freeze them and let independent future consequence select; do not choose by taste."
        permission = "REPAIR_FRONTIER_ONLY"

    contrast = []
    for r in rows:
        contrast.append({
            "challenge_id": r.get("challenge_id"),
            "typed_result": r.get("typed_result"),
            "live_best": r.get("live_best"),
            "best_verified_length": r.get("best_verified_length"),
            "best_capability": r.get("best_capability"),
            "evidence_signature": evidence_signature(r),
        })

    strict_ids = {w.get("challenge_id") for w in strict}
    winners = [x for x in contrast if x["challenge_id"] in strict_ids]
    others = [x for x in contrast if x["challenge_id"] not in strict_ids]
    separators = []
    if winners and others:
        def flat(row):
            es = row["evidence_signature"]
            return {
                "any_verified": any(e["verified"] for e in es),
                "any_quotient": any(e["quotient_found"] for e in es),
                "any_saturated": any(e["saturated"] for e in es),
                "best_capability": row.get("best_capability"),
            }
        wf = [flat(x) for x in winners]
        of = [flat(x) for x in others]
        for k in ["any_verified", "any_quotient", "any_saturated", "best_capability"]:
            wvals = {x[k] for x in wf}
            ovals = {x[k] for x in of}
            if wvals.isdisjoint(ovals):
                separators.append({
                    "observable": k,
                    "winner_values": sorted(map(str, wvals)),
                    "other_values": sorted(map(str, ovals)),
                    "status": "observed separator only; not yet a licensed representation repair",
                })

    state = {
        "controller": "RESOLVE_ACC_V1",
        "source_algorithm": "Minimal Developmental Algorithm 2026-09-13",
        "authority": args.authority_label,
        "S_t": {
            "declared_capabilities": caps,
            "retained_mechanisms": retained,
        },
        "P_t": protected,
        "result_counts": dict(typed),
        "portfolio_complete": portfolio_complete,
        "expressive_inadequacy_certified": expressive_inadequacy,
        "growth_authorized_by_input_evidence": growth_authorized,
        "transition": transition,
        "permission": permission,
        "next_action": next_action,
        "frozen_strict_verified_wins": frozen_strict,
        "fresh_strict_verified_wins": strict,
        "candidate_existing_observable_separators": separators,
        "laws": [
            "construct cheapest decisive witness available in the present",
            "independent verification supplies authority",
            "search failure is not expressive inadequacy",
            "preserve prior protected consequences",
            "make only the smallest licensed change",
            "future consequence selects among multiple lawful minima",
            "contract only proven redundancy",
        ],
    }

    save(out / "developmental_state.json", state)
    save(out / "consequence_contrasts.json", contrast)
    save(out / "next_action.json", {
        "transition": transition,
        "permission": permission,
        "next_action": next_action,
    })
    print("RESOLVE_ACC", json.dumps(state, sort_keys=True))


if __name__ == "__main__":
    main()
