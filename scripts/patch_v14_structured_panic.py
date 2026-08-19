#!/usr/bin/env python3
from pathlib import Path
p=Path('scripts/run_developmental_distinction_discovery_v14.py')
s=p.read_text()
old="""def native_fault_location(stderr):\n    xs=re.findall(r'panicked at (src/[^:\\n]+\\.rs:\\d+:\\d+)',stderr)\n    return next((x for x in reversed(xs) if 'src/tc.rs' in x),None)\n"""
new="""def native_fault_location(stderr):\n    # Use the semantics-inert structured panic hook: all injected families must\n    # terminate at exactly the same common trap site.\n    ps=[e.get('site') for e in events(stderr) if e.get('kind')=='panic' and e.get('site')]\n    return ps[-1] if ps else None\n"""
if old not in s: raise SystemExit('V14 panic-location anchor missing')
p.write_text(s.replace(old,new,1))
print('patched V14 to gate on structured common panic boundary')
