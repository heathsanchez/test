from controller import ResearchState, CandidateAction, choose_action, worst_case_elimination, import_is_admissible


def A(name, lifecycle, mode, preds, **kw):
    return CandidateAction(name, lifecycle, mode, tuple(preds), **kw)


def main():
    H = ('SEARCH_ONLY','REPRESENTATION','INFRASTRUCTURE','SURROGATE')

    # 1. Prefer a true separator to a flashy action that predicts the same thing
    # under every live rival, even if the flashy action is cheaper.
    s = ResearchState('separator')
    flashy = A('flashy_patch','DISCOVER','EXPLOIT',('x','x','x','x'))
    separator = A('small_separator','DISCOVER','EXPLOIT',('a','b','c','d'), verifier_calls=1)
    assert worst_case_elimination(flashy.predictions) == 0
    assert worst_case_elimination(separator.predictions) == 3
    assert choose_action(s,H,[flashy,separator]).name == 'small_separator'

    # 2. Apparatus invalidity blocks semantic experiments regardless of apparent
    # information value. Repair is an upstream gate, not another hypothesis.
    s = ResearchState('infra', apparatus_valid=False)
    semantic = A('semantic_test','DISCOVER','DISCRIMINATE',('a','b','c','d'))
    repair = A('repair_runner','REPAIR','INSPECT',('r','r','r','r'), verifier_calls=1)
    assert choose_action(s,H,[semantic,repair]).name == 'repair_runner'

    # 3. Closure before invention: when the allegedly missing object may already
    # exist, a closure inspection outranks a representation-changing separator.
    s = ResearchState('closure', existing_structure_unknown=True)
    invent = A('new_dag','DISCOVER','REFRAME',('a','b','c','d'), changes_representation=True)
    inspect = A('inspect_existing','DISCOVER','INSPECT',('a','b','b','b'), inspects_existing_closure=True)
    assert choose_action(s,H,[invent,inspect]).name == 'inspect_existing'

    # 4. Once closure is known, stronger discrimination beats mode aesthetics.
    s = ResearchState('known_closure', repeated_local_failures=3)
    reframe_weak = A('pretty_reframe','DISCOVER','REFRAME',('a','a','b','b'))
    local_strong = A('local_separator','DISCOVER','EXPLOIT',('a','b','c','d'))
    assert choose_action(s,H,[reframe_weak,local_strong]).name == 'local_separator'

    # 5. On equal epistemic value, stay with the warranted mode, then choose the
    # lower-scaffold/lower-risk/lower-cost action. This prevents novelty bias.
    s = ResearchState('tie', repeated_local_failures=2)
    local = A('local_equal','DISCOVER','EXPLOIT',('a','a','b','b'))
    reframe = A('reframe_equal','DISCOVER','REFRAME',('a','a','b','b'))
    assert choose_action(s,H,[local,reframe]).name == 'reframe_equal'
    reframe_big = A('reframe_big','DISCOVER','REFRAME',('a','a','b','b'), scaffold_additions=2)
    reframe_small = A('reframe_small','DISCOVER','REFRAME',('a','a','b','b'), scaffold_additions=0)
    assert choose_action(s,H,[reframe_big,reframe_small]).name == 'reframe_small'

    # 6. An external paper/comment/analogy is inert by itself; it becomes an
    # admissible source of candidate reframes only after an internal trigger.
    assert not import_is_admissible(ResearchState('import_only', external_import_active=True))
    assert import_is_admissible(ResearchState('import_stall', external_import_active=True, repeated_local_failures=2))
    assert import_is_admissible(ResearchState('import_map', external_import_active=True, residual_sharp=False))

    # 7. Prediction bookkeeping cannot silently omit rivals.
    try:
        choose_action(ResearchState('bad'), H, [A('bad','DISCOVER','EXPLOIT',('x','y'))])
    except ValueError:
        pass
    else:
        raise AssertionError('prediction/hypothesis mismatch must fail')

    print('v3_adversarial_invariants=PASS')


if __name__ == '__main__':
    main()
