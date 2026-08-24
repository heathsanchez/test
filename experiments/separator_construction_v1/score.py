import json,re,sys,itertools
from pathlib import Path
ROOT=Path(__file__).parent
CASES={c['id']:c for c in json.loads((ROOT/'cases.json').read_text())['cases']}
answers=json.loads(Path(sys.argv[1] if len(sys.argv)>1 else ROOT/'answers.json').read_text())
pat=re.compile(r'TEST:\s*probe\(([^,]+),([^,]+),([^\)]+)\)',re.I)

def eval_case(c,answer):
    m=pat.search(answer)
    valid=False; separates=False; cost=None; expr=None
    if m:
        p,ctrl,metric=[x.strip() for x in m.groups()]
        if p in c['allowed']['probe'] and ctrl in c['allowed']['control'] and metric in c['allowed']['metric']:
            valid=True; expr=f'{p}|{ctrl}|{metric}'
            ot=c['target'].get(expr,c['default']); orv=c['rival'].get(expr,c['default'])
            separates=ot!=orv
            cost=c['cost']['probe']+c['cost']['control'][ctrl]+c['cost']['metric']
    # frozen minimum separating cost by exhaustive DSL census
    mincost=999
    for p,ctrl,metric in itertools.product(c['allowed']['probe'],c['allowed']['control'],c['allowed']['metric']):
        e=f'{p}|{ctrl}|{metric}'
        if c['target'].get(e,c['default'])!=c['rival'].get(e,c['default']):
            cc=c['cost']['probe']+c['cost']['control'][ctrl]+c['cost']['metric']; mincost=min(mincost,cc)
    low=answer.lower(); rival_hit=any(t in low for t in c['rival_terms'])
    utility=(1.0/cost) if valid and separates else 0.0
    return {'valid':valid,'expression':expr,'separates':separates,'cost':cost,'minimum_cost':mincost if mincost<999 else None,'minimal_separator':bool(valid and separates and cost==mincost),'rival_hit':rival_hit,'separator_utility':utility}

rows=[]
for a in answers:
    r={**a,**eval_case(CASES[a['case_id']],a['answer'])}; rows.append(r)
arms=sorted(set(r['arm'] for r in rows)); summary={}
for arm in arms:
    rr=[r for r in rows if r['arm']==arm]; n=len(rr)
    summary[arm]={'n':n,'valid_rate':sum(r['valid'] for r in rr)/n,'separator_rate':sum(r['separates'] for r in rr)/n,'minimal_separator_rate':sum(r['minimal_separator'] for r in rr)/n,'rival_hit_rate':sum(r['rival_hit'] for r in rr)/n,'mean_separator_utility':sum(r['separator_utility'] for r in rr)/n}
primary={'rival_first_gt_generic':summary['RIVAL_FIRST']['mean_separator_utility']>summary['GENERIC']['mean_separator_utility'],'counterfactual_ge_rival':summary['COUNTERFACTUAL_WORLDS']['mean_separator_utility']>=summary['RIVAL_FIRST']['mean_separator_utility'],'verified_gt_rival':summary['VERIFIED_RESIDUAL']['mean_separator_utility']>summary['RIVAL_FIRST']['mean_separator_utility']}
primary['primary_pass']=primary['rival_first_gt_generic']
obj={'summary':summary,'primary':primary,'rows':rows}
(ROOT/'scores.json').write_text(json.dumps(obj,indent=2)); print(json.dumps({'summary':summary,'primary':primary},indent=2))
