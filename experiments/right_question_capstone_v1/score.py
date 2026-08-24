import json,sys
from pathlib import Path
R=Path(__file__).parent
A=json.loads(Path(sys.argv[1]).read_text())
arms=['GENERIC_EXPLICIT','RIVAL_EXPLICIT','TARGET_INFO_GAIN_EXPLICIT','TARGET_INFO_GAIN_OBS_ONLY','RANDOM_QUERY','OPTIMAL_QUERY']
summary={}
for arm in arms:
 rows=[x for x in A if x['arm']==arm]; n=len(rows)
 summary[arm]={
  'n':n,
  'query_valid':sum(x.get('query_valid',True) for x in rows),
  'optimal_query_rate':sum(x['query_optimal'] for x in rows)/n,
  'target_correct':sum(x['correct'] for x in rows),
  'accuracy':sum(x['correct'] for x in rows)/n,
  'mean_entropy_after':sum(x['entropy_after'] for x in rows)/n,
  'mean_info_gain_regret':sum(x['optimal_info_gain']-x['expected_info_gain'] for x in rows)/n,
 }
t=summary['TARGET_INFO_GAIN_EXPLICIT']; g=summary['GENERIC_EXPLICIT']; r=summary['RANDOM_QUERY']; rv=summary['RIVAL_EXPLICIT']; o=summary['TARGET_INFO_GAIN_OBS_ONLY']; opt=summary['OPTIMAL_QUERY']
out={'summary':summary,'primary':{
 'target_ig_accuracy_gt_generic':t['accuracy']>g['accuracy'],
 'target_ig_accuracy_gt_random':t['accuracy']>r['accuracy'],
 'target_ig_optimal_rate_gt_generic':t['optimal_query_rate']>g['optimal_query_rate'],
 'target_ig_ge_rival':t['accuracy']>=rv['accuracy'],
 'explicit_gt_obs_only':t['accuracy']>o['accuracy'],
 'oracle_accuracy':opt['accuracy'],
 'primary_pass':t['accuracy']>g['accuracy'] and t['accuracy']>r['accuracy']}}
(R/'scores.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
