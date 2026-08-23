import json
from pathlib import Path

HERE = Path(__file__).parent

def load_graph():
    return json.loads((HERE / 'graph.json').read_text())

def view(g, max_order):
    events=[e for e in g['events'] if e['order']<=max_order]
    rels=[r for r in g['relations'] if r['order']<=max_order]
    claims={c['id']:c for c in g['claims']}
    support={k:[] for k in claims}; refute={k:[] for k in claims}
    for r in rels:
        if r['to'] not in claims: continue
        if r['type']=='SUPPORTS': support[r['to']].append(r)
        if r['type']=='REFUTES': refute[r['to']].append(r)
    state={}
    for k in claims:
        if refute[k]: status='REFUTED'
        elif support[k]: status='SUPPORTED'
        else: status='UNRESOLVED'
        state[k]={'status':status,'support':support[k],'refute':refute[k]}
    return {'events':events,'relations':rels,'claims':claims,'state':state}

def facts(v):
    out={}
    for e in v['events']:
        out[e['id']]=e.get('facts',{})
    return out

def generate_actions(v):
    """Generate research actions from evidence motifs, not a supplied action list."""
    st=v['state']; f=facts(v); actions=[]

    # E0031 motif: late canonical convergence with few raw repeats.
    if 'E0031' in f and st['H_LATE_IDENTITY']['status']=='SUPPORTED':
        if f['E0031']['existing_frame_hit_rate'] > 0.25 and f['E0031']['raw_pair_repeat_rate'] < 0.05:
            actions.append({
                'id':'MAP_SCAN_COST','mode':'MAP','complexity':1,
                'why':'Late canonical reuse is common but raw repetition is rare; measure whether projection cost is dominated by traversal before changing representation.'})

    # E0032 motif: shallow scans reject heavyweight indexing; inspect composition closure.
    if 'E0032' in f and st['H_HEAVY_DAG']['status']=='REFUTED':
        actions.append({
            'id':'MAP_TAIL_REUSE','mode':'INSPECT_CLOSURE','complexity':1,
            'why':'Heavy representation is not justified; inspect whether existing shared suffixes already cache exact remaining projections.'})

    # E0033 motif: concrete same-frame reuse opportunity supports a causal separator.
    if 'E0033' in f and st['H_TAIL_COMPOSE']['status']=='SUPPORTED':
        rate=f['E0033']['exact_match_rate']; usable=f['E0033']['usable_fraction']
        if rate >= 0.05 and usable == 1.0:
            actions.append({
                'id':'TEST_TAIL_SPLICE','mode':'DISCRIMINATE','complexity':1,
                'composition_before_invention':True,
                'why':'Exact reusable tail projections are frequent and usable; test splice + ablation before quotient-index invention.'})

    # Representation escalation remains available only after the same-frame candidate is absent/null.
    if st['H_LATE_IDENTITY']['status']=='SUPPORTED' and st['H_RAW_CACHE']['status']=='REFUTED':
        actions.append({
            'id':'TEST_QUOTIENT_INDEX','mode':'REFRAME','complexity':4,
            'changes_representation':True,
            'why':'Late identity remains live; use only after cheaper closure/composition routes are exhausted.'})
    return actions

def rank(actions):
    def key(a):
        return (
            0 if a.get('composition_before_invention') else 1,
            1 if a.get('changes_representation') else 0,
            {'DISCRIMINATE':0,'INSPECT_CLOSURE':1,'MAP':2,'REFRAME':3}.get(a['mode'],4),
            a['complexity'],a['id'])
    return sorted(actions,key=key)

def choose(g,max_order):
    v=view(g,max_order); acts=rank(generate_actions(v))
    # Before E0033, do not leap over the diagnostic implied by current evidence.
    if max_order < 33:
        desired='MAP_SCAN_COST' if max_order==31 else 'MAP_TAIL_REUSE'
        for a in acts:
            if a['id']==desired: return a,v
    return (acts[0] if acts else None),v

if __name__=='__main__':
    g=load_graph()
    for o in (31,32,33):
        a,v=choose(g,o)
        print(o,a['id'] if a else None,{k:x['status'] for k,x in v['state'].items()})
