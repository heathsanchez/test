import json,sys
from collections import defaultdict
from pathlib import Path
p=Path(sys.argv[1]); rows=json.loads(p.read_text())
by=defaultdict(list)
for r in rows: by[r['arm']].append(r)
summary={}
for arm,rs in sorted(by.items()):
    n=len(rs); valid=sum(r.get('query_valid',True) for r in rs); opt=sum(r['query_optimal'] for r in rs); cor=sum(r['correct'] for r in rs)
    summary[arm]={'n':n,'query_valid':valid,'optimal_query_rate':opt/n,'target_correct':cor,'accuracy':cor/n,
                  'mean_entropy_after':sum(r['entropy_after'] for r in rs)/n,
                  'mean_info_gain_regret':sum(r['optimal_info_gain']-r['chosen_info_gain'] for r in rs)/n}
byfam={}
for m in [2,3,5]:
    byfam[str(m)]={}
    for arm in sorted(by):
        rs=[r for r in by[arm] if r['m']==m]
        if not rs: continue
        n=len(rs)
        byfam[str(m)][arm]={'n':n,'optimal_query_rate':sum(r['query_optimal'] for r in rs)/n,
                            'accuracy':sum(r['correct'] for r in rs)/n,
                            'mean_entropy_after':sum(r['entropy_after'] for r in rs)/n}
q=summary['TARGET_QUOTIENT']; o=summary['OBS_ONLY']; s=summary['SHAM_MARGINAL']
primary={'quotient_optimal_gt_obs':q['optimal_query_rate']>o['optimal_query_rate'],
         'quotient_accuracy_gt_obs':q['accuracy']>o['accuracy'],
         'quotient_optimal_ge_0p90':q['optimal_query_rate']>=0.90,
         'quotient_gt_sham_optimal':q['optimal_query_rate']>s['optimal_query_rate'],
         'quotient_regret_lt_obs':q['mean_info_gain_regret']<o['mean_info_gain_regret']}
primary['primary_pass']=primary['quotient_optimal_gt_obs'] and primary['quotient_accuracy_gt_obs'] and primary['quotient_optimal_ge_0p90']
out={'summary':summary,'by_family':byfam,'primary':primary}
Path(__file__).with_name('scores.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
