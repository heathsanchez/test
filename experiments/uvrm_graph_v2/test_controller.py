from controller import load_graph, choose, view, generate_actions


def ids(xs): return {x['id'] for x in xs}

def main():
    g=load_graph()

    # Historical prequential reconstruction: no future evidence available.
    a31,_=choose(g,31); assert a31['id']==g['expected']['after_E0031']
    a32,_=choose(g,32); assert a32['id']==g['expected']['after_E0032']
    a33,v33=choose(g,33); assert a33['id']==g['expected']['after_E0033']

    # Status is evidence-derived, not declarative on hypothesis nodes.
    assert v33['state']['H_RAW_CACHE']['status']=='REFUTED'
    assert v33['state']['H_HEAVY_DAG']['status']=='REFUTED'
    assert v33['state']['H_TAIL_COMPOSE']['status']=='SUPPORTED'

    # No hindsight: E0033-derived action must not exist at E0032.
    assert 'TEST_TAIL_SPLICE' not in ids(generate_actions(view(g,32)))

    # Delete E0033 support relation: tail composition loses support and cannot be selected.
    g2=load_graph()
    g2['relations']=[r for r in g2['relations'] if not (r['from']=='E0033' and r['to']=='H_TAIL_COMPOSE')]
    acts2=generate_actions(view(g2,33))
    assert 'TEST_TAIL_SPLICE' not in ids(acts2)
    assert view(g2,33)['state']['H_TAIL_COMPOSE']['status']=='UNRESOLVED'

    # Delete raw-cache refutation: graph must cease claiming that branch is refuted.
    g3=load_graph()
    g3['relations']=[r for r in g3['relations'] if not (r['from']=='E0031' and r['to']=='H_RAW_CACHE')]
    assert view(g3,33)['state']['H_RAW_CACHE']['status']=='UNRESOLVED'

    # Perturb E0033 opportunity below the preregistered threshold: no splice separator.
    g4=load_graph()
    for e in g4['events']:
        if e['id']=='E0033': e['facts']['exact_match_rate']=0.01
    assert 'TEST_TAIL_SPLICE' not in ids(generate_actions(view(g4,33)))

    # Representation-level index remains available but is dominated by supported same-frame composition.
    all33=generate_actions(view(g,33)); assert 'TEST_QUOTIENT_INDEX' in ids(all33)
    assert choose(g,33)[0]['id']=='TEST_TAIL_SPLICE'

    print('uvrm_graph_v2=PASS')
    print('prequential_steps=3/3')
    print('evidence_ablation=PASS')
    print('no_hindsight=PASS')
    print('candidate_generation_from_graph=PASS')

if __name__=='__main__': main()
