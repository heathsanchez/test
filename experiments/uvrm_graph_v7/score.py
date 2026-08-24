import json,re,sys
from pathlib import Path
HERE=Path(__file__).parent
ROOT=HERE.parent
DATA=json.loads((ROOT/'uvrm_graph_v5'/'cases.json').read_text())
ARMS=('MASK_00','MASK_10','MASK_01','MASK_11')
EDGES={'MASK_00':0,'MASK_10':1,'MASK_01':1,'MASK_11':2}

def norm(s): return re.sub(r'[^a-z0-9]+',' ',s.lower()).strip()
def has_any(t,alts): return any(norm(a) in t for a in alts)
def score_text(case,text):
    t=norm(text)
    exact_mode=case['expected_mode'].lower() in t
    required_hits=sum(has_any(t,g) for g in case['required'])
    forbidden_hits=sum(has_any(t,g) for g in case['forbidden'])
    semantic=required_hits/len(case['required'])
    return {'exact_mode':exact_mode,'required_hits':required_hits,'required_total':len(case['required']),'semantic_score':semantic,'forbidden_hits':forbidden_hits,'semantic_pass':semantic>=2/3 and forbidden_hits==0}

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: score.py answers.json')
    ans=json.loads(Path(sys.argv[1]).read_text()); rows=[]
    for c in DATA['cases']:
        for arm in ARMS:
            key=f"{c['id']}__{arm}"
            rows.append({'case':c['id'],'domain':c['domain'],'arm':arm,'edge_count':EDGES[arm],**score_text(c,ans[key])})
    agg={}
    for arm in ARMS:
        rs=[r for r in rows if r['arm']==arm]
        agg[arm]={'n':len(rs),'edge_count':EDGES[arm],'semantic_pass_rate':sum(r['semantic_pass'] for r in rs)/len(rs),'mean_semantic_score':sum(r['semantic_score'] for r in rs)/len(rs),'forbidden_rate':sum(r['forbidden_hits']>0 for r in rs)/len(rs)}
    cases=[]
    for c in DATA['cases']:
        rs={r['arm']:r for r in rows if r['case']==c['id']}
        full=rs['MASK_11']['semantic_score']
        attaining=[r for r in rs.values() if r['semantic_score']==full and r['forbidden_hits']==rs['MASK_11']['forbidden_hits']]
        min_edges=min(r['edge_count'] for r in attaining)
        e1_necessary=rs['MASK_01']['semantic_score']<full
        e2_necessary=rs['MASK_10']['semantic_score']<full
        synergy=(rs['MASK_10']['semantic_score']<full and rs['MASK_01']['semantic_score']<full and rs['MASK_11']['semantic_score']>max(rs['MASK_10']['semantic_score'],rs['MASK_01']['semantic_score']))
        cases.append({'case':c['id'],'domain':c['domain'],'full_score':full,'best_le1_edge_score':max(rs['MASK_00']['semantic_score'],rs['MASK_10']['semantic_score'],rs['MASK_01']['semantic_score']),'min_edges_matching_full':min_edges,'edge1_necessary_relative_full':e1_necessary,'edge2_necessary_relative_full':e2_necessary,'two_edge_synergy':synergy})
    print(json.dumps({'rows':rows,'aggregate':agg,'case_minimality':cases},indent=2))
if __name__=='__main__': main()
