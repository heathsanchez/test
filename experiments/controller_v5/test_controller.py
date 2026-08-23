from controller import (
    Budget, ResearchState, ImportArtifact, CandidateAction, choose_next,
    robust_worst_case_elimination, adversarially_expand_predictions,
    buffer_import, update_hypotheses
)


def F(*xs): return frozenset(xs)
def A(name,lifecycle,mode,preds,**kw):
    return CandidateAction(name,lifecycle,mode,tuple(preds),**kw)

B=Budget(10,10,10,10000,100)
H=('SEARCH','REPRESENTATION','SURROGATE')


def main():
    # 1. The critical V5 fix: failure to GENERATE a separator is not evidence
    # for reframing while the candidate-generation boundary remains open.
    zero=A('zero','DISCOVER','EXPLOIT',[F('x'),F('x'),F('x')])
    open_s=ResearchState('open_search',H,repeated_local_failures=5,candidate_generation_exhausted=False)
    assert choose_next(open_s,B,[zero]).value == 'EXPAND_CANDIDATES'
    closed_s=ResearchState('closed_search',H,repeated_local_failures=5,candidate_generation_exhausted=True)
    assert choose_next(closed_s,B,[zero]).value == 'REFRAME'

    # 2. An independent prediction critic can only widen possibilities. A
    # self-scored perfect separator loses credit when the critic finds overlaps.
    self_scored=A('claimed_separator','DISCOVER','DISCRIMINATE',[F('a'),F('b'),F('c')])
    assert robust_worst_case_elimination(self_scored,3)==2
    audited=adversarially_expand_predictions(self_scored,(F('b'),F('a'),F('a')))
    assert robust_worst_case_elimination(audited,3)==1

    # 3. External imports may arrive before a stall. Good imports are buffered as
    # candidate hypotheses but do not force REFRAME or belief update by arrival.
    art=ImportArtifact('paper','TRANSFER_SCOPE',True,True)
    newH=buffer_import(H,art)
    assert newH == H+('TRANSFER_SCOPE',)
    weak=ImportArtifact('interesting_but_vague','HANDWAVE',True,False)
    assert buffer_import(H,weak)==H

    # 4. An import-derived action can win BEFORE a stall if it actually separates
    # more live rivals. Source is provenance, not a novelty penalty or bonus.
    hi=H+('TRANSFER_SCOPE',)
    s=ResearchState('early_import_use',hi)
    local=A('local','DISCOVER','EXPLOIT',[F('x'),F('x'),F('y'),F('x')],source='local')
    imported=A('paper_test','DISCOVER','EXPLOIT',[F('a'),F('b'),F('c'),F('d')],source='import:paper')
    assert choose_next(s,B,[local,imported]).value=='paper_test'

    # 5. Strong local separator still beats an imported reframe when it carries
    # more robust information. The controller does not reward novelty.
    s=ResearchState('no_novelty_bonus',H,repeated_local_failures=3)
    import_reframe=A('import_reframe','DISCOVER','REFRAME',[F('a'),F('a'),F('b')],source='import')
    local_sep=A('local_sep','DISCOVER','EXPLOIT',[F('a'),F('b'),F('c')],source='local')
    assert choose_next(s,B,[import_reframe,local_sep]).value=='local_sep'

    # 6. Misaligned proxy/objective is upstream of research optimization.
    s=ResearchState('wrong_scoreboard',H,objective_metric_aligned=False)
    assert choose_next(s,B,[local_sep]).value=='AUDIT_GOAL_METRIC'

    # 7. Surprise remains a hypothesis-model miss, not forced inference.
    kept,surprise=update_hypotheses(ResearchState('surprise',H),self_scored,'unpredicted')
    assert surprise and kept==H

    # 8. Empty action pool likewise cannot be called representation failure when
    # generator search has not been exhausted.
    assert choose_next(open_s,B,[]).value=='EXPAND_CANDIDATES'

    print('controller_v5_invariants=PASS')

if __name__=='__main__': main()
