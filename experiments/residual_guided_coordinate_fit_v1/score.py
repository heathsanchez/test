import json,sys
from pathlib import Path
R=Path(__file__).parent
A=json.loads(Path(sys.argv[1]).read_text())
arms=['ONE_SHOT','RANDOM_RESTART','RESIDUAL_GUIDED','CSP_ORACLE']
summary={}
for arm in arms:
    rows=[x for x in A if x['arm']==arm]
    n=len(rows)
    held=sum(x['heldout_pred']==x['heldout_truth'] for x in rows)
    exact=sum(x['best_train']==7 for x in rows)
    mean_train=sum(x['best_train'] for x in rows)/(7*n) if n else 0
    first=[x['best_round'] for x in rows if x['best_train']==7 and x['best_round'] is not None]
    summary[arm]={'n':n,'heldout_correct':held,'accuracy':held/n if n else 0,'train_7of7':exact,
                  'mean_train_fraction':mean_train,'mean_first_exact_round':sum(first)/len(first) if first else None}
rg=summary['RESIDUAL_GUIDED']['accuracy']; rr=summary['RANDOM_RESTART']['accuracy']; one=summary['ONE_SHOT']['accuracy']; oracle=summary['CSP_ORACLE']['accuracy']
out={'summary':summary,'primary':{'residual_guided_gt_random_restart':rg>rr,'residual_guided_gt_one_shot':rg>one,'csp_oracle_ceiling':oracle,'primary_pass':rg>rr and oracle==1.0}}
(R/'scores.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
