from controller import (
    Budget, ResearchState, CandidateAction, choose_next,
    robust_worst_case_elimination, update_hypotheses, admit_import
)


def F(*xs): return frozenset(xs)
def A(name, lifecycle, mode, predictions, **kw):
    return CandidateAction(name, lifecycle, mode, tuple(predictions), **kw)

B = Budget(10,10,10,10000,100)


def main():
    H = ('SEARCH','REPRESENTATION','SURROGATE')

    # Uncertain overlapping predictions do not get fake discrimination credit.
    vague = A('vague','DISCOVER','EXPLOIT',[F('x','y'),F('x','y'),F('x','y')])
    sharp = A('sharp','DISCOVER','EXPLOIT',[F('x'),F('y'),F('z')])
    assert robust_worst_case_elimination(vague,3) == 0
    assert robust_worst_case_elimination(sharp,3) == 2
    d = choose_next(ResearchState('sep',H),B,[vague,sharp])
    assert (d.kind,d.value) == ('ACTION','sharp')

    # Budget is a hard feasibility boundary, not a cosmetic tie-break.
    huge = A('huge','DISCOVER','EXPLOIT',[F('x'),F('y'),F('z')],model_calls=99)
    modest = A('modest','DISCOVER','EXPLOIT',[F('x'),F('x'),F('y')],model_calls=1)
    assert choose_next(ResearchState('budget',H),B,[huge,modest]).value == 'modest'

    # Apparatus failure gates semantic research.
    repair = A('repair','REPAIR','INSPECT',[F('r'),F('r'),F('r')],verifier_calls=1)
    semantic = A('semantic','DISCOVER','DISCRIMINATE',[F('x'),F('y'),F('z')])
    assert choose_next(ResearchState('infra',H,apparatus_valid=False),B,[semantic,repair]).value == 'repair'

    # Closure-before-invention survives even when invention looks more decisive.
    inspect = A('inspect','DISCOVER','INSPECT',[F('same'),F('same'),F('other')],inspects_existing_closure=True)
    invent = A('invent','DISCOVER','REFRAME',[F('a'),F('b'),F('c')],changes_representation=True)
    assert choose_next(ResearchState('closure',H,existing_structure_unknown=True),B,[invent,inspect]).value == 'inspect'

    # Repeated zero-information local actions trigger altitude change; an outside
    # import changes candidate generation only when such a trigger already exists.
    zero = A('zero','DISCOVER','EXPLOIT',[F('x'),F('x'),F('x')])
    s = ResearchState('stall',H,repeated_local_failures=3)
    assert choose_next(s,B,[zero]).value == 'REFRAME'
    si = ResearchState('stall_import',H,repeated_local_failures=3,external_import_active=True)
    assert choose_next(si,B,[zero]).value == 'REFRAME_WITH_IMPORT'

    # Surprise is preserved as a model miss, not forced into a preferred rival.
    a = A('prediction',["DISCOVER"][0],'DISCRIMINATE',[F('x'),F('y'),F('z')])
    kept, surprise = update_hypotheses(ResearchState('surprise',H),a,'q')
    assert surprise and kept == H
    narrowed, surprise = update_hypotheses(ResearchState('normal',H),a,'y')
    assert not surprise and narrowed == ('REPRESENTATION',)

    # Success is not terminal: if a target passes and a control exists, attack it.
    control = A('ablate','VERIFY','DISCRIMINATE',[F('same'),F('different'),F('same')],is_ablation_or_control=True)
    more_search = A('more_search','DISCOVER','EXPLOIT',[F('a'),F('b'),F('c')])
    assert choose_next(ResearchState('green',H,target_verified=True),B,[more_search,control]).value == 'ablate'

    # Import admission requires trigger + structural mapping + differential test.
    base = ResearchState('import',H,external_import_active=True,repeated_local_failures=2)
    assert admit_import(base,'ANALOGUE',True,True) == H + ('ANALOGUE',)
    assert admit_import(base,'HANDWAVE',True,False) == H
    no_trigger = ResearchState('no_trigger',H,external_import_active=True)
    assert admit_import(no_trigger,'ANALOGUE',True,True) == H

    print('controller_v4_invariants=PASS')

if __name__ == '__main__': main()
