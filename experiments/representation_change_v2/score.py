import json, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
CASES = {c['id']: c for c in json.loads((ROOT/'cases.json').read_text())['cases']}
ANS = json.loads(Path(sys.argv[1]).read_text())
ARMS = ['RAW_OUTCOME','PROSE_MEMORY','STRUCTURED_STATE','STRUCTURED_ABLATION']

rows=[]
summary=defaultdict(lambda:{'n':0,'correct':0})
for r in ANS:
    m=re.search(r'CHOICE\s*:\s*([ABCD])', r['answer'], re.I)
    choice=m.group(1).upper() if m else None
    gold=CASES[r['case_id']]['correct']
    ok=(choice==gold)
    rows.append({**r,'choice':choice,'correct_choice':gold,'is_correct':ok})
    summary[r['arm']]['n']+=1
    summary[r['arm']]['correct']+=int(ok)

outsum={}
for a in ARMS:
    s=summary[a]
    outsum[a]={**s,'accuracy':s['correct']/s['n'] if s['n'] else 0.0}

primary={
    'structured_gt_raw': outsum['STRUCTURED_STATE']['accuracy'] > outsum['RAW_OUTCOME']['accuracy'],
    'structured_gt_ablation': outsum['STRUCTURED_STATE']['accuracy'] > outsum['STRUCTURED_ABLATION']['accuracy'],
    'prose_gt_raw': outsum['PROSE_MEMORY']['accuracy'] > outsum['RAW_OUTCOME']['accuracy'],
    'structured_gt_prose': outsum['STRUCTURED_STATE']['accuracy'] > outsum['PROSE_MEMORY']['accuracy'],
}
primary['primary_pass']=primary['structured_gt_raw'] and primary['structured_gt_ablation']
out={'summary':outsum,'primary':primary,'rows':rows}
(ROOT/'scores.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'summary':outsum,'primary':primary},indent=2))
