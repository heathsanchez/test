#!/usr/bin/env python3
from pathlib import Path
import subprocess
subprocess.run(['python3','scripts/generate_developmental_distinction_gold_v22.py'],check=True)
src=Path('scripts/run_developmental_distinction_gold_v22.py')
dst=Path('scripts/run_developmental_distinction_external_gold_v23.py')
s=src.read_text()
s=s.replace('developmental-distinction-gold-v22','developmental-distinction-external-gold-v23')
s=s.replace('fault-v22-','fault-v23-')
s=s.replace('SEEN_PER_FAMILY=4','SEEN_PER_FAMILY=0')
contaminated = [
'good/tutorial/128_quotIndReduction.ndjson',
'good/tutorial/126_quotSoundType.ndjson',
'good/undecidability/alg-conv-trans-acc-left.ndjson',
'good/init-prelude.ndjson',
'good/perf/app-lam.ndjson',
'good/perf/shift-cascade.ndjson',
'good/tutorial/082_Prod.snd.ndjson',
'good/perf/grind-ring-5.ndjson',
'good/tutorial/080_RBTree.id_spec.ndjson',
'good/undecidability/subject-reduction-redex.ndjson',
'good/tutorial/079_listRecReduction.ndjson',
]
anchor='selected={}\n'
if anchor not in s: raise SystemExit('V23 selected anchor missing')
block='CONTAMINATED_CASES='+repr(set(contaminated))+'\nselected={}\n'
s=s.replace(anchor,block,1)
s=s.replace('need=SEEN_PER_FAMILY+GOLD_PER_FAMILY', "pool=[x for x in pool if x[1] not in CONTAMINATED_CASES]\n    need=GOLD_PER_FAMILY")
s=s.replace('selected[fam]=[r for _,r in pool[SEEN_PER_FAMILY:SEEN_PER_FAMILY+GOLD_PER_FAMILY]]','selected[fam]=[r for _,r in pool[:GOLD_PER_FAMILY]]')
s=s.replace("'status':'SEALED_GOLD_V22'", "'status':'EXTERNAL_SEALED_GOLD_V23'")
s=s.replace("'seen_cases_skipped_per_family':SEEN_PER_FAMILY,", "'contaminated_case_paths_excluded':sorted(CONTAMINATED_CASES),")
s=s.replace("if acc!=1.0: raise SystemExit('frozen V21 quotient failed sealed gold transfer')", "if acc!=1.0: raise SystemExit('frozen V21 quotient failed external sealed gold transfer')")
s=s.replace("generated V22 sealed gold evaluation", "generated V23 external sealed gold evaluation")
dst.write_text(s)
print('generated V23 external gold evaluator with exact prior-path exclusion and frozen V21 rule')
