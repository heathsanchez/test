#!/usr/bin/env python3
from pathlib import Path
import collections
import json
import re
import subprocess
import time

root = Path.cwd()
out = root / 'results/developmental-checker-live-v1'
out.mkdir(parents=True, exist_ok=True)

bins = {
    'binary': root / 'baseline/target/release/sokonanoda',
    'trace': root / 'trace/target/release/sokonanoda',
}
cfgs = {
    'binary': root / 'baseline/config.json',
    'trace': root / 'trace/config.json',
}

def status(rc):
    return 'accept' if rc == 0 else ('decline' if rc == 2 else 'reject')

cases = []
for kind, expected in [('good','accept'),('bad','reject')]:
    for p in sorted((root/'arena-tests'/kind).rglob('*.ndjson')):
        cases.append((p, kind, expected))

trace_re = re.compile(r'^\[MGTRACE\]\s+(.*)$')

def parse_event(line):
    m = trace_re.match(line.strip())
    if not m:
        return None
    d = {}
    for tok in m.group(1).split():
        if '=' in tok:
            k,v = tok.split('=',1)
            d[k]=v
    return d

rows=[]
semantic_mismatches=[]
expected_failures=[]
for idx,(p,kind,expected) in enumerate(cases,1):
    rec={'case':str(p.relative_to(root/'arena-tests')),'kind':kind,'expected':expected}
    outputs={}
    for arm in ['binary','trace']:
        t0=time.perf_counter()
        with p.open('rb') as f:
            cp=subprocess.run([str(bins[arm]),str(cfgs[arm])],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        elapsed=time.perf_counter()-t0
        events=[]
        if arm=='trace':
            txt=cp.stderr.decode('utf-8','replace')
            events=[e for e in (parse_event(line) for line in txt.splitlines()) if e]
        outputs[arm]={'rc':cp.returncode,'status':status(cp.returncode),'seconds':elapsed,'events':events}
    rec['binary']=outputs['binary']
    rec['trace']=outputs['trace']
    if outputs['binary']['status'] != outputs['trace']['status']:
        semantic_mismatches.append(rec['case'])
    if outputs['binary']['status'] != expected:
        expected_failures.append({'case':rec['case'],'expected':expected,'got':outputs['binary']['status']})
    rows.append(rec)
    if idx % 25 == 0:
        print(f'checked {idx}/{len(cases)}')

reject_rows=[r for r in rows if r['binary']['status']=='reject']
nonempty=[r for r in reject_rows if r['trace']['events']]

def signature(events):
    xs=[]
    for e in events:
        xs.append((e.get('kind'),e.get('site'),e.get('ok'),e.get('heads_match')))
    return tuple(xs[-24:])

sig_counts=collections.Counter(signature(r['trace']['events']) for r in nonempty)
kind_counts=collections.Counter()
site_counts=collections.Counter()
for r in nonempty:
    for e in r['trace']['events']:
        kind_counts[e.get('kind','?')]+=1
        site_counts[e.get('site','?')]+=1

# Frozen information-value router. This is not a repair-rate claim.
UNIVERSE=8
def routed_size(events):
    kinds={e.get('kind') for e in events}
    if 'resource' in kinds: return 1
    if 'projection' in kinds: return 1
    if 'iota' in kinds: return 2
    if 'defeq' in kinds and 'unfold' in kinds: return 3
    if 'defeq' in kinds: return 4
    if 'unfold' in kinds: return 3
    panic_sites=[e.get('site','') for e in events if e.get('kind')=='panic']
    if panic_sites:
        site=panic_sites[-1]
        if 'inductive.rs' in site: return 1
        if 'infer.rs' in site: return 2
        if 'conv.rs' in site: return 2
        if 'eval.rs' in site: return 3
        if 'level.rs' in site: return 1
        if 'quot.rs' in site: return 1
        if 'parser.rs' in site: return 1
        if 'tc.rs' in site: return 3
    return UNIVERSE

routing=[{'case':r['case'],'binary_candidates':UNIVERSE,'trace_candidates':routed_size(r['trace']['events'])} for r in reject_rows]
mean_trace=sum(x['trace_candidates'] for x in routing)/len(routing) if routing else None

summary={
    'status':'LIVE_TRACE_GATE_V1B',
    'kernel_source':'metalogiclabs/mathgraph-lean-kernel master at workflow execution',
    'cases_total':len(rows),
    'good_cases':sum(r['kind']=='good' for r in rows),
    'bad_cases':sum(r['kind']=='bad' for r in rows),
    'semantic_mismatches_binary_vs_trace':semantic_mismatches,
    'baseline_vs_expected_failures':expected_failures,
    'rejects_total':len(reject_rows),
    'rejects_with_nonempty_structural_trace':len(nonempty),
    'trace_coverage_of_rejects':(len(nonempty)/len(reject_rows) if reject_rows else None),
    'distinct_nonempty_trace_signatures':len(sig_counts),
    'event_kind_counts':dict(kind_counts),
    'event_site_counts':dict(site_counts),
    'routing_diagnostic':{
        'label':'information-value only; not repair evidence',
        'binary_candidate_families':UNIVERSE,
        'mean_trace_candidate_families':mean_trace,
        'narrowing_factor':(UNIVERSE/mean_trace if mean_trace else None),
    },
    'gate_semantic_identity_pass':not semantic_mismatches,
    'gate_expected_correctness_pass':not expected_failures,
}

(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True))
(out/'rows.json').write_text(json.dumps(rows,indent=2,sort_keys=True))
(out/'routing.json').write_text(json.dumps(routing,indent=2,sort_keys=True))
(out/'trace_signatures.json').write_text(json.dumps([
    {'count':n,'signature':[list(x) for x in sig]} for sig,n in sig_counts.most_common()
],indent=2))
print(json.dumps(summary,indent=2,sort_keys=True))

if semantic_mismatches:
    raise SystemExit('FAIL: tracing changed checker verdicts')
if expected_failures:
    raise SystemExit('FAIL: baseline checker not correct on frozen corpus')
