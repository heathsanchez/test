import json
from pathlib import Path

HERE = Path(__file__).parent

def load_graph():
    return json.loads((HERE / 'graph.json').read_text())

def index(g):
    return {n['id']: n for n in g['nodes']}

def incoming(g, node_id, edge_type=None):
    return [e for e in g['edges'] if e['to']==node_id and (edge_type is None or e['type']==edge_type)]

def refuted_hypotheses(g):
    idx=index(g)
    return {e['to'] for e in g['edges']
            if e['type']=='REFUTES' and idx.get(e['to'],{}).get('type')=='HYPOTHESIS'}

def supported_hypotheses(g):
    idx=index(g)
    return {e['to'] for e in g['edges']
            if e['type']=='SUPPORTS' and idx.get(e['to'],{}).get('type')=='HYPOTHESIS'}

def live_hypotheses(g):
    ref=refuted_hypotheses(g)
    # A rival may remain live without positive evidence, but 'supported' is tracked separately.
    return [n for n in g['nodes'] if n['type']=='HYPOTHESIS' and n['id'] not in ref]

def candidate_score(g, a):
    ref=refuted_hypotheses(g)
    sup=supported_hypotheses(g)
    live={h['id'] for h in live_hypotheses(g)}
    motives=incoming(g,a['id'],'MOTIVATES')
    discr=incoming(g,a['id'],'DISCRIMINATES')
    sources={e['from'] for e in motives+discr}
    dead_motive=bool(sources) and all(s in ref for s in sources)
    discriminates_supported=any(e['from'] in sup for e in discr)
    discriminates_live=any(e['from'] in live for e in discr)
    has_supported_source=any(s in sup for s in sources)
    # Prefer directly evidence-supported separators, then live discriminators,
    # then composition-before-invention, before representation expansion.
    return (
        1 if dead_motive else 0,
        0 if discriminates_supported else 1,
        0 if has_supported_source else 1,
        0 if discriminates_live else 1,
        0 if a.get('composition_before_invention') else 1,
        1 if a.get('changes_representation') else 0,
        a.get('complexity',99),
        a['id']
    )

def choose_next(g):
    candidates=[n for n in g['nodes'] if n['type']=='CANDIDATE_ACTION']
    return min(candidates,key=lambda a:candidate_score(g,a)) if candidates else None

def reconstruct_state(g):
    ref=refuted_hypotheses(g)
    sup=supported_hypotheses(g)
    live=[h['id'] for h in live_hypotheses(g)]
    residuals=[n['id'] for n in g['nodes'] if n['type']=='RESIDUAL']
    choice=choose_next(g)
    return {
        'residual_frontier': residuals[-1] if residuals else None,
        'live_hypotheses': live,
        'supported_hypotheses': sorted(sup),
        'refuted_hypotheses': sorted(ref),
        'next_action': choice['id'] if choice else None,
        'next_action_name': choice.get('name') if choice else None,
        'score': candidate_score(g,choice) if choice else None,
    }

if __name__=='__main__':
    print(json.dumps(reconstruct_state(load_graph()),indent=2))
