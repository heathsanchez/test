import json,sys,statistics
from pathlib import Path
R=Path(__file__).parent
A=json.loads(Path(sys.argv[1]).read_text())
arms=['NO_EXTRA','RANDOM_QUERY','INFO_GAIN_QUERY','ORACLE_QUERY']
summary={}
for arm in arms:
    rows=[x for x in A if x['arm']==arm]
    summary[arm]={
        'n':len(rows),
        'correct':sum(bool(x['correct']) for x in rows),
        'accuracy':sum(bool(x['correct']) for x in rows)/len(rows),
        'mean_n_before':statistics.mean(x['n_before'] for x in rows),
        'mean_n_after':statistics.mean(x['n_after'] for x in rows),
        'mean_entropy_before':statistics.mean(x['entropy_before'] for x in rows),
        'mean_entropy_after':statistics.mean(x['entropy_after'] for x in rows),
    }
info=summary['INFO_GAIN_QUERY']['accuracy']; rnd=summary['RANDOM_QUERY']['accuracy']; no=summary['NO_EXTRA']['accuracy']
out={'summary':summary,'primary':{
    'info_gain_gt_random':info>rnd,
    'info_gain_gt_no_extra':info>no,
    'oracle_ceiling':summary['ORACLE_QUERY']['accuracy'],
    'primary_pass':info>rnd
}}
(R/'scores.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
