import json,re,sys
from pathlib import Path
R=Path(__file__).parent
D=json.loads((R/'cases.json').read_text())
A=json.loads(Path(sys.argv[1]).read_text())
truth={c['id']:c['correct'] for c in D['cases']}
arms=['RAW_RECONSTRUCT','JOIN_DOTS','RIVAL_SEPARATOR','VERIFIED_RESIDUAL','ORACLE_LAW']
summary={}
for arm in arms:
    rows=[x for x in A if x['arm']==arm]; correct=0
    for x in rows:
        m=re.search(r'CHOICE:\s*([JKLM])',x['answer'].upper())
        pred=m.group(1) if m else None
        x['parsed_choice']=pred; x['correct']=(pred==truth[x['case_id']]); correct+=int(x['correct'])
    summary[arm]={'n':len(rows),'correct':correct,'accuracy':correct/len(rows) if rows else 0}
vr=summary['VERIFIED_RESIDUAL']['accuracy']; raw=summary['RAW_RECONSTRUCT']['accuracy']
primary={'verified_gt_raw':vr>raw,'rival_gt_raw':summary['RIVAL_SEPARATOR']['accuracy']>raw,'join_gt_raw':summary['JOIN_DOTS']['accuracy']>raw,'oracle_ceiling':summary['ORACLE_LAW']['accuracy'],'primary_pass':vr>raw}
out={'summary':summary,'primary':primary}
(R/'scores.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
