#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

PRINCIPAL='Nucleus::ResearchAgent::"crystal"'
RESOURCE='Nucleus::PromotionGate::"nucleus"'

def q(s):
    return json.dumps(str(s), separators=(",", ":"))

def payload(fields):
    ordered=["campaign","residual","candidate","authority","corpus","originEvidence"]
    return "{ " + ", ".join(f"{k}: {q(fields[k])}" for k in ordered) + " }"

def response(ts, action, fields, rid):
    p=payload(fields)
    return (
        f"@{ts} scope(principal: {PRINCIPAL}, resource: {RESOURCE}) "
        f"request_context(input: {p}) "
        f'Nucleus::Action::"{action}"::response('
        f"input: {p}, callerPrincipal: {PRINCIPAL}, callerResource: {RESOURCE}, "
        f'requestId: {q(rid)})'
    )

def request(ts, action, fields, rid):
    p=payload(fields)
    return (
        f"@{ts} scope(principal: {PRINCIPAL}, resource: {RESOURCE}) "
        f"request_context(input: {p}) "
        f'Nucleus::Action::"{action}"::request('
        f"input: {p}, callerPrincipal: {PRINCIPAL}, callerResource: {RESOURCE}, "
        f'requestId: {q(rid)})'
    )

def empty_list(result, key):
    value=result.get(key)
    return isinstance(value,list) and len(value)==0

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--result", required=True)
    ap.add_argument("--test", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--out", required=True)
    args=ap.parse_args()

    result=json.loads(Path(args.result).read_text())
    changes={r["test"]:r for r in result.get("changes",[])}
    if args.test not in changes:
        raise SystemExit(f"target test not present in changes: {args.test}")
    change=changes[args.test]

    candidate=result["candidate_sha"]
    authority=result["base_sha"]
    fields={
        "campaign":"nucleus",
        "residual":args.test,
        "candidate":candidate,
        "authority":authority,
        "corpus":args.corpus,
        "originEvidence":args.evidence,
    }

    residual_observed=change.get("base") in (2,3)
    candidate_derived=(
        residual_observed
        and change.get("candidate") in (0,1)
        and change.get("candidate")==change.get("expected")
        and change.get("candidate")!=change.get("base")
    )

    controls_green=all(empty_list(result,k) for k in (
        "wrong","regressions","errors","false_accepts","false_rejects"
    ))

    counts_complete=(
        isinstance(result.get("native_accept"),int)
        and isinstance(result.get("native_reject"),int)
        and isinstance(result.get("candidate_residual"),int)
        and result["native_accept"]+result["native_reject"]+result["candidate_residual"]==193
    )
    full_reclosure_green=candidate_derived and controls_green and counts_complete

    lines=[]
    t=0
    if residual_observed:
        lines.append(response(t,"ResidualObserved",fields,"auto-residual")); t+=10
    if candidate_derived:
        lines.append(response(t,"CandidateDerived",fields,"auto-candidate")); t+=10
    if controls_green:
        lines.append(response(t,"ControlsGreen",fields,"auto-controls")); t+=10
    if full_reclosure_green:
        lines.append(response(t,"FullReclosureGreen",fields,"auto-reclosure")); t+=10
    else:
        lines.append(response(t,"CandidateRejected",fields,"auto-rejected")); t+=10

    lines.append(request(t,"Admit",fields,"auto-admit"))
    Path(args.out).write_text("\n".join(lines)+"\n")

    summary={
        "schema":"nucleus-dogwood-evidence-to-events-v1",
        "source_result":str(args.result),
        "target_test":args.test,
        "candidate_sha":candidate,
        "authority_sha":authority,
        "residual_observed":residual_observed,
        "candidate_derived":candidate_derived,
        "controls_green":controls_green,
        "counts_complete":counts_complete,
        "full_reclosure_green":full_reclosure_green,
        "events":[line.split('Nucleus::Action::"',1)[1].split('"',1)[0] for line in lines],
    }
    print(json.dumps(summary,sort_keys=True))

if __name__=="__main__":
    main()
