import json, re, sys
from pathlib import Path

ROOT=Path(__file__).parent
CASES={c['id']:c for c in json.loads((ROOT/'cases.json').read_text())['cases']}
ANS=json.loads(Path(sys.argv[1]).read_text())


def norm(s):
    return re.sub(r'\s+',' ',s.lower())

def group_hit(text, group):
    t=norm(text)
    return any(x.lower() in t for x in group)

def frac(text, groups):
    return sum(group_hit(text,g) for g in groups)/len(groups) if groups else 0.0

rows=[]
for a in ANS:
    c=CASES[a['case_id']]; text=a['answer']
    e=frac(text,c['experiment_required'])
    s=frac(text,c['separation_required'])
    d=frac(text,c['discipline_required'])
    rows.append({**a,'experiment_score':e,'separation_score':s,'discipline_score':d,'joint_score':(e+s)/2,'joint_pass':e>=2/3 and s>=1/2})

arms=sorted(set(r['arm'] for r in rows))
summary={}
for arm in arms:
    rs=[r for r in rows if r['arm']==arm]
    summary[arm]={
      'n':len(rs),
      'mean_experiment_score':sum(r['experiment_score'] for r in rs)/len(rs),
      'mean_separation_score':sum(r['separation_score'] for r in rs)/len(rs),
      'mean_discipline_score':sum(r['discipline_score'] for r in rs)/len(rs),
      'mean_joint_score':sum(r['joint_score'] for r in rs)/len(rs),
      'joint_passes':sum(r['joint_pass'] for r in rs)
    }
primary={
 'verified_residual_gt_generic': summary['VERIFIED_RESIDUAL']['mean_joint_score']>summary['GENERIC']['mean_joint_score'],
 'info_gain_gt_verify_separation': summary['INFO_GAIN']['mean_separation_score']>summary['VERIFY']['mean_separation_score'],
 'rival_gt_verify_separation': summary['RIVAL']['mean_separation_score']>summary['VERIFY']['mean_separation_score']
}
primary['primary_pass']=primary['verified_residual_gt_generic']
out={'summary':summary,'primary':primary,'rows':rows}
(ROOT/'scores.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'summary':summary,'primary':primary},indent=2))
