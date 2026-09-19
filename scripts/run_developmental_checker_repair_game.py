#!/usr/bin/env python3
from pathlib import Path
import json, re, shutil, subprocess, time

root = Path.cwd()
out = root / 'results/developmental-checker-repair-v2'
out.mkdir(parents=True, exist_ok=True)

TRACE_PATCH = root / 'scripts/patch_developmental_checker_trace.py'
BASE = root / 'base'
TRACE = root / 'trace'
ARENA = root / 'arena-tests'
CFG = '{"use_stdin":true,"nat_extension":true,"string_extension":true,"unpermitted_axiom_hard_error":false,"unsafe_permit_all_axioms":true,"num_threads":1}\n'

FAMILIES = ['INFER_APP', 'PROJECTION', 'IOTA', 'UNFOLD']
EPISODES = [
    {'id':'F1','family':'INFER_APP','target':'good/tutorial/006_betaReduction.ndjson','module':'infer'},
    {'id':'F2','family':'PROJECTION','target':'good/tutorial/081_And.right.ndjson','module':'infer'},
    {'id':'F3','family':'IOTA','target':'good/tutorial/079_listRecReduction.ndjson','module':'conv'},
    {'id':'F4','family':'UNFOLD','target':'good/tutorial/030_peano3.ndjson','module':'conv'},
]

# Prospectively fixed controller policies.
BINARY_ORDER = FAMILIES[:]
ABLATION_ORDER = {
    'infer':['INFER_APP','PROJECTION','IOTA','UNFOLD'],
    'conv':['IOTA','UNFOLD','INFER_APP','PROJECTION'],
}

def run(bin_path, case_path):
    with case_path.open('rb') as f:
        cp = subprocess.run([str(bin_path), str(bin_path.parent.parent.parent / 'config.json')], stdin=f,
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return cp.returncode, cp.stderr.decode('utf-8','replace')

def status(rc):
    return 'accept' if rc == 0 else ('decline' if rc == 2 else 'reject')

def events(stderr):
    out=[]
    for line in stderr.splitlines():
        if not line.startswith('[MGTRACE] '):
            continue
        d={}
        for tok in line[len('[MGTRACE] '):].split():
            if '=' in tok:
                k,v=tok.split('=',1); d[k]=v
        out.append(d)
    return out

def route_full(ev):
    # Uses only structural trace kind/site, never case/theorem identity.
    sites=[e.get('site','') for e in ev]
    if any(s=='infer.app_arg' for s in sites): return 'INFER_APP'
    if any(s=='infer.proj' for s in sites): return 'PROJECTION'
    if any(s=='conv.recursor' for s in sites): return 'IOTA'
    if any(s=='conv.unfold_pair' for s in sites): return 'UNFOLD'
    return None

def inject_fault(src: Path, family: str):
    if family == 'INFER_APP':
        p=src/'src/infer.rs'; s=p.read_text()
        anchor='eprintln!("[MGTRACE] kind=defeq site=infer.app_arg depth={} ok={}", depth, mg_ok);'
        repl=anchor+'\n                    panic!("MGFAULT_INFER_APP");'
    elif family == 'PROJECTION':
        p=src/'src/infer.rs'; s=p.read_text()
        anchor='eprintln!("[MGTRACE] kind=projection site=infer.proj depth={}", depth);'
        repl=anchor+'\n        panic!("MGFAULT_PROJECTION");'
    elif family == 'IOTA':
        p=src/'src/conv.rs'; s=p.read_text()
        anchor='eprintln!("[MGTRACE] kind=iota site=conv.recursor depth={} heads_match={}", depth, heads_match);'
        repl=anchor+'\n                panic!("MGFAULT_IOTA");'
    elif family == 'UNFOLD':
        p=src/'src/conv.rs'; s=p.read_text()
        anchor='eprintln!("[MGTRACE] kind=unfold site=conv.unfold_pair depth={}", depth);'
        repl=anchor+'\n                        panic!("MGFAULT_UNFOLD");'
    else: raise ValueError(family)
    if anchor not in s:
        raise RuntimeError(f'fault anchor not found for {family}')
    p.write_text(s.replace(anchor,repl,1))

# Baseline and trace arm already reconstructed by workflow.
baseline_bin = BASE/'target/release/sokonanoda'
trace_bin = TRACE/'target/release/sokonanoda'

# Hard semantic baseline gate over full frozen Arena corpus.
full_fail=[]
for kind, expected in [('good','accept'),('bad','reject')]:
    for case in sorted((ARENA/kind).rglob('*.ndjson')):
        rc,_ = run(baseline_bin, case)
        if status(rc)!=expected:
            full_fail.append({'case':str(case.relative_to(ARENA)),'expected':expected,'got':status(rc)})
if full_fail:
    (out/'summary.json').write_text(json.dumps({'status':'BASELINE_GATE_FAIL','failures':full_fail},indent=2))
    raise SystemExit('baseline semantic gate failed')

rows=[]
for ep in EPISODES:
    work = root / f"fault-{ep['id']}"
    if work.exists(): shutil.rmtree(work)
    shutil.copytree(TRACE, work, ignore=shutil.ignore_patterns('target'))
    inject_fault(work, ep['family'])
    (work/'config.json').write_text(CFG)
    subprocess.run(['cargo','build','--release'], cwd=work, check=True,
                   env={**__import__('os').environ,'RUSTFLAGS':'-C target-cpu=native'})
    faulty_bin=work/'target/release/sokonanoda'
    target=ARENA/ep['target']

    # Fault must convert a previously accepted target into reject.
    base_rc,_=run(trace_bin,target)
    fault_rc, fault_err=run(faulty_bin,target)
    ev=events(fault_err)
    routed=route_full(ev)
    if status(base_rc)!='accept' or status(fault_rc)!='reject':
        raise SystemExit(f"fault discriminator failed for {ep['id']}: base={status(base_rc)} fault={status(fault_rc)}")

    policies={
      'BINARY':BINARY_ORDER,
      'TRACE':([routed]+[x for x in FAMILIES if x!=routed]) if routed else BINARY_ORDER,
      'TRACE_ABLATION':ABLATION_ORDER[ep['module']],
    }
    arm_results={}
    for arm,order in policies.items():
        calls=0; attempts=[]; solved=False
        for cand in order:
            calls+=1
            # Candidate repair family is applied blindly. Only the matching family removes
            # the injected defect; wrong-family repairs leave the defective checker unchanged.
            checker = trace_bin if cand==ep['family'] else faulty_bin
            rc,_=run(checker,target)
            ok=(status(rc)=='accept')
            attempts.append({'candidate':cand,'verdict':status(rc)})
            if ok:
                solved=True; break
        arm_results[arm]={'verifier_calls':calls,'solved':solved,'attempts':attempts}

    rows.append({
      **ep,
      'fault_trace_events':ev[-32:],
      'full_trace_route':routed,
      'arms':arm_results,
    })

summary={
  'status':'LIVE_CONTROLLED_REPAIR_GAME',
  'scope':'controlled fault injection; actual checker compilation + Arena verifier calls',
  'episodes':len(rows),
  'baseline_full_corpus_gate_pass':True,
  'rows':rows,
}
for arm in ['BINARY','TRACE','TRACE_ABLATION']:
    vals=[r['arms'][arm]['verifier_calls'] for r in rows]
    summary[arm.lower()]={
      'repair_rate':sum(r['arms'][arm]['solved'] for r in rows)/len(rows),
      'mean_verifier_calls':sum(vals)/len(vals),
      'calls':vals,
    }
summary['trace_vs_binary_call_reduction_factor']=summary['binary']['mean_verifier_calls']/summary['trace']['mean_verifier_calls']
summary['trace_vs_ablation_call_reduction_factor']=summary['trace_ablation']['mean_verifier_calls']/summary['trace']['mean_verifier_calls']
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True))
print(json.dumps(summary,indent=2,sort_keys=True))

if summary['trace']['repair_rate'] != 1.0 or summary['binary']['repair_rate'] != 1.0 or summary['trace_ablation']['repair_rate'] != 1.0:
    raise SystemExit('repair-rate gate failed')
