#!/usr/bin/env python3
from pathlib import Path
import re

src=Path('scripts/run_developmental_checker_span_v9.py')
s=src.read_text()
s=s.replace("results/developmental-checker-repair-v8","results/developmental-checker-repair-v9")
s=s.replace("FAMILIES=['IOTA','UNFOLD','PROJECTION']","FAMILIES=['EVAL','PROJECTION']")
s=s.replace("EXCLUDE={'good/tutorial/081_And.right.ndjson','good/tutorial/084_PSigma.snd.ndjson','good/perf/app-lam.ndjson'}",
            "EXCLUDE={'good/tutorial/081_And.right.ndjson','good/tutorial/084_PSigma.snd.ndjson','good/perf/app-lam.ndjson','good/perf/grind-ring-5.ndjson','good/undecidability/alg-conv-trans-acc-right.ndjson'}")
# We are patching source code of a Python runner whose embedded Rust string uses literal \\n sequences.
old=r'''        let declared = self.eval(0, empty_env, d.info().ty);\n        let mg_decl_ok = self.def_eq_at(0, val_ty, declared);'''
new=r'''        let declared = self.eval(0, empty_env, d.info().ty);\n        eprintln!("[MGTRACE] kind=eval site=infer.declared_type depth=0 value={:p}", declared);\n        let mg_decl_ok = self.def_eq_at(0, val_ty, declared);'''
if old not in s: raise SystemExit('declared-type eval anchor missing')
s=s.replace(old,new,1)
pat=re.compile(r'def mechanism\(e\):\n.*?\n(?=def route_nearest_mechanism)',re.S)
new_mech='''def mechanism(e):
    k=e.get('kind'); site=e.get('site','')
    if k=='eval' and site=='infer.declared_type': return 'EVAL'
    if k in ('projection','projection_result') and site=='infer.proj': return 'PROJECTION'
    return None

'''
s,n=pat.subn(new_mech,s,count=1)
if n!=1: raise SystemExit(f'mechanism replacement count={n}')
s=s.replace("'LIVE_PRODUCER_SPAN_V8'","'LIVE_PRODUCER_SPAN_V9'")
s=s.replace("post-producer semantic distractors","post-producer declared-type eval distractors")
s=s.replace("IOTA/unfold distractor","declared-type eval distractor")
s=src.write_text(s)
print('patched V9 runner for real downstream declared-type eval')
