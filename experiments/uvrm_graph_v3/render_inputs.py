import json
from pathlib import Path

HERE = Path(__file__).parent
E = json.loads((HERE/'evidence.json').read_text())
B = json.loads((HERE/'benchmark_cases.json').read_text())

UVRM_MIN = '''Use the verified residual process. Push the strongest current route; read the result as evidence; diagnose the failure level; map when unclear; inspect closure before invention; state rivals; prefer the smallest deciding experiment; do not promote stronger claims while weaker explanations remain viable.'''


def visible_nodes(cutoff):
    return [n for n in E['nodes'] if n['order'] <= cutoff]


def visible_edges(cutoff):
    return [e for e in E['typed_edges'] if e['order'] <= cutoff]


def transcript(case):
    chunks=[f"TARGET: {case['target']}", UVRM_MIN]
    for n in visible_nodes(case['cutoff_order']):
        chunks.append(f"RESULT {n['id']}: {n['text']} Facts={n['facts']} Provenance={n['provenance']}")
    chunks.append('TASK: Give current residual, diagnosis, live rivals, research mode, and smallest next experiment. Do not use future information.')
    return '\n\n'.join(chunks)


def graph(case, typed=True, rules=False):
    cutoff=case['cutoff_order']
    payload={
        'target':case['target'],
        'method':UVRM_MIN,
        'evidence':visible_nodes(cutoff),
        'hypotheses':E['hypotheses'],
    }
    if typed:
        payload['relations']=visible_edges(cutoff)
    else:
        # Same visible facts and hypothesis text, but strip scientific relation types.
        payload['relations']=[{'order':e['order'],'from':e['from'],'to':e['to'],'text':e['text']} for e in visible_edges(cutoff)]
    if rules:
        payload['generation_hints']=[
            'Rare literal repetition plus frequent convergence weakens literal-cache explanations.',
            'If an expensive new representation is not justified, inspect existing closure/composition first.',
            'When exact reusable same-frame structure is observed, test that composition causally before ontology expansion.'
        ]
    payload['task']='Give current residual, diagnosis, live rivals, research mode, and smallest next experiment. Do not use future information.'
    return json.dumps(payload,indent=2,sort_keys=True)


def render_all():
    out=HERE/'rendered'
    out.mkdir(exist_ok=True)
    for c in B['cases']:
        cid=c['id']
        (out/f'{cid}__TRANSCRIPT.txt').write_text(transcript(c))
        (out/f'{cid}__GRAPH.json').write_text(graph(c,typed=True,rules=False))
        (out/f'{cid}__GRAPH_ABL.json').write_text(graph(c,typed=False,rules=False))
        (out/f'{cid}__GRAPH_RULES.json').write_text(graph(c,typed=True,rules=True))

if __name__=='__main__':
    render_all()
    print('rendered', len(B['cases'])*4, 'inputs')
