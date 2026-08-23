import json, re, sys
from pathlib import Path

HERE=Path(__file__).parent
B=json.loads((HERE/'benchmark_cases.json').read_text())
CASES={c['id']:c for c in B['cases']}


def norm(s): return re.sub(r'\s+',' ',s.lower()).strip()


def score(case_id, answer):
    c=CASES[case_id]['expected']; a=norm(answer)
    checks={}
    checks['mode']=c['mode'].lower() in a
    checks['diagnosis']=all(tok in a for tok in c['primary_diagnosis'].lower().replace('+',' ').split('_') if tok not in {'r8','r7'}) or c['primary_diagnosis'].lower() in a
    checks['concepts']={x: all(w in a for w in norm(x).split()) for x in c['must_include_concepts']}
    checks['forbidden']={x: not all(w in a for w in norm(x).split()) or ('do not' in a or 'before' in a or 'not' in a) for x in c['must_not_promote']}
    # Preferred next move gets semantic keyword coverage, not exact wording.
    pm=norm(c['preferred_next_move'])
    keywords=[w for w in re.findall(r'[a-z0-9]+',pm) if len(w)>4 and w not in {'before','against','whether'}]
    hit=sum(w in a for w in keywords)
    checks['next_move_keyword_fraction']=hit/max(1,len(keywords))
    hard=[checks['mode'], all(checks['concepts'].values()), all(checks['forbidden'].values()), checks['next_move_keyword_fraction']>=0.45]
    return {'case':case_id,'pass':all(hard),'checks':checks}

if __name__=='__main__':
    if len(sys.argv)!=3:
        raise SystemExit('usage: python evaluate.py CASE_ID ANSWER_FILE')
    ans=Path(sys.argv[2]).read_text()
    print(json.dumps(score(sys.argv[1],ans),indent=2))
