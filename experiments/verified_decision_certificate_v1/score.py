import json, sys
from collections import defaultdict
from pathlib import Path

p=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).with_name('answers.json'))
rows=json.loads(p.read_text())
summary={}; by_family={}
for arm in sorted(set(r['arm'] for r in rows)):
    rs=[r for r in rows if r['arm']==arm]; n=len(rs)
    x={'n':n,'optimal_query_rate':sum(r.get('query_optimal',False) for r in rs)/n,
       'target_correct':sum(r['correct'] for r in rs),'accuracy':sum(r['correct'] for r in rs)/n,
       'decision_complete_rate':sum(r.get('decision_complete',False) for r in rs)/n,
       'mean_entropy_after':sum(r['entropy_after'] for r in rs)/n}
    if any('certificate_exact' in r for r in rs):
        x['certificate_exact_rate']=sum(r.get('certificate_exact',False) for r in rs)/n
        x['mean_n_errors']=sum(r.get('n_errors',0) for r in rs)/n
    if any('rounds' in r for r in rs): x['mean_rounds']=sum(r.get('rounds',1) for r in rs)/n
    summary[arm]=x
for m in sorted(set(r['m'] for r in rows)):
    by_family[str(m)]={}
    for arm in sorted(set(r['arm'] for r in rows)):
        rs=[r for r in rows if r['m']==m and r['arm']==arm]
        if not rs: continue
        n=len(rs); z={'n':n,'optimal_query_rate':sum(r.get('query_optimal',False) for r in rs)/n,
                       'accuracy':sum(r['correct'] for r in rs)/n,
                       'decision_complete_rate':sum(r.get('decision_complete',False) for r in rs)/n}
        if any('certificate_exact' in r for r in rs): z['certificate_exact_rate']=sum(r.get('certificate_exact',False) for r in rs)/n
        by_family[str(m)][arm]=z
v=summary['VERIFIED_CERTIFICATE']; o=summary['ONE_SHOT_CERTIFICATE']; raw=summary['RAW_DIRECT']; hand=summary['HAND_CERTIFICATE']
primary={'verified_accuracy_gt_one_shot':v['accuracy']>o['accuracy'],
         'verified_decision_complete_gt_one_shot':v['decision_complete_rate']>o['decision_complete_rate'],
         'verified_accuracy_ge_0p90':v['accuracy']>=0.90,
         'verified_decision_complete_ge_0p80':v['decision_complete_rate']>=0.80,
         'verified_accuracy_gt_raw':v['accuracy']>raw['accuracy'],
         'hand_accuracy_ge_0p95':hand['accuracy']>=0.95}
primary['primary_pass']=primary['verified_accuracy_gt_one_shot'] and primary['verified_decision_complete_gt_one_shot']
out={'summary':summary,'by_family':by_family,'primary':primary}
Path(__file__).with_name('scores.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
