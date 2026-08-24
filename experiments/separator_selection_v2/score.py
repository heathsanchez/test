import json,re,sys
from pathlib import Path
ROOT=Path(__file__).parent
cases={c['id']:c for c in json.loads((ROOT/'cases.json').read_text())['cases']}
ans=json.loads(Path(sys.argv[1]).read_text())
arms=['GENERIC','RIVAL','COUNTERFACTUAL','VERIFIED_RESIDUAL']; s={a:{'n':0,'correct':0} for a in arms}; rows=[]
for x in ans:
    m=re.search(r'CHOICE:\s*([ABCD])',x['answer'],re.I); choice=m.group(1).upper() if m else None
    ok=choice==cases[x['case_id']]['correct']; s[x['arm']]['n']+=1; s[x['arm']]['correct']+=int(ok); rows.append({**x,'choice':choice,'correct':ok})
for a in arms: s[a]['accuracy']=s[a]['correct']/s[a]['n'] if s[a]['n'] else 0
primary={'counterfactual_gt_generic':s['COUNTERFACTUAL']['accuracy']>s['GENERIC']['accuracy'],'rival_gt_generic':s['RIVAL']['accuracy']>s['GENERIC']['accuracy'],'verified_gt_rival':s['VERIFIED_RESIDUAL']['accuracy']>s['RIVAL']['accuracy']}
primary['primary_pass']=primary['counterfactual_gt_generic']
out={'summary':s,'primary':primary,'rows':rows}; (ROOT/'scores.json').write_text(json.dumps(out,indent=2)); print(json.dumps({'summary':s,'primary':primary},indent=2))