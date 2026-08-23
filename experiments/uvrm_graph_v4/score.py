import json,re,sys
from pathlib import Path
HERE=Path(__file__).parent
DATA=json.loads((HERE/'cases.json').read_text())

def norm(s): return re.sub(r'[^a-z0-9]+',' ',s.lower())

def score_text(case,text):
    t=norm(text)
    mode_ok=case['expected_mode'].lower() in t
    concept_hits=sum(1 for x in case['expected_move_concepts'] if norm(x).strip() in t)
    avoid_hits=sum(1 for x in case['avoid'] if norm(x).strip() in t)
    return {'mode_ok':mode_ok,'concept_hits':concept_hits,'concept_total':len(case['expected_move_concepts']),'avoid_hits':avoid_hits,
            'pass':mode_ok and concept_hits>=max(1,(len(case['expected_move_concepts'])+1)//2) and avoid_hits==0}

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: score.py answers.json')
    ans=json.loads(Path(sys.argv[1]).read_text())
    rows=[]
    for c in DATA['cases']:
        for arm in ('TRANSCRIPT','GRAPH_ABL','GRAPH','GRAPH_RULES'):
            key=f"{c['id']}__{arm}"
            if key not in ans: continue
            rows.append({'case':c['id'],'domain':c['domain'],'arm':arm,**score_text(c,ans[key])})
    print(json.dumps(rows,indent=2))
    by={}
    for r in rows:
        by.setdefault(r['arm'],[]).append(r)
    print(json.dumps({a:{'n':len(rs),'pass_rate':sum(r['pass'] for r in rs)/len(rs),'mean_concept_recall':sum(r['concept_hits']/r['concept_total'] for r in rs)/len(rs),'avoid_rate':sum(r['avoid_hits']>0 for r in rs)/len(rs)} for a,rs in by.items()},indent=2))

if __name__=='__main__': main()
