import json, re, sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent
CASES = json.loads((ROOT / 'cases.json').read_text())
ANS = json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'answers.json').read_text())
case_map = {c['id']: c for c in CASES['cases']}


def norm(s):
    return re.sub(r'\s+', ' ', s.lower().replace('_',' ').replace('-',' '))


def group_hit(text, group):
    t = norm(text)
    return any(norm(x) in t for x in group)

rows = []
agg = defaultdict(lambda: {'n':0,'abs':0.0,'exp':0.0,'joint':0.0,'passes':0,'forbidden':0})
for a in ANS:
    c = case_map[a['case_id']]
    txt = a['answer']
    ah = [group_hit(txt,g) for g in c['abstraction_required']]
    eh = [group_hit(txt,g) for g in c['experiment_required']]
    fh = [group_hit(txt,g) for g in c.get('forbidden',[])]
    abs_score = sum(ah)/len(ah)
    exp_score = sum(eh)/len(eh)
    joint = (abs_score + exp_score)/2
    passed = abs_score >= (2/3) and exp_score >= 0.5 and not any(fh)
    row = {
        'case_id': a['case_id'], 'arm': a['arm'],
        'abstraction_score': abs_score, 'experiment_score': exp_score,
        'joint_score': joint, 'joint_pass': passed,
        'abstraction_hits': ah, 'experiment_hits': eh, 'forbidden_hits': fh,
        'answer': txt
    }
    rows.append(row)
    z = agg[a['arm']]
    z['n'] += 1; z['abs'] += abs_score; z['exp'] += exp_score; z['joint'] += joint
    z['passes'] += int(passed); z['forbidden'] += int(any(fh))

summary = {}
for arm, z in agg.items():
    n=z['n']
    summary[arm] = {
        'n': n,
        'mean_abstraction_score': z['abs']/n,
        'mean_experiment_score': z['exp']/n,
        'mean_joint_score': z['joint']/n,
        'joint_passes': z['passes'],
        'forbidden_cases': z['forbidden']
    }

primary = {
    'oocr_verify_gt_raw_global': summary['OOCR_VERIFY']['mean_joint_score'] > summary['RAW_GLOBAL']['mean_joint_score'],
    'oocr_verify_gt_shuffled': summary['OOCR_VERIFY']['mean_joint_score'] > summary['SHUFFLED']['mean_joint_score']
}
primary['primary_pass'] = all(primary.values())

out = {'schema':'residual.oocr.v1.score','summary':summary,'primary':primary,'rows':rows}
(ROOT / 'scores.json').write_text(json.dumps(out, indent=2))
print(json.dumps({'summary':summary,'primary':primary}, indent=2))
