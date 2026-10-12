"""V8 bounded source-conditioned induction binder repair; no reference-proof equality."""
from pathlib import Path
import re,json
root=Path(__file__).parent
source=(root/'InductionHoldout.lean').read_text()
decl=re.search(r'def\s+(\w+)\s+\((\w+)\s*:\s*Nat\s*→\s*Nat\)\s*:\s*Nat\s*→\s*Nat\s*→\s*Nat\s*\n\s*\|\s*0,\s*(\w+)\s*=>\s*\3\s*\n\s*\|\s*(\w+)\s*\+\s*1,\s*(\w+)\s*=>\s*\1\s+\2\s+\4\s*\(\2\s+\5\)',source)
assert decl, 'unknown recursion structure; fail closed'
fn,operator,seed,step_index,step_seed=decl.groups()
assert seed==step_seed
theorem=re.search(r'theorem\s+\w+.*?\((\w+)\s*:\s*Nat\).*?:=\s*by\s*\n\s*induction\s+(\w+)\s+with',source,re.S)
assert theorem,'unrecognized induction structure'
binder,index=theorem.groups()
assert binder==seed and index!=binder
needle=f'induction {index} with'
assert source.count(needle)==1
candidate=source.replace(needle,f'induction {index} generalizing {binder} with')
assert candidate!=source
(root/'InductionHoldoutGenerated.lean').write_text(candidate)
print(json.dumps({'status':'CANDIDATE_REQUIRES_LEAN','source':'InductionHoldout.lean','generated':'InductionHoldoutGenerated.lean','generalized_binder':binder,'induction_index':index,'reference_proof_comparison':False,'grammar':'two-argument function iteration recursion only'},sort_keys=True))
