#!/usr/bin/env python3
import json, os, re, sys, time
from pathlib import Path
from urllib import request, error

BASE = "https://api.sair.foundation/api/public/v1"
API_KEY = os.environ.get("SAIR_API_KEY", "")
if not API_KEY:
    raise SystemExit("SAIR_API_KEY is not set")

ROOT = Path(os.environ.get("ACC_SUBMIT_OUT", "acc_submit/out"))
ROOT.mkdir(parents=True, exist_ok=True)
SUBMISSION_PATH = Path(os.environ.get("ACC_SUBMISSION_FILE", "acc_submit/v1_verified_submission.txt"))

def save(name, obj):
    p = ROOT / name
    if isinstance(obj, (dict, list)):
        p.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        p.write_text(str(obj), encoding="utf-8")
    return p

def api(method, path, body=None):
    url = BASE + path
    headers = {"Authorization": f"Bearer {API_KEY}"}
    data = None
    if body is not None:
        data = json.dumps(body, separators=(",", ":")).encode()
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            parsed = json.loads(raw) if raw else {}
            return resp.status, dict(resp.headers.items()), parsed
    except error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"raw": raw}
        return e.code, dict(e.headers.items()), parsed

def get(path):
    status, headers, obj = api("GET", path)
    if not (200 <= status < 300):
        raise RuntimeError(f"GET {path} failed HTTP {status}: {obj}")
    return headers, obj

def data_obj(obj):
    return obj.get("data", obj) if isinstance(obj, dict) else obj

def extract_items(obj):
    d = data_obj(obj)
    if isinstance(d, dict) and isinstance(d.get("items"), list):
        return d["items"]
    if isinstance(d, list):
        return d
    raise RuntimeError(f"snapshot missing data.items; keys={list(d) if isinstance(d,dict) else type(d)}")

def parse_submission(text):
    rows=[]
    pat=re.compile(r"^([A-Za-z0-9_-]+)\s*:\s*(\[.*\])\s*$")
    for ln,line in enumerate(text.splitlines(),1):
        content=line.split("#",1)[0].strip()
        if not content:
            continue
        m=pat.match(content)
        if not m:
            raise ValueError(f"bad submission line {ln}")
        moves=json.loads(m.group(2))
        if not isinstance(moves,list) or not all(type(x) is int for x in moves):
            raise ValueError(f"bad moves line {ln}")
        rows.append((m.group(1), moves, content))
    return rows

LENGTH_KEYS = (
    "shortestMoveCount","currentShortestMoveCount","bestMoveCount","moveCount",
    "currentBestLength","bestLength","shortestLength","solutionLength","length",
    "shortestMoves","currentShortestMoves","bestMoves",
)
NESTED_KEYS=("best","currentBest","shortest","solution","currentSolution","record")
STATUS_KEYS=("status","solutionStatus","state")

def numeric_len(v):
    if type(v) is int:
        return v
    if isinstance(v, list):
        return len(v)
    if isinstance(v, dict):
        for k in LENGTH_KEYS:
            if k in v:
                q=numeric_len(v[k])
                if q is not None:
                    return q
    return None

def live_shortest(item):
    for k in LENGTH_KEYS:
        if k in item:
            q=numeric_len(item[k])
            if q is not None:
                return ("solved", q, k)
    for nk in NESTED_KEYS:
        if isinstance(item.get(nk), dict):
            q=numeric_len(item[nk])
            if q is not None:
                return ("solved", q, nk)
    status=""
    for k in STATUS_KEYS:
        if k in item and item[k] is not None:
            status=str(item[k]).lower()
            break
    solved_flag=item.get("solved")
    if solved_flag is False:
        return ("unsolved", None, "solved=false")
    if any(tok in status for tok in ("unsolved","open","none","no_solution","not_solved")):
        return ("unsolved", None, f"status={status}")
    # Some APIs encode no record as null.
    for k in ("shortestMoveCount","currentShortestMoveCount","bestMoveCount","currentBestLength","bestLength"):
        if k in item and item[k] is None:
            return ("unsolved", None, f"{k}=null")
    return ("unknown", None, "no recognized shortest/status field")

def challenge_id(item):
    for k in ("challengeId","challenge_id","id"):
        if item.get(k):
            return str(item[k])
    return None

# 1. Eligibility and live spec.
_, me = get("/competitions/acc/me")
save("me.json", me)
_, spec = get("/competitions/acc/submission-spec")
save("submission_spec.json", spec)

# 2. Live snapshots.
_, ac = get("/competitions/acc/discoveries/snapshot?problem=ac")
_, sac = get("/competitions/acc/discoveries/snapshot?problem=stable_ac")
save("snapshot_ac_before.json", ac)
save("snapshot_stable_ac_before.json", sac)

snap = {}
for obj,problem in ((ac,"ac"),(sac,"stable_ac")):
    for item in extract_items(obj):
        cid=challenge_id(item)
        if cid:
            snap[cid]=(problem,item)

source_text = SUBMISSION_PATH.read_text(encoding="utf-8")
rows = parse_submission(source_text)
comparison=[]
selected=[]

for cid,moves,line in rows:
    if cid not in snap:
        comparison.append({"challenge_id":cid,"ours":len(moves),"decision":"skip","reason":"missing_from_snapshot"})
        continue
    problem,item=snap[cid]
    state,best,evidence=live_shortest(item)
    rec={"challenge_id":cid,"problem":problem,"ours":len(moves),"live_state":state,"live_best":best,"evidence":evidence}
    if state=="unsolved":
        rec["decision"]="submit"
        rec["reason"]="currently_unsolved"
        selected.append(line)
    elif state=="solved" and len(moves) <= best:
        rec["decision"]="submit"
        rec["reason"]="tie_or_improve"
        selected.append(line)
    elif state=="solved":
        rec["decision"]="skip"
        rec["reason"]="longer_than_live_best"
    else:
        rec["decision"]="skip"
        rec["reason"]="fail_closed_unknown_snapshot_schema"
        rec["snapshot_keys"]=sorted(item.keys())
    comparison.append(rec)

save("comparison.json", comparison)
filtered = "\n".join(selected) + ("\n" if selected else "")
save("filtered_submission.txt", filtered)
summary={
    "candidate_rows":len(rows),
    "selected_rows":len(selected),
    "selected_ac":sum(1 for x in selected if x.startswith("ac-")),
    "selected_stable_ac":sum(1 for x in selected if x.startswith("sac-")),
    "unknown_schema_rows":sum(1 for x in comparison if x["reason"]=="fail_closed_unknown_snapshot_schema"),
    "longer_rows":sum(1 for x in comparison if x["reason"]=="longer_than_live_best"),
    "unsolved_rows":sum(1 for x in comparison if x["reason"]=="currently_unsolved"),
    "tie_or_improve_rows":sum(1 for x in comparison if x["reason"]=="tie_or_improve"),
}
save("pre_submit_summary.json", summary)
print("PRE_SUBMIT", json.dumps(summary, sort_keys=True), flush=True)

if not selected:
    print("NO_COMPETITIVE_ROWS: nothing submitted", flush=True)
    raise SystemExit(0)

# 3. Submit one filtered batch.
payload={"payload":{"text":filtered},"meta":{"description":"MathGraph ACC V1: locally replay-verified, live-frontier filtered"}}
status, headers, submitted = api("POST", "/competitions/acc/submissions", payload)
save("submit_response.json", {"http_status":status,"headers":headers,"body":submitted})
if status != 202:
    raise RuntimeError(f"submission failed HTTP {status}: {submitted}")

d=data_obj(submitted)
sid = d.get("submissionId") if isinstance(d,dict) else None
if not sid:
    raise RuntimeError(f"202 response missing data.submissionId: {submitted}")
save("submission_id.txt", sid+"\n")
print("SUBMISSION_ID", sid, flush=True)

# 4. Poll to terminal state.
final=None
for attempt in range(1, 61):
    st, hdr, obj = api("GET", f"/competitions/acc/submissions/{sid}")
    save(f"poll_{attempt:02d}.json", {"http_status":st,"body":obj})
    if not (200 <= st < 300):
        raise RuntimeError(f"poll failed HTTP {st}: {obj}")
    dd=data_obj(obj)
    state=str(dd.get("status","")).lower() if isinstance(dd,dict) else ""
    print("POLL", attempt, state, flush=True)
    if state in ("complete","completed","failed","error","rejected"):
        final=obj
        break
    retry=hdr.get("Retry-After") or hdr.get("retry-after")
    try:
        sleep_s=max(2,min(20,int(retry))) if retry else 5
    except Exception:
        sleep_s=5
    time.sleep(sleep_s)

if final is None:
    raise RuntimeError("submission did not reach terminal state within poll budget")
save("final_submission.json", final)

fd=data_obj(final)
state=str(fd.get("status","")).lower() if isinstance(fd,dict) else ""
if state not in ("complete","completed"):
    raise RuntimeError(f"submission terminal state is {state}: {final}")

results = fd.get("results",[]) if isinstance(fd,dict) else []
if isinstance(results,list) and results:
    bad=[x for x in results if x.get("ok") is False]
    if bad:
        save("failed_results.json", bad)
        raise RuntimeError(f"{len(bad)} submitted rows failed verification")
    print("VERIFIED_RESULTS", len(results), flush=True)

# 5. Capture post-submit public state and history.
for problem,name in (("ac","ac"),("stable_ac","stable_ac")):
    _, obj = get(f"/competitions/acc/discoveries/snapshot?problem={problem}")
    save(f"snapshot_{name}_after.json", obj)
    _, lb = get(f"/competitions/acc/leaderboard?problem={problem}")
    save(f"leaderboard_{name}_after.json", lb)

_, mine = get("/competitions/acc/submissions/mine")
save("submissions_mine_after.json", mine)

post={
    "submission_id":sid,
    "selected_rows":len(selected),
    "result_rows":len(results) if isinstance(results,list) else None,
    "status":state,
}
save("post_submit_summary.json", post)
print("POST_SUBMIT", json.dumps(post, sort_keys=True), flush=True)
