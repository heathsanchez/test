#!/usr/bin/env python3
from pathlib import Path
p=Path('scripts/run_developmental_distinction_invention_v20.py')
s=p.read_text()
old="""def native_fault_location(stderr):
    xs=re.findall(r'panicked at (src/[^:\\n]+\\.rs:\\d+:\\d+)',stderr)
    return next((x for x in reversed(xs) if 'src/tc.rs' in x),None)
"""
new="""def native_fault_location(stderr):
    ps=[e.get('site') for e in events(stderr) if e.get('kind')=='panic' and e.get('site')]
    return ps[-1] if ps else None
"""
if old not in s: raise SystemExit('V20 panic-location anchor missing')
p.write_text(s.replace(old,new,1))
print('patched V20 to structured common panic boundary')
