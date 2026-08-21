#!/usr/bin/env python3
"""Adversarial audit of V6 stage2 scoring.

Corrects two weaknesses discovered after reveal:
1. lexical bucket missed 'caching' because it only searched 'cache';
2. a 12-commit / multi-year horizon can make a broad prediction look stronger than it
   was at the immediate decision frontier.

Reports horizons 3, 5, 8, 12 and does not gate success; it is an audit.
"""
import json
from pathlib import Path

p=Path('v6_sealed_replay_result.json')
if not p.exists():
    raise SystemExit('Place downloaded stage2 result at v6_sealed_replay_result.json')
x=json.load(open(p))
msgs=[c['message'].lower() for c in x['future_commits']]

pred_terms=['lean4','lean 4','compat','feature','parser','kernel','declar','build','cargo','rust','api','dependency','deps','compile','edition','test','example','binary','cli','integration','debug','release','upstream','export format','lint']
rival_terms=['cache','caching','alloc','allocation','index','layout','perf','fast','optim','uparam substitution']

def count(ms,terms):
    text='\n'.join(ms)
    return sum(text.count(t) for t in terms)

rows=[]
for h in (3,5,8,12):
    a=count(msgs[:h],pred_terms)
    b=count(msgs[:h],rival_terms)
    rows.append({'horizon':h,'predicted_family_hits':a,'rival_perf_hits':b,'margin':a-b})

# Manual semantic flags frozen here after reveal solely as an audit, not evidence.
classification=[
  'documentation', 'release_operationalization', 'low_level_caching',
  'upstream_compatibility_fix', 'test_format_compatibility', 'merge',
  'release_operationalization', 'api_lint_compatibility', 'upstream_compatibility_note',
  'parser_feature_change', 'parser_operationalization', 'merge'
]
out={
 'protocol':'DEVELOPMENTAL_CONTROLLER_PILOT_V6_ADVERSARIAL_AUDIT',
 'rows':rows,
 'semantic_classification':classification,
 'audit_verdict':'PARTIAL',
 'interpretation':(
   'The frozen prediction has real support, especially after five commits, but the immediate frontier also contains a genuine low-level caching optimization. '
   'The original scorer overstated the result by missing the word caching and by using a broad multi-year horizon. '
   'V6 therefore demonstrates sealed prospective support, not blind recovery of a unique breakthrough coordinate.'
 ),
 'next_test_requirement':(
   'Select a checkpoint from a dense experimental epoch rather than arbitrary repository history; score the first high-information intervention family, '
   'use a short frozen horizon, and compare against at least two rival controller predictions.'
 )
}
json.dump(out,open('v6_sealed_replay_audit.json','w'),indent=2)
print(json.dumps(out,indent=2))
