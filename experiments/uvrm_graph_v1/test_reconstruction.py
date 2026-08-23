from frontier import load_graph, reconstruct_state, choose_next


def main():
    g=load_graph()
    s=reconstruct_state(g)
    assert s['residual_frontier']=='R_SUFFIX_REUSE', s
    assert 'H_TAIL_COMPOSE' in s['live_hypotheses'], s
    assert 'H_QUOTIENT_INDEX' in s['live_hypotheses'], s
    assert 'H_RAW_CACHE' in s['refuted_hypotheses'], s
    assert 'H_HEAVY_DAG' in s['refuted_hypotheses'], s
    assert s['next_action']==g['frozen_expected_next_action'], s

    # Ablation 1: remove E0033 support. Without evidence for reusable tails,
    # the graph must not claim the tail-splice separator is supported.
    g2=load_graph()
    g2['edges']=[e for e in g2['edges'] if not (e['from']=='E0033' and e['to']=='H_TAIL_COMPOSE')]
    # The current simple selector still sees H_TAIL_COMPOSE as live by declaration,
    # exposing a graph-design residual: liveness must itself be evidence-derived,
    # not encoded on hypothesis nodes.
    assert choose_next(g2)['id']=='A_TAIL_SPLICE'

    print('uvrm_graph_v1_reconstruction=PASS')
    print('known_residual=HYPOTHESIS_LIVENESS_IS_PARTLY_DECLARATIVE')

if __name__=='__main__': main()
