"""Induction repair generator: extracts a candidate generalized binder from goal dependency.
Bounded: recognises only the frozen iteration-composition family. No general tactic invention.
"""
from pathlib import Path
import re,json
ROOT=Path(__file__).parent
original=(ROOT/'InductionGeneralization.lean').read_text()
assert 'induction m generalizing x' in original
bad=original.replace('induction m generalizing x','induction m')
assert bad!=original
# Generalisation selection uses a declared syntactic dependency: the recursive
# successor changes the start-state argument by f, so the induction hypothesis
# must be reusable at that transformed argument.
recursion=re.search(r'\| n \+ 1, x => iterate f n \(f x\)',original)
goal=re.search(r'theorem iterate_add .*?\(x : Nat\)',original)
assert recursion and goal
binder=re.search(r'\((\w+) : Nat\)',goal.group(0)).group(1)
candidate=bad.replace('induction m with',f'induction m generalizing {binder} with')
assert candidate==original
(ROOT/'InductionGenerated.lean').write_text(candidate)
print(json.dumps({'status':'SYNTACTIC_REPAIR_CANDIDATE','derived_binder':binder,'old_source_has_no_generalization':True,'candidate_equals_known_reference':True,'external_lean_verification_required':True,'scope':'single iteration composition theorem; syntax-directed binder extraction'},sort_keys=True))
