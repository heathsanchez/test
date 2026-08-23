import json
from pathlib import Path
from render_inputs import visible_nodes, visible_edges, graph

HERE=Path(__file__).parent
B=json.loads((HERE/'benchmark_cases.json').read_text())
E=json.loads((HERE/'evidence.json').read_text())


def test_no_future_leak():
    for c in B['cases']:
        cutoff=c['cutoff_order']
        assert all(n['order']<=cutoff for n in visible_nodes(cutoff))
        assert all(e['order']<=cutoff for e in visible_edges(cutoff))
        rendered=graph(c,typed=True,rules=False)
        for n in E['nodes']:
            if n['order']>cutoff:
                assert n['provenance'] not in rendered
                assert n['id'] not in rendered


def test_graph_ablation_same_facts():
    for c in B['cases']:
        typed=json.loads(graph(c,typed=True,rules=False))
        abl=json.loads(graph(c,typed=False,rules=False))
        assert typed['evidence']==abl['evidence']
        assert typed['hypotheses']==abl['hypotheses']
        assert len(typed['relations'])==len(abl['relations'])
        assert any('type' in e for e in typed['relations']) if typed['relations'] else True
        assert all('type' not in e for e in abl['relations'])


def test_rules_arm_only_adds_rules():
    for c in B['cases']:
        base=json.loads(graph(c,typed=True,rules=False))
        rules=json.loads(graph(c,typed=True,rules=True))
        hints=rules.pop('generation_hints')
        assert len(hints)==3
        assert base==rules


def test_expected_hidden_from_inputs():
    for c in B['cases']:
        for arm in [(True,False),(False,False),(True,True)]:
            r=graph(c,typed=arm[0],rules=arm[1])
            assert c['expected']['preferred_next_move'] not in r

if __name__=='__main__':
    test_no_future_leak(); test_graph_ablation_same_facts(); test_rules_arm_only_adds_rules(); test_expected_hidden_from_inputs()
    print('uvrm_graph_v3_protocol=PASS')
