import json, sys
from pathlib import Path
R=Path(__file__).parent
A=json.loads(Path(sys.argv[1]).read_text())
arms=['RAW','JOIN_DOTS','RIVAL','VERIFIED_RESIDUAL','LATENT_CONSTRUCT','ORACLE_LAW']
summary={}
for arm in arms:
    rows=[x for x in A if x['arm']==arm]
    n=len(rows)
    parse_valid=sum(isinstance(x.get('law'),dict) for x in rows)
    train7=sum(x.get('train_correct')==7 for x in rows)
    held=sum(x.get('heldout_pred')==x.get('heldout_truth') for x in rows)
    add=sum(isinstance(x.get('law'),dict) and x['law'].get('kind')=='add_mod4' for x in rows)
    summary[arm]={'n':n,'parse_valid':parse_valid,'train_7of7':train7,'heldout_correct':held,'accuracy':held/n if n else 0,'add_mod4_count':add}
lat=summary['LATENT_CONSTRUCT']['accuracy']; raw=summary['RAW']['accuracy']
out={'summary':summary,'primary':{
    'latent_gt_raw':lat>raw,
    'latent_gt_join':lat>summary['JOIN_DOTS']['accuracy'],
    'latent_gt_rival':lat>summary['RIVAL']['accuracy'],
    'latent_gt_verified':lat>summary['VERIFIED_RESIDUAL']['accuracy'],
    'oracle_ceiling':summary['ORACLE_LAW']['accuracy'],
    'primary_pass':lat>raw and summary['ORACLE_LAW']['accuracy']==1.0
}}
(R/'scores.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
