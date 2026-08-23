from frontier import load_graph, reconstruct_state, choose_next


def main():
    g=load_graph()
    s=reconstruct_state(g)
    assert s['residual_frontier']=='R_SUFFIX_REUSE', s
    assert 'H_TAIL_COMPOSE' in s['supported_hypotheses'], s
    assert 'H_QUOTIENT_INDEX' in s['live_hypotheses'], s
    assert 'H_RAW_CACHE' in s['refuted_hypotheses'], s
    assert 'H_HEAVY_DAG' in s['refuted_hypotheses'], s
    assert s['next_action']==g['frozen_expected_next_action'], s

    # Evidence ablation: if the E0033 support edge disappears, the controller
    # must stop treating the splice as the evidence-backed next separator.
    g2=load_graph()
    g2['edges']=[e for e in g2['edges'] if not (e['from']=='E0033' and e['to']=='H_TAIL_COMPOSE')]
    s2=reconstruct_state(g2)
    assert 'H_TAIL_COMPOSE' not in s2['supported_hypotheses'], s2
    assert choose_next(g2)['id']!='A_TAIL_SPLICE', s2

    # Negative-law ablation: if the evidence refuting raw-cache repair is hidden,
    # that branch must become live again rather than remaining silently rejected.
    g3=load_graph()
    g3['edges']=[e for e in g3['edges'] if not (e['from']=='E0031' and e['to']=='H_RAW_CACHE' and e['type']=='REFUTES')]
    s3=reconstruct_state(g3)
    assert 'H_RAW_CACHE' not in s3['refuted_hypotheses'], s3

    print('uvrm_graph_v1_reconstruction=PASS')
    print('graph_only_next=A_TAIL_SPLICE')
    print('evidence_ablation_changes_next=PASS')
    print('negative_law_ablation_reopens_branch=PASS')

if __name__=='__main__': main()
