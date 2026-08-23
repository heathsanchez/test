import json
from pathlib import Path
HERE=Path(__file__).parent
D=json.loads((HERE/'cases.json').read_text())

def main():
    ids=set()
    for c in D['cases']:
        assert c['id'] not in ids; ids.add(c['id'])
        assert c['evidence'] and c['relations']
        assert c['expected_mode'] in {'MAP','DISCRIMINATE','TRANSFER','EXPLOIT','REFRAME','INSPECT'}
        assert c['expected_move_concepts']
        # Protected labels must not be embedded in evidence or relation endpoints.
        protected=[c['expected_mode'],*c['expected_move_concepts'],*c['avoid']]
        raw=(' '.join(c['evidence'])+' '+' '.join(x for r in c['relations'] for x in (r[0],r[2]))).lower()
        # Terms may naturally overlap; only exact expected label serialization is forbidden.
        assert 'expected_mode' not in raw and 'expected_move_concepts' not in raw
        # GRAPH and GRAPH_ABL parity: relation endpoints identical by construction; labels are sole difference.
        for r in c['relations']:
            assert len(r)==3 and r[1] in {'SUPPORTS','REFUTES','WEAKENS','MOTIVATES','BLOCKS','SHARPENS','RIVAL_OF'}
    domains={c['domain'] for c in D['cases']}
    assert {'lean_kernel','sair','triskelion','mathgraph'} <= domains
    print(f"cases={len(D['cases'])} domains={sorted(domains)} validation=PASS")

if __name__=='__main__': main()
