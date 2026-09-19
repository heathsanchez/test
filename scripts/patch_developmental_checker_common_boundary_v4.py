#!/usr/bin/env python3
from pathlib import Path

p=Path('scripts/run_developmental_checker_repair_game.py')
s=p.read_text()

old='''def route_full(ev):
    # Uses only structural trace kind/site, never case/theorem identity.
    sites=[e.get('site','') for e in ev]
    if any(s=='infer.app_arg' for s in sites): return 'INFER_APP'
    if any(s=='infer.proj' for s in sites): return 'PROJECTION'
    if any(s=='conv.recursor' for s in sites): return 'IOTA'
    if any(s=='conv.unfold_pair' for s in sites): return 'UNFOLD'
    return None
'''
new='''def route_full(ev):
    # V4: use the terminal recognized structural event before the common trap.
    for e in reversed(ev):
        if e.get('kind') == 'panic':
            continue
        site=e.get('site','')
        if site=='infer.app_arg': return 'INFER_APP'
        if site=='infer.proj': return 'PROJECTION'
        if site=='conv.recursor': return 'IOTA'
        if site=='conv.unfold_pair': return 'UNFOLD'
    return None
'''
if old not in s: raise SystemExit('route block not found')
s=s.replace(old,new,1)

needle="def inject_fault(src: Path, family: str):\n"
insert=needle+'''    # All faults terminate through one identical panic site/message. Native stderr
    # therefore cannot identify which subsystem set up the failure.
    tc=src/'src/tc.rs'
    ts=tc.read_text()
    ta='const CHUNK_SIZE: usize = 64;'
    helper=''' + "'''\n\n#[inline(never)]\npub(crate) fn mg_fault_trap() {\n    panic!(\"MGFAULT\");\n}\n'''" + '''
    if 'fn mg_fault_trap()' not in ts:
        if ta not in ts: raise RuntimeError('tc helper anchor not found')
        tc.write_text(ts.replace(ta,ta+helper,1))
'''
if needle not in s: raise SystemExit('inject_fault anchor not found')
s=s.replace(needle,insert,1)

for oldpanic in [
    'panic!("MGFAULT_INFER_APP");',
    'panic!("MGFAULT_PROJECTION");',
    'panic!("MGFAULT_IOTA");',
    'panic!("MGFAULT_UNFOLD");',
]:
    if oldpanic not in s: raise SystemExit(f'fault panic not found: {oldpanic}')
    s=s.replace(oldpanic,'crate::tc::mg_fault_trap();',1)

oldline="    fault_rc, fault_err=run(faulty_bin,target)\n    ev=events(fault_err)\n"
newline="    fault_rc, fault_err=run(faulty_bin,target)\n    native_locs=re.findall(r'panicked at (src/[^:\\n]+\\.rs:\\d+:\\d+)', fault_err)\n    native_loc=next((x for x in reversed(native_locs) if 'src/tc.rs:161:' not in x), None)\n    ev=events(fault_err)\n"
if oldline not in s: raise SystemExit('fault stderr anchor not found')
s=s.replace(oldline,newline,1)

oldpol="      'BINARY':BINARY_ORDER,\n      'TRACE':([routed]+[x for x in FAMILIES if x!=routed]) if routed else BINARY_ORDER,\n"
newpol="      'BINARY':BINARY_ORDER,\n      'NATIVE_STDERR':BINARY_ORDER,\n      'TRACE':([routed]+[x for x in FAMILIES if x!=routed]) if routed else BINARY_ORDER,\n"
if oldpol not in s: raise SystemExit('policy anchor not found')
s=s.replace(oldpol,newpol,1)

oldrow="      'full_trace_route':routed,\n      'arms':arm_results,\n"
newrow="      'full_trace_route':routed,\n      'native_panic_location':native_loc,\n      'arms':arm_results,\n"
if oldrow not in s: raise SystemExit('row anchor not found')
s=s.replace(oldrow,newrow,1)

s=s.replace("'status':'LIVE_CONTROLLED_REPAIR_GAME'", "'status':'LIVE_COMMON_BOUNDARY_REPAIR_GAME_V4'", 1)
s=s.replace("for arm in ['BINARY','TRACE','TRACE_ABLATION']:", "for arm in ['BINARY','NATIVE_STDERR','TRACE','TRACE_ABLATION']:", 1)
oldmetric="summary['trace_vs_binary_call_reduction_factor']=summary['binary']['mean_verifier_calls']/summary['trace']['mean_verifier_calls']\n"
newmetric=oldmetric+"summary['trace_vs_native_stderr_call_reduction_factor']=summary['native_stderr']['mean_verifier_calls']/summary['trace']['mean_verifier_calls']\nsummary['native_panic_locations']=sorted(set(r['native_panic_location'] for r in rows))\n"
if oldmetric not in s: raise SystemExit('metric anchor not found')
s=s.replace(oldmetric,newmetric,1)
oldgate="if summary['trace']['repair_rate'] != 1.0 or summary['binary']['repair_rate'] != 1.0 or summary['trace_ablation']['repair_rate'] != 1.0:\n"
newgate="if len(summary['native_panic_locations']) != 1:\n    raise SystemExit(f\"common native boundary gate failed: {summary['native_panic_locations']}\")\nif summary['trace']['repair_rate'] != 1.0 or summary['binary']['repair_rate'] != 1.0 or summary['native_stderr']['repair_rate'] != 1.0 or summary['trace_ablation']['repair_rate'] != 1.0:\n"
if oldgate not in s: raise SystemExit('gate anchor not found')
s=s.replace(oldgate,newgate,1)

p.write_text(s)
print('applied frozen V4 common-boundary repair protocol')
