import json,re,sys
from pathlib import Path
ROOT=Path(__file__).parent
cases={c['id']:c for c in json.loads((ROOT/'cases.json').read_text())['cases']}
answers=json.loads(Path(sys.argv[1]).read_text())
arms=['COLD','RAW_EPISODE','PROSE_LAW','STRUCTURED_LAW','WRONG_LAW']
summary={}
rows=[]
for arm in arms:
    xs=[x for x in answers if x['arm']==arm]
    correct=0
    for x in xs:
        m=re.search(r'CHOICE:\s*([JKLM])',x['answer'])
        ch=m.group(1) if m else None
        ok=ch==cases[x['case_id']]['correct']
        correct+=int(ok)
        rows.append({'case_id':x['case_id'],'arm':arm,'choice':ch,'correct':ok})
    summary[arm]={'n':len(xs),'correct':correct,'accuracy':correct/len(xs) if xs else 0}
A={k:v['accuracy'] for k,v in summary.items()}
primary={'structured_gt_cold':A['STRUCTURED_LAW']>A['COLD'],'structured_gt_raw':A['STRUCTURED_LAW']>A['RAW_EPISODE'],'structured_gt_wrong':A['STRUCTURED_LAW']>A['WRONG_LAW']}
primary['primary_pass']=all(primary.values())
out={'summary':summary,'primary':primary,'secondary':{'structured_minus_prose':A['STRUCTURED_LAW']-A['PROSE_LAW'],'cold_ceiling_warning':A['COLD']>=0.75},'rows':rows}
(ROOT/'scores.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))