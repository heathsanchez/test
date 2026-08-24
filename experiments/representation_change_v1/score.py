import json, re, sys
from pathlib import Path

ROOT = Path(__file__).parent
DATA = json.loads((ROOT / 'cases.json').read_text())
ANS = json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'answers.json').read_text())
correct = {c['id']: c['correct'] for c in DATA['cases']}

rows=[]
for x in ANS:
    m = re.search(r'CHOICE\s*:\s*([ABCD])\b', x['answer'], re.I)
    choice = m.group(1).upper() if m else None
    ok = choice == correct[x['case_id']]
    rows.append({**x,'parsed_choice':choice,'correct_choice':correct[x['case_id']],'correct':ok})

arms=sorted({r['arm'] for r in rows})
summary={}
for a in arms:
    rs=[r for r in rows if r['arm']==a]
    summary[a]={'n':len(rs),'correct':sum(r['correct'] for r in rs),'accuracy':sum(r['correct'] for r in rs)/len(rs)}

S=summary
primary={
    'structured_gt_raw': S['STRUCTURED_STATE']['accuracy'] > S['RAW_OUTCOME']['accuracy'],
    'structured_gt_ablation': S['STRUCTURED_STATE']['accuracy'] > S['STRUCTURED_ABLATION']['accuracy'],
    'prose_gt_raw': S['PROSE_MEMORY']['accuracy'] > S['RAW_OUTCOME']['accuracy'],
    'structured_gt_prose': S['STRUCTURED_STATE']['accuracy'] > S['PROSE_MEMORY']['accuracy'],
}
primary['primary_pass'] = primary['structured_gt_raw'] and primary['structured_gt_ablation']

out={'summary':summary,'primary':primary,'rows':rows}
(ROOT/'scores.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'summary':summary,'primary':primary},indent=2))
