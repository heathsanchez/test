#!/usr/bin/env python3
import argparse, json, re, sys
from datetime import datetime, timezone
from urllib import request
from pathlib import Path

INV = (0,1,3,2,5,4,7,6,9,8,11,10,13,12)
PUBLIC_BASE = "https://server-9527.sair.foundation"


def parse_line(line):
    m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(\[.*\])\s*$", line.strip())
    if not m:
        return None
    return m.group(1), list(json.loads(m.group(2)))


def inverse_reduce(xs):
    st = []
    for a in xs:
        if st and st[-1] < 14 and a < 14 and INV[st[-1]] == a:
            st.pop()
        else:
            st.append(a)
    return st


def loop_erase(core, initial, moves):
    state = tuple(tuple(w) for w in initial)
    states = [state]
    out = []
    pos = {state: 0}
    for m in moves:
        nxt = core.apply_move(states[-1], m)
        if nxt in pos:
            j = pos[nxt]
            for st in states[j+1:]:
                pos.pop(st, None)
            states = states[:j+1]
            out = out[:j]
        else:
            out.append(m)
            states.append(nxt)
            pos[nxt] = len(out)
    return out


def compress(core, initial, moves):
    cur = list(moves)
    while True:
        nxt = inverse_reduce(cur)
        nxt = loop_erase(core, initial, nxt)
        nxt = inverse_reduce(nxt)
        if len(nxt) == len(cur):
            return nxt
        cur = nxt


def scoring_candidate(row, candidate_len, our_best=None):
    """Publish a new scoring consequence: solve, strict improvement, or new tie.

    A tie is worth reduced ACC score, so it is a valid consequence unless we
    already hold the same or a better certificate for that exact scoring cell.
    """
    if isinstance(our_best, int) and our_best <= candidate_len:
        return False, "already_held_by_us_at_same_or_better_length"
    if row.get("status") == "unsolved":
        return True, "currently_unsolved"
    best = row.get("currentBestLength")
    if isinstance(best, int) and candidate_len < best:
        return True, "strict_improvement"
    if isinstance(best, int) and candidate_len == best:
        return True, "scoring_tie"
    return False, "longer_than_live_best"


def public_snapshot_map(problem):
    url = f"{PUBLIC_BASE}/api/acc/discoveries/snapshot?problem={problem}"
    req = request.Request(url, headers={"User-Agent":"Mozilla/5.0", "Accept":"application/json"})
    with request.urlopen(req, timeout=60) as r:
        obj = json.loads(r.read().decode("utf-8"))
    d = obj.get("data", obj)
    return obj, {x["challengeId"]: x for x in d["items"]}


def first_int(obj, keys):
    if not isinstance(obj, dict):
        return None
    lowered = {str(k).lower(): v for k, v in obj.items()}
    for key in keys:
        v = lowered.get(key.lower())
        if isinstance(v, int) and not isinstance(v, bool):
            return v
    for v in obj.values():
        if isinstance(v, dict):
            got = first_int(v, keys)
            if got is not None:
                return got
    return None


def parse_utc_timestamp(rec):
    if not isinstance(rec, dict):
        return None
    keys = (
        # ACC submission history currently exposes receivedAt/updatedAt.
        "receivedAt", "received_at", "updatedAt", "updated_at",
        "createdAt", "created_at", "submittedAt", "submitted_at",
        "created", "timestamp", "submitted"
    )
    for key in keys:
        v = rec.get(key)
        if not isinstance(v, str) or not v.strip():
            continue
        s = v.strip()
        try:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def quota_state(api, data_obj):
    """Read current server policy and count today's UTC submission batches.

    Fail closed if the current quota cannot be proved. One POST is one batch,
    independent of the number of rows carried in that batch.
    """
    st, _, comp_obj = api("GET", "/competitions/acc")
    if not 200 <= st < 300:
        return {"blocked": True, "reason": f"competition_spec_http_{st}"}
    comp = data_obj(comp_obj)
    daily_limit = first_int(comp, (
        "dailySubmissions", "daily_submissions", "dailySubmissionLimit",
        "daily_submission_limit", "submissionsPerDay", "submissions_per_day"
    ))
    if daily_limit is None:
        # Current pinned ACC policy fallback. The gate remains conservative:
        # history still must be measurable before any POST is allowed.
        daily_limit = 40
        limit_source = "fallback_40"
    else:
        limit_source = "competition_api"

    st, _, mine_obj = api("GET", "/competitions/acc/submissions/mine?limit=100")
    if not 200 <= st < 300:
        return {
            "blocked": True, "reason": f"submissions_mine_http_{st}",
            "daily_limit": daily_limit, "limit_source": limit_source,
        }
    md = data_obj(mine_obj)
    items = md.get("items", []) if isinstance(md, dict) else []
    if not isinstance(items, list):
        return {
            "blocked": True, "reason": "submissions_mine_items_not_list",
            "daily_limit": daily_limit, "limit_source": limit_source,
        }

    # Prefer explicit server counters when exposed.
    used = first_int(md, (
        "dailySubmissionsUsed", "daily_submissions_used", "submissionsUsedToday",
        "submissions_used_today", "usedToday", "used_today"
    ))
    remaining = first_int(md, (
        "dailySubmissionsRemaining", "daily_submissions_remaining",
        "submissionsRemainingToday", "submissions_remaining_today",
        "remainingToday", "remaining_today"
    ))
    source = "server_counter"

    if used is None and remaining is not None:
        used = max(0, daily_limit - remaining)
    if remaining is None and used is not None:
        remaining = max(0, daily_limit - used)

    if used is None:
        if not items:
            used = 0
            remaining = daily_limit
            source = "empty_history"
        else:
            today = datetime.now(timezone.utc).date()
            stamps = [parse_utc_timestamp(x) for x in items]
            if any(x is None for x in stamps):
                return {
                    "blocked": True,
                    "reason": "quota_history_has_unparseable_timestamps",
                    "daily_limit": daily_limit,
                    "limit_source": limit_source,
                    "history_items": len(items),
                }
            used = sum(dt.date() == today for dt in stamps)
            remaining = max(0, daily_limit - used)
            source = "utc_history_count"

    return {
        "blocked": remaining is None or remaining < 1 or used >= daily_limit,
        "reason": "daily_quota_exhausted" if (remaining is not None and remaining < 1) else "ok",
        "daily_limit": daily_limit,
        "used_today": used,
        "remaining": remaining,
        "limit_source": limit_source,
        "usage_source": source,
        "history_items": len(items),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--acc-root", required=True)
    p.add_argument("--glob", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--cycle", type=int, default=0)
    a = p.parse_args()

    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root))
    from solver_v2_gssub import submit_batch, api, data_obj

    acc = Path(a.acc_root)
    sys.path.insert(0, str(acc / "competition/tools"))
    from verifier import core, stable_core

    manifest = json.loads((acc / "competition/tools/verifier/data/manifest.json").read_text())
    limits = manifest["limits"]
    by_id = {c["challenge_id"]: c for c in manifest["challenges"]}

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    files = sorted(Path(".").glob(a.glob))
    raw_candidates = {}
    for fp in files:
        for line in fp.read_text().splitlines():
            parsed = parse_line(line)
            if not parsed:
                continue
            cid, moves = parsed
            if not cid.startswith("ac-"):
                continue
            prev = raw_candidates.get(cid)
            if prev is None or len(moves) < len(prev):
                raw_candidates[cid] = moves

    verified = {}
    compression = []
    for cid, moves in sorted(raw_candidates.items()):
        c = by_id[cid]
        short = compress(core, c["initial_relators"], moves)
        verdict = core.verify(c, short, c["move_spec_version"], limits)
        sid = "sac-" + cid[3:]
        sc = by_id[sid]
        stable = short + [16, 15]
        sv = stable_core.verify(sc, stable, sc["move_spec_version"], limits)
        rec = {
            "challenge_id": cid,
            "raw_length": len(moves),
            "compressed_length": len(short),
            "saved": len(moves) - len(short),
            "ac_ok": bool(verdict.get("ok")),
            "stable_id": sid,
            "stable_length": len(stable),
            "stable_ok": bool(sv.get("ok")),
        }
        compression.append(rec)
        if not verdict.get("ok") or not sv.get("ok"):
            raise RuntimeError(f"compressed candidate failed official verifier: {rec}")
        verified[cid] = (short, sid, stable)

    # Authenticated history is used both to avoid redundant rows and to prove
    # that at least one daily submission batch remains before POSTing.
    st, _, mine_obj = api("GET", "/competitions/acc/submissions/mine?limit=100")
    if not 200 <= st < 300:
        raise RuntimeError(("submissions_mine", st, mine_obj))
    md = data_obj(mine_obj)
    our_best = {}
    for sub in md.get("items", []):
        for rr in sub.get("results", []):
            if not rr.get("ok"):
                continue
            qid = rr.get("challenge_id")
            n = rr.get("length")
            if qid and isinstance(n, int):
                our_best[qid] = min(n, our_best.get(qid, n))

    # First live filter.
    acsnap, ac = public_snapshot_map("ac")
    ssnap, sac = public_snapshot_map("stable_ac")
    (out / "snapshot_ac_pre.json").write_text(json.dumps(acsnap, indent=2, sort_keys=True) + "\n")
    (out / "snapshot_stable_pre.json").write_text(json.dumps(ssnap, indent=2, sort_keys=True) + "\n")

    selected = []
    selection = []
    for cid, (moves, sid, stable) in sorted(verified.items()):
        for qid, path, live in ((cid, moves, ac), (sid, stable, sac)):
            row = live.get(qid)
            if row is None:
                selection.append({"challenge_id": qid, "length": len(path), "selected": False, "reason": "missing_live_row"})
                continue
            ok, reason = scoring_candidate(row, len(path), our_best.get(qid))
            selection.append({
                "challenge_id": qid,
                "length": len(path),
                "live_status": row.get("status"),
                "live_best": row.get("currentBestLength"),
                "selected": ok,
                "reason": reason,
                "gate": "first_live_check",
            })
            if ok:
                selected.append((qid, path))

    # Re-read the live frontier immediately before publication. Any candidate
    # that lost its strict edge in the meantime is dropped without spending a
    # quota unit.
    acsnap2, ac2 = public_snapshot_map("ac")
    ssnap2, sac2 = public_snapshot_map("stable_ac")
    (out / "snapshot_ac_final.json").write_text(json.dumps(acsnap2, indent=2, sort_keys=True) + "\n")
    (out / "snapshot_stable_final.json").write_text(json.dumps(ssnap2, indent=2, sort_keys=True) + "\n")
    final_selected = []
    final_recheck = []
    for qid, path in selected:
        live = ac2 if qid.startswith("ac-") else sac2
        row = live.get(qid)
        if row is None:
            final_recheck.append({"challenge_id": qid, "length": len(path), "selected": False, "reason": "missing_live_row"})
            continue
        ok, reason = scoring_candidate(row, len(path), our_best.get(qid))
        final_recheck.append({
            "challenge_id": qid,
            "length": len(path),
            "live_status": row.get("status"),
            "live_best": row.get("currentBestLength"),
            "selected": ok,
            "reason": reason,
        })
        if ok:
            final_selected.append((qid, path))
    selected = final_selected

    dropped_for_batch_limit = 0
    if len(selected) > 500:
        dropped_for_batch_limit = len(selected) - 500
        selected = selected[:500]

    text = "\n".join(f"{cid}: {json.dumps(m, separators=(',', ':'))}" for cid, m in selected)
    if text:
        text += "\n"
    (out / "submission.txt").write_text(text)
    (out / "selection.json").write_text(json.dumps(selection, indent=2, sort_keys=True) + "\n")
    (out / "final_recheck.json").write_text(json.dumps(final_recheck, indent=2, sort_keys=True) + "\n")
    (out / "compression.json").write_text(json.dumps(compression, indent=2, sort_keys=True) + "\n")

    quota = quota_state(api, data_obj)
    (out / "quota.json").write_text(json.dumps(quota, indent=2, sort_keys=True) + "\n")

    submission_id = None
    terminal = None
    failures = None
    if selected and not quota.get("blocked", True):
        submission_id, response, polls, final = submit_batch(text)
        (out / "submission_response.json").write_text(json.dumps(response, indent=2, sort_keys=True) + "\n")
        (out / "submission_polls.json").write_text(json.dumps(polls, indent=2, sort_keys=True) + "\n")
        (out / "submission_final.json").write_text(json.dumps(final, indent=2, sort_keys=True) + "\n")
        d = final.get("data", final)
        terminal = str(d.get("status", "")).lower() if isinstance(d, dict) else ""
        results = d.get("results", []) if isinstance(d, dict) else []
        failures = sum(1 for x in results if x.get("ok") is False) if isinstance(results, list) else None
        if terminal not in ("complete", "completed"):
            raise RuntimeError(f"submission terminal state {terminal}")
        if failures:
            raise RuntimeError(f"{failures} platform verification failures")

    report = {
        "experiment": "acc-continuous-residual-loop-v5-scoring-quota",
        "cycle": a.cycle,
        "source_files": [str(x) for x in files],
        "raw_ac_candidates": len(raw_candidates),
        "verified_ac_candidates": len(verified),
        "compression_moves_saved": sum(x["saved"] for x in compression),
        "selected_rows": len(selected),
        "selected_ac": sum(cid.startswith("ac-") for cid, _ in selected),
        "selected_stable": sum(cid.startswith("sac-") for cid, _ in selected),
        "selected_scoring_ties": sum(x.get("selected") and x.get("reason") == "scoring_tie" for x in final_recheck),
        "selected_strict_improvements": sum(x.get("selected") and x.get("reason") == "strict_improvement" for x in final_recheck),
        "selected_unsolved": sum(x.get("selected") and x.get("reason") == "currently_unsolved" for x in final_recheck),
        "dropped_for_batch_limit": dropped_for_batch_limit,
        "daily_submission_limit": quota.get("daily_limit"),
        "daily_submissions_used_pre": quota.get("used_today"),
        "daily_submissions_remaining_pre": quota.get("remaining"),
        "quota_blocked": quota.get("blocked", True),
        "quota_reason": quota.get("reason"),
        "quota_usage_source": quota.get("usage_source"),
        "submission_id": submission_id,
        "terminal_status": terminal,
        "failed_rows": failures,
    }
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("CONTINUOUS_AGGREGATE", json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
