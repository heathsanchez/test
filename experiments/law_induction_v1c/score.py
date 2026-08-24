import json,re,sys
from pathlib import Path
R=Path(__file__).parent
D=json.loads((R.parent/'law_induction_v1b'/'cases.json').read_text())
A=json.loads(Path(sys.argv[1]).read_text())
truth={c['id']:c['correct'] for c in D['cases']}
arms=['RAW_RECONSTRUCT','JOIN_DOTS','RIVAL_SEPARATOR','VERIFIED_RESIDUAL','ORACLE_LAW']
def parse(t):
    ms=re.findall(r'CHOICE:\s*([JKLM])',t.upper()); return ms[-1] if ms else None
summary={}
for arm in arms:
    rows=[x for x in A if x['arm']==arm]; n=len(rows); k=sum(parse(x['answer'])==truth[x['case_id']] for x in rows)
    summary[arm]={'n':n,'correct':k,'accuracy':k/n if n else 0}
raw=summary['RAW_RECONSTRUCT']['accuracy']; vr=summary['VERIFIED_RESIDUAL']['accuracy']
out={'summary':summary,'primary':{'verified_gt_raw':vr>raw,'rival_gt_raw':summary['RIVAL_SEPARATOR']['accuracy']>raw,'join_gt_raw':summary['JOIN_DOTS']['accuracy']>raw,'oracle_ceiling':summary['ORACLE_LAW']['accuracy'],'primary_pass':vr>raw}}
(R/'scores.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
