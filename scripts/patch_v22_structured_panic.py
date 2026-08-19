#!/usr/bin/env python3
from pathlib import Path
import re
p=Path('scripts/run_developmental_distinction_gold_v22.py')
s=p.read_text()
new="""def native_fault_location(stderr):
    ps=[e.get('site') for e in events(stderr) if e.get('kind')=='panic' and e.get('site')]
    return ps[-1] if ps else None
"""
pat=r"def native_fault_location\(stderr\):\n(?:    .*\n)+?(?=def bucket_count\(n\):)"
m=re.search(pat,s)
if not m:
    raise SystemExit('V22 panic-location function not found')
s=s[:m.start()]+new+'\n'+s[m.end():]
p.write_text(s)
print('patched V22 to structured common panic boundary')
