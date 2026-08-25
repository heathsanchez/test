import json, sys
from collections import defaultdict
from pathlib import Path
rows=json.loads(Path(sys.argv[1]).read_text())
by=defaultdict(list)
for r in rows: by[r['arm']].append(r)
def summ(rs):
    n=len(rs)
    return {'n':n,'optimal_query_rate':sum(r.get('query_optimal',False) for r in rs)/n,'accuracy':sum(r.get('correct',False) for r in rs)/n,'mean_entropy_after':sum(r.get('entropy_after',0.0) for r in rs)/n,'ranking_verified_rate':sum(r.get('ranking_verified',False) for r in rs)/n if any('ranking_verified' in r for r in rs) else None}
summary={a:summ(rs) for a,rs in by.items()}
fam={}
for m in [2,3,5]:
    fam[str(m)]={}
    for a,rs in by.items():
        z=[r for r in rs if r['m']==m]
        if z: fam[str(m)][a]=summ(z)
v=summary['VERIFIED_COMPARATIVE']; o=summary['ONE_SHOT_COMPARATIVE']; h=summary['HAND_COMPARATIVE']
primary={'verified_accuracy_gt_one_shot':v['accuracy']>o['accuracy'],'verified_optimal_gt_one_shot':v['optimal_query_rate']>o['optimal_query_rate'],'verified_accuracy_ge_0p90':v['accuracy']>=0.90,'verified_optimal_ge_0p80':v['optimal_query_rate']>=0.80,'hand_accuracy_ge_0p95':h['accuracy']>=0.95}
primary['primary_pass']=primary['verified_accuracy_gt_one_shot'] and primary['verified_optimal_gt_one_shot']
out={'summary':summary,'by_family':fam,'primary':primary}
Path(__file__).with_name('scores.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
