import json,re,sys
from pathlib import Path
HERE=Path(__file__).parent
DATA=json.loads((HERE.parent/'uvrm_graph_v5'/'cases.json').read_text())
ARMS=('RAW','RECONSTRUCT_1','RECONSTRUCT_2','GRAPH','GRAPH_PERMUTED')

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
            if key in ans: rows.append({'case':c['id'],'domain':c['domain'],'arm':arm,**score_text(c,ans[key])})
    print(json.dumps(rows,indent=2))
    out={}
    for arm in ARMS:
        rs=[r for r in rows if r['arm']==arm]
        out[arm]={'n':len(rs),'invocations_per_case':2 if arm=='RECONSTRUCT_2' else 1,'max_generated_tokens_per_case':400 if arm=='RECONSTRUCT_2' else 220,'exact_mode_rate':sum(r['exact_mode'] for r in rs)/len(rs),'semantic_pass_rate':sum(r['semantic_pass'] for r in rs)/len(rs),'mean_semantic_score':sum(r['semantic_score'] for r in rs)/len(rs),'forbidden_rate':sum(r['forbidden_hits']>0 for r in rs)/len(rs)}
    print(json.dumps(out,indent=2))
if __name__=='__main__': main()
