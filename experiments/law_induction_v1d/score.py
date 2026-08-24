import json,sys
from pathlib import Path
R=Path(__file__).parent
A=json.loads(Path(sys.argv[1]).read_text())
arms=['RAW_RECONSTRUCT','JOIN_DOTS','RIVAL_SEPARATOR','VERIFIED_RESIDUAL','ORACLE_LAW']
summary={}
for arm in arms:
    rows=[x for x in A if x['arm']==arm]
    n=len(rows)
    valid=sum(isinstance(x.get('law'),dict) and x['law'].get('kind') in ('lookup','add_mod4') for x in rows)
    train7=sum(x.get('train_correct')==7 for x in rows)
    held=sum(x.get('heldout_pred')==x.get('heldout_truth') for x in rows)
    add=sum(isinstance(x.get('law'),dict) and x['law'].get('kind')=='add_mod4' for x in rows)
    summary[arm]={'n':n,'parse_valid':valid,'train_7of7':train7,'heldout_correct':held,'accuracy':held/n if n else 0,'add_mod4_count':add}
raw=summary['RAW_RECONSTRUCT']['accuracy']; vr=summary['VERIFIED_RESIDUAL']['accuracy']
out={'summary':summary,'primary':{'verified_gt_raw':vr>raw,'rival_gt_raw':summary['RIVAL_SEPARATOR']['accuracy']>raw,'join_gt_raw':summary['JOIN_DOTS']['accuracy']>raw,'oracle_ceiling':summary['ORACLE_LAW']['accuracy'],'primary_pass':vr>raw and summary['ORACLE_LAW']['accuracy']==1.0}}
(R/'scores.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
