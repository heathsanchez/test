#!/usr/bin/env python3
from pathlib import Path
import collections, json, re, subprocess

root=Path.cwd()
out=root/'results/developmental-checker-native-control-v3'
out.mkdir(parents=True,exist_ok=True)
ARENA=root/'arena-tests'
bins={'native':root/'base/target/release/sokonanoda','trace':root/'trace/target/release/sokonanoda'}
cfgs={'native':root/'base/config.json','trace':root/'trace/config.json'}

panic_loc_re=re.compile(r'panicked at (src/[^:\n]+\.rs:\d+:\d+)')
trace_re=re.compile(r'^\[MGTRACE\]\s+(.*)$')

def run(arm,p):
    with p.open('rb') as f:
        cp=subprocess.run([str(bins[arm]),str(cfgs[arm])],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    return cp.returncode,cp.stderr.decode('utf-8','replace')

def parse_trace(txt):
    ev=[]
    for line in txt.splitlines():
        m=trace_re.match(line.strip())
        if not m: continue
        d={}
        for tok in m.group(1).split():
            if '=' in tok:
                k,v=tok.split('=',1); d[k]=v
        ev.append(d)
    return ev

def module(site):
    if not site: return None
    if site.startswith('src/'):
        return site.split('/')[1].split('.')[0]
    if site.startswith('infer.'): return 'infer'
    if site.startswith('conv.'): return 'conv'
    return site.split('.')[0]

rows=[]
for p in sorted((ARENA/'bad').rglob('*.ndjson')):
    nrc,nerr=run('native',p)
    trc,terr=run('trace',p)
    if nrc==0 or trc==0 or nrc!=trc:
        raise SystemExit(f'verdict gate failed: {p} native={nrc} trace={trc}')
    locs=panic_loc_re.findall(nerr)
    native_loc=next((x for x in reversed(locs) if 'src/tc.rs' not in x), None)
    ev=parse_trace(terr)
    trace_panic=next((e.get('site') for e in reversed(ev) if e.get('kind')=='panic' and 'src/tc.rs' not in e.get('site','')),None)
    terminal=next((e for e in reversed(ev) if e.get('kind')!='panic'),None)
    rows.append({
      'case':str(p.relative_to(ARENA)),
      'native_location':native_loc,
      'native_module':module(native_loc),
      'trace_panic_location':trace_panic,
      'trace_panic_module':module(trace_panic),
      'terminal_structural_kind':terminal.get('kind') if terminal else None,
      'terminal_structural_site':terminal.get('site') if terminal else None,
      'terminal_structural_module':module(terminal.get('site')) if terminal else None,
      'native_equals_trace_panic':native_loc==trace_panic,
    })

n=len(rows)
native_cov=sum(bool(r['native_location']) for r in rows)
trace_cov=sum(bool(r['trace_panic_location']) for r in rows)
both=[r for r in rows if r['native_location'] and r['trace_panic_location']]
summary={
 'status':'NATURAL_REJECT_NATIVE_STDERR_CONTROL_V3',
 'rejects':n,
 'native_panic_location_coverage':native_cov/n,
 'structured_panic_location_coverage':trace_cov/n,
 'native_and_structured_location_exact_agreement':sum(r['native_equals_trace_panic'] for r in both)/len(both) if both else None,
 'native_distinct_failure_locations':len(set(r['native_location'] for r in rows if r['native_location'])),
 'structured_distinct_failure_locations':len(set(r['trace_panic_location'] for r in rows if r['trace_panic_location'])),
 'terminal_structural_coverage':sum(bool(r['terminal_structural_site']) for r in rows)/n,
 'terminal_module_matches_native_failure_module':sum(r['terminal_structural_module']==r['native_module'] for r in rows if r['native_module'])/sum(bool(r['native_module']) for r in rows),
 'native_module_counts':dict(collections.Counter(r['native_module'] for r in rows)),
 'terminal_kind_counts':dict(collections.Counter(r['terminal_structural_kind'] for r in rows)),
}
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True))
(out/'rows.json').write_text(json.dumps(rows,indent=2,sort_keys=True))
print(json.dumps(summary,indent=2,sort_keys=True))
