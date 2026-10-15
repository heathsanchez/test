#!/usr/bin/env python3
from pathlib import Path

p = Path('scripts/run_developmental_checker_repair_game.py')
s = p.read_text()
old = '''def route_full(ev):
    # Uses only structural trace kind/site, never case/theorem identity.
    sites=[e.get('site','') for e in ev]
    if any(s=='infer.app_arg' for s in sites): return 'INFER_APP'
    if any(s=='infer.proj' for s in sites): return 'PROJECTION'
    if any(s=='conv.recursor' for s in sites): return 'IOTA'
    if any(s=='conv.unfold_pair' for s in sites): return 'UNFOLD'
    return None
'''
new = '''def route_full(ev):
    # V2B precommit: trace history is not causal attribution. Route on the
    # terminal recognized structural event immediately preceding panic.
    # Uses no theorem/case identity and no raw expression content.
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
if old not in s:
    raise SystemExit('V2 route block not found')
s=s.replace(old,new,1)
s=s.replace("'status':'LIVE_CONTROLLED_REPAIR_GAME'", "'status':'LIVE_CONTROLLED_REPAIR_GAME_V2B_TERMINAL'", 1)
p.write_text(s)
print('applied frozen V2B terminal-residual router')
