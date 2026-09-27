#!/usr/bin/env python3
"""V24 — first contact with raw natural-domain artifacts.

This runner is intentionally fail-loud. It does not manufacture synthetic episodes
when native traces are missing. It inventories checked-out real repositories using
only structural JSON/JSONL information (field names are audit-only), searches for
native repeated record carriers rich enough to support verifier-relative
substitutability, and reports whether the §15 adequacy experiment is actually
runnable from current public artifacts.

A later commit may add the generic adequacy learner only after this audit finds a
sufficient natural carrier. The present evidentiary run must not hand-distill raw
sources to make the gate pass.
"""
from __future__ import annotations
import argparse, json, os
from pathlib import Path
from collections import Counter, defaultdict

TEXT_EXT={'.json','.jsonl','.ndjson'}
IGNORE_PARTS={'.git','node_modules','.venv','venv','__pycache__'}


def scalar(x): return x is None or isinstance(x,(bool,int,float,str))

def flatten_types(x, path=()):
    out=[]
    if scalar(x):
        out.append((path,type(x).__name__,x))
    elif isinstance(x,list):
        out.append((path,'list_len',len(x)))
        for i,v in enumerate(x[:64]): out.extend(flatten_types(v,path+('[]',)))
    elif isinstance(x,dict):
        out.append((path,'dict_arity',len(x)))
        # keys are deliberately erased from learner-side structural features.
        for _,v in sorted(x.items(), key=lambda kv:str(type(kv[1]))):
            out.extend(flatten_types(v,path+('{}',)))
    return out


def record_carriers(x, origin):
    """Yield repeated dict-record lists without using semantic key names."""
    got=[]
    def walk(v, depth=0):
        if depth>10: return
        if isinstance(v,list):
            if len(v)>=2 and sum(isinstance(z,dict) for z in v)>=2:
                rows=[z for z in v if isinstance(z,dict)]
                got.append((origin,rows))
            for z in v[:256]: walk(z,depth+1)
        elif isinstance(v,dict):
            for z in v.values(): walk(z,depth+1)
    walk(x)
    return got


def parse_file(p):
    try:
        if p.suffix=='.json': return json.loads(p.read_text(errors='replace'))
        rows=[]
        for line in p.read_text(errors='replace').splitlines():
            line=line.strip()
            if not line: continue
            try: rows.append(json.loads(line))
            except Exception: pass
        return rows if rows else None
    except Exception:
        return None


def carrier_stats(rows):
    # No field names: only structural scalar/type/count signatures.
    sigs=[]
    for r in rows[:512]:
        fs=flatten_types(r)
        types=Counter(t for _,t,_ in fs)
        bools=sum(isinstance(v,bool) for _,_,v in fs)
        nums=sum(isinstance(v,(int,float)) and not isinstance(v,bool) for _,_,v in fs)
        strings=sum(isinstance(v,str) for _,_,v in fs)
        sigs.append((tuple(sorted(types.items())),bools,nums,strings,len(fs)))
    distinct=len(set(sigs))
    # A minimally useful raw episode carrier has repeated records and nontrivial
    # observed variation. This is readiness, not an adequacy proof.
    return {'records':len(rows),'distinct_structural_signatures':distinct,
            'structurally_nontrivial':len(rows)>=4 and distinct>=2}


def audit_domain(name,root):
    root=Path(root); files=[]; carriers=[]
    if not root.exists():
        return {'domain':name,'root':str(root),'exists':False,'machine_files':0,'carriers':[],
                'eligible_for_adequacy':False,'reason':'SOURCE_ROOT_MISSING'}
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in TEXT_EXT: continue
        if any(q in IGNORE_PARTS for q in p.parts): continue
        if p.stat().st_size>20_000_000: continue
        obj=parse_file(p)
        if obj is None: continue
        files.append(str(p.relative_to(root)))
        for origin,rows in record_carriers(obj,str(p.relative_to(root))):
            s=carrier_stats(rows); s['origin']=origin; carriers.append(s)
    good=[c for c in carriers if c['structurally_nontrivial']]
    # This deliberately does NOT claim adequacy merely from structural records.
    # We also require raw intervention/verifier consequences to be identifiable
    # without semantic field-name adapters. Current audit has no lawful generic
    # way to designate them, so the stronger eligibility remains false until
    # the raw source exposes executable/typed consequence structure.
    return {'domain':name,'root':str(root),'exists':True,'machine_files':len(files),
            'sample_machine_files':files[:25],'carriers':sorted(carriers,key=lambda x:-x['records'])[:20],
            'structural_carrier_found':bool(good),
            'native_intervention_verifier_interface_found':False,
            'eligible_for_adequacy':False,
            'reason':('RAW_RECORDS_FOUND_BUT_NO_DOMAIN_AGNOSTIC_NATIVE_INTERVENTION_VERIFIER_INTERFACE'
                      if good else 'NO_NONTRIVIAL_NATIVE_MACHINE_READABLE_EPISODE_CARRIER')}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',action='append',default=[],help='NAME=PATH')
    ap.add_argument('--out-dir',required=True)
    a=ap.parse_args(); out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    src=[]
    for spec in a.source:
        if '=' not in spec: raise SystemExit('source must be NAME=PATH')
        n,p=spec.split('=',1); src.append((n,p))
    domains=[audit_domain(n,p) for n,p in src]
    eligible=[d for d in domains if d['eligible_for_adequacy']]
    structural=[d for d in domains if d.get('structural_carrier_found')]
    gates={
      'native_raw_artifacts_not_hand_distilled':True,
      'at_least_three_eligible_real_domains':len(eligible)>=3,
      'no_manual_developmental_feature_map':True,
      'field_and_domain_names_absent_from_learner':True,
      'adequacy_induced_by_verifier_substitutability':False,
      'heldout_domain_action_transfer_100pct':False,
      'all_heldout_actions_independently_verified':False,
      'adequacy_ablation_breaks_transfer':False,
      'shuffled_verifier_breaks_structure':False,
      'causal_capability_gain_on_heldout_domain':False,
    }
    gates['RAW_NATURAL_ADEQUACY_GATE']=all(gates.values())
    status=('READY_FOR_RAW_ADEQUACY_INDUCTION' if len(eligible)>=3 else
            'INSUFFICIENT_NATURAL_RAW_TRACE_DOMAINS')
    result={
      'status':status,
      'claim_scope':'raw public repository artifacts only; no hand-distilled replacement episodes; this first-contact run is a readiness/adequacy-boundary audit, not a synthetic substitute',
      'domains_requested':len(domains),
      'domains_with_nontrivial_machine_record_carriers':len(structural),
      'eligible_domains':len(eligible),
      'domains':domains,
      'next_required_object':'domain-agnostic executable/typed intervention-verifier consequence interface derivable from native traces, without hand-authored developmental roles',
      'gates':gates,
    }
    (out/'RESULT.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
