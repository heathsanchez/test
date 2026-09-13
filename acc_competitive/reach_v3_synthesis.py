#!/usr/bin/env python3
import argparse
import glob
import json
from pathlib import Path

GUARDS = ["never", "boundary", "nonboundary", "all"]


def save(p, o):
    Path(p).write_text(json.dumps(o, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def dominates(a, b):
    ok = (
        a["strict_rows_frozen"] >= b["strict_rows_frozen"]
        and a["verified_prospective"] >= b["verified_prospective"]
        and a["total_nodes"] <= b["total_nodes"]
        and a["total_atomic_length_prospective"] <= b["total_atomic_length_prospective"]
    )
    strict = (
        a["strict_rows_frozen"] > b["strict_rows_frozen"]
        or a["verified_prospective"] > b["verified_prospective"]
        or a["total_nodes"] < b["total_nodes"]
        or a["total_atomic_length_prospective"] < b["total_atomic_length_prospective"]
    )
    return ok and strict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", required=True)
    ap.add_argument("--prospective-count", type=int, required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for p in glob.glob(a.glob, recursive=True):
        try:
            x = json.loads(Path(p).read_text())
        except Exception:
            continue
        if x.get("experiment") == "ACC_REACH_V3_BOOLEAN_GUARD":
            rows.append(x)

    expected = len(GUARDS) * (a.prospective_count + 3)
    if len(rows) != expected:
        raise RuntimeError(f"expected {expected} V3 case results, got {len(rows)}")

    reports = {}
    best_paths = {}
    for g in GUARDS:
        rr = [x for x in rows if x["guard"] == g]
        prosp = [x for x in rr if x["role"] == "prospective"]
        replay = [x for x in rr if x["role"] == "protected_replay"]
        if len(prosp) != a.prospective_count or len(replay) != 3:
            raise RuntimeError((g, len(prosp), len(replay)))

        replay_ok = all(
            (r.get("ac_verdict") or {}).get("ok") is True
            and (r.get("stable_verdict") or {}).get("ok") is True
            for r in replay
        )
        strict_ac = sum(bool(r.get("strict_ac_frozen")) for r in prosp)
        strict_stable = sum(bool(r.get("strict_stable_frozen")) for r in prosp)
        verified = sum(
            (r.get("ac_verdict") or {}).get("ok") is True
            and (r.get("stable_verdict") or {}).get("ok") is True
            for r in prosp
        )
        reports[g] = {
            "guard": g,
            "truth_table": next(r["guard_truth_table_false_true"] for r in rr),
            "protected_replay_ok": replay_ok,
            "prospective_targets": len(prosp),
            "verified_prospective": verified,
            "quotient_hits_prospective": sum(r.get("quotient_found") is True for r in prosp),
            "strict_ac_frozen": strict_ac,
            "strict_stable_frozen": strict_stable,
            "strict_rows_frozen": strict_ac + strict_stable,
            "total_nodes": sum(int(r.get("nodes", 0)) for r in rr),
            "total_atomic_length_prospective": sum(
                int(r.get("atomic_length", 0))
                for r in prosp if (r.get("ac_verdict") or {}).get("ok") is True
            ),
            "replay_failures": [
                r["challenge_id"] for r in replay
                if not (
                    (r.get("ac_verdict") or {}).get("ok") is True
                    and (r.get("stable_verdict") or {}).get("ok") is True
                )
            ],
        }

    admissible = [r for r in reports.values() if r["protected_replay_ok"]]
    adequate = [r for r in admissible if r["strict_rows_frozen"] > 0]
    novel_adequate = [r for r in adequate if r["guard"] != "boundary"]

    frontier = []
    for x in admissible:
        if not any(dominates(y, x) for y in admissible if y["guard"] != x["guard"]):
            frontier.append(x)
    frontier.sort(key=lambda r: r["guard"])

    if novel_adequate:
        transition = "REACH_V3_ADEQUATE_CONTINUATION_FOUND"
        permission = "ADMIT_MINIMIZE_COMPILE"
    elif adequate:
        transition = "CURRENT_GUARD_SETTLES_FROZEN_PACK"
        permission = "NO_NOVEL_DEVELOPMENT_REQUIRED"
    else:
        transition = "REACH_V3_OBSTRUCTION_CERTIFIED"
        permission = "RECURSE_ON_REACH_V3_AUTHORIZED"

    strict_target_ids = set()
    for g in adequate:
        for r in rows:
            if r["guard"] != g["guard"] or r["role"] != "prospective":
                continue
            if r.get("strict_ac_frozen") or r.get("strict_stable_frozen"):
                strict_target_ids.add(r["challenge_id"])

    # Recover shortest verified AC certificate text from sibling files.
    candidates = {}
    for p in glob.glob(a.glob, recursive=True):
        base = Path(p).parent
        c = base / "candidate_ac.txt"
        if not c.exists():
            continue
        for line in c.read_text().splitlines():
            if ":" not in line:
                continue
            cid, raw = line.split(":", 1)
            cid = cid.strip()
            if cid not in strict_target_ids:
                continue
            moves = json.loads(raw.strip())
            if cid not in candidates or len(moves) < len(candidates[cid]):
                candidates[cid] = moves

    (out / "best_strict_ac.txt").write_text(
        "".join(
            f"{cid}: {json.dumps(m,separators=(',',':'))}\n"
            for cid, m in sorted(candidates.items())
        ),
        encoding="utf-8",
    )

    summary = [reports[g] | {"pareto_frontier": any(x["guard"] == g for x in frontier)}
               for g in GUARDS]
    report = {
        "experiment": "ACC_REACH_V3_BOOLEAN_GUARD_SYNTHESIS",
        "declared_language": (
            "Complete Boolean one-input transducer language over the existing "
            "boundary-inverse proposal-admission predicate: 4 truth tables."
        ),
        "declared_language_complete": True,
        "candidate_count": 4,
        "admissible_replay_clean": [r["guard"] for r in admissible],
        "adequate_guards": [r["guard"] for r in adequate],
        "novel_adequate_guards": [r["guard"] for r in novel_adequate],
        "pareto_frontier": [r["guard"] for r in frontier],
        "strict_targets_for_fresh_recheck": sorted(strict_target_ids),
        "transition": transition,
        "permission": permission,
        "next_action": (
            "Admit and prospectively compile the replay-clean novel guard(s)."
            if novel_adequate else
            "The complete one-site Boolean guard language is inadequate on the "
            "frozen encounter. Recurse to the next pre-quotient object: proposal "
            "construction itself, not another hand-picked priority or guard."
        ),
        "scope": (
            "Authority is limited to the frozen V3 prospective pack and the "
            "complete four-function Boolean language over the existing boundary "
            "cancellation guard."
        ),
        "unrestricted_search_inadequacy_certified": False,
    }
    save(out / "guard_summary.json", summary)
    save(out / "report.json", report)
    print("REACH_V3_SYNTHESIS", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
