import json, sys
from collections import defaultdict
from pathlib import Path

p=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).parent/'answers.json')
rows=json.loads(p.read_text())
arms=sorted(set(r['arm'] for r in rows))
summary={}
for arm in arms:
    xs=[r for r in rows if r['arm']==arm]
    summary[arm]={
        'n':len(xs),
        'query_valid':sum(1 for r in xs if r.get('query_valid',True)),
        'optimal_query_rate':sum(r['query_optimal'] for r in xs)/len(xs),
        'target_correct':sum(r['correct'] for r in xs),
        'accuracy':sum(r['correct'] for r in xs)/len(xs),
        'mean_entropy_after':sum(r['entropy_after'] for r in xs)/len(xs),
        'mean_info_gain_regret':sum(r['optimal_info_gain']-r['chosen_info_gain'] for r in xs)/len(xs),
    }
by_family={}
for m in [2,3,5]:
    by_family[str(m)]={}
    for arm in arms:
        xs=[r for r in rows if r['arm']==arm and r['m']==m]
        by_family[str(m)][arm]={
            'n':len(xs),
            'optimal_query_rate':sum(r['query_optimal'] for r in xs)/len(xs),
            'accuracy':sum(r['correct'] for r in xs)/len(xs),
            'mean_entropy_after':sum(r['entropy_after'] for r in xs)/len(xs),
        }
t=summary['TARGET_INFO_GAIN_OBS_ONLY']; rnd=summary['RANDOM_QUERY']; gen=summary['GENERIC_OBS_ONLY']
primary={
    'target_ig_accuracy_gt_random':t['accuracy']>rnd['accuracy'],
    'target_ig_optimal_rate_ge_0p80':t['optimal_query_rate']>=0.80,
    'target_ig_ge_generic_accuracy':t['accuracy']>=gen['accuracy'],
    'target_ig_regret_lt_random':t['mean_info_gain_regret']<rnd['mean_info_gain_regret'],
}
primary['primary_pass']=primary['target_ig_accuracy_gt_random'] and primary['target_ig_optimal_rate_ge_0p80']
out={'summary':summary,'by_family':by_family,'primary':primary}
(Path(__file__).parent/'scores.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
