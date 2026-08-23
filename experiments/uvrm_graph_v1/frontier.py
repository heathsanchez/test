import json
from pathlib import Path

HERE = Path(__file__).parent

def load_graph():
    return json.loads((HERE / 'graph.json').read_text())

def index(g):
    return {n['id']: n for n in g['nodes']}

def incoming(g, node_id, edge_type=None):
    return [e for e in g['edges'] if e['to']==node_id and (edge_type is None or e['type']==edge_type)]

def outgoing(g, node_id, edge_type=None):
    return [e for e in g['edges'] if e['from']==node_id and (edge_type is None or e['type']==edge_type)]

def refuted_hypotheses(g):
    idx=index(g)
    ref=set()
    for e in g['edges']:
        if e['type']=='REFUTES' and idx.get(e['to'],{}).get('type')=='HYPOTHESIS':
            ref.add(e['to'])
    return ref

def live_hypotheses(g):
    ref=refuted_hypotheses(g)
    return [n for n in g['nodes'] if n['type']=='HYPOTHESIS' and n['id'] not in ref]

def candidate_score(g, a):
    idx=index(g)
    ref=refuted_hypotheses(g)
    # A candidate whose motivating hypothesis is refuted should be dominated.
    motives=incoming(g,a['id'],'MOTIVATES')
    dead_motive=any(e['from'] in ref for e in motives)
    # Actions that directly discriminate a live hypothesis get priority.
    discr=incoming(g,a['id'],'DISCRIMINATES')
    live=set(h['id'] for h in live_hypotheses(g))
    discriminates_live=any(e['from'] in live for e in discr)
    # Closure/composition before invention is a hard methodological preference
    # when a live same-frame candidate exists.
    return (
        1 if dead_motive else 0,
        0 if discriminates_live else 1,
        0 if a.get('composition_before_invention') else 1,
        1 if a.get('changes_representation') else 0,
        a.get('complexity',99),
        a['id']
    )

def choose_next(g):
    candidates=[n for n in g['nodes'] if n['type']=='CANDIDATE_ACTION']
    if not candidates:
        return None
    return min(candidates,key=lambda a:candidate_score(g,a))

def reconstruct_state(g):
    ref=refuted_hypotheses(g)
    live=[h['id'] for h in live_hypotheses(g)]
    residuals=[n['id'] for n in g['nodes'] if n['type']=='RESIDUAL']
    choice=choose_next(g)
    return {
        'residual_frontier': residuals[-1] if residuals else None,
        'live_hypotheses': live,
        'refuted_hypotheses': sorted(ref),
        'next_action': choice['id'] if choice else None,
        'next_action_name': choice.get('name') if choice else None,
        'score': candidate_score(g,choice) if choice else None,
    }

if __name__=='__main__':
    s=reconstruct_state(load_graph())
    print(json.dumps(s,indent=2))
