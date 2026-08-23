from equivalence import Probe, Move, EquivalenceProtocol, preoutcome_equivalent, equivalence_classes, source_substitution

def F(*xs): return frozenset(xs)

P=EquivalenceProtocol((Probe('semantic_effect'),Probe('resource_effect'),Probe('transfer_effect')),True)

def main():
    human=Move('human_tail_splice','HUMAN',(F('same_semantics'),F('faster'),F('transfers')))
    residual=Move('residual_parent_reuse','RESIDUAL',(F('same_semantics'),F('faster'),F('transfers')))
    local=Move('local_cache_resize','LOCAL',(F('same_semantics'),F('faster','neutral'),F('fails_transfer')))

    # 1. Different syntax/source can be equivalent when frozen behavior matches.
    assert preoutcome_equivalent(human,residual,P)
    assert not preoutcome_equivalent(human,local,P)

    # 2. Source substitution is attributed only through pre-outcome equivalence.
    sub=source_substitution([human,residual,local],P,'HUMAN')
    assert sub == [(('human_tail_splice','residual_parent_reuse'),True)]

    # 3. Protected-result access disqualifies post-hoc equivalence claims.
    hindsight=Move('posthoc_clone','STRUCTURAL',human.signature,protected_outcome_access=True)
    assert not preoutcome_equivalent(human,hindsight,P)
    cs=equivalence_classes([human,hindsight],P)
    assert len(cs)==1 and cs[0]==[human]

    # 4. An unfrozen probe language cannot support attribution.
    unfrozen=EquivalenceProtocol(P.probes,False)
    assert not preoutcome_equivalent(human,residual,unfrozen)

    # 5. Missing probe coverage is not equivalent by convenience.
    short=Move('short','IMPORT',(F('same_semantics'),F('faster')))
    assert not preoutcome_equivalent(human,short,P)

    # 6. Same terminal success is insufficient if pre-outcome signatures differ.
    # Both could eventually solve the task, but V9 does not merge them unless the
    # frozen behavioral probe suite already licensed that merge.
    alt=Move('different_mechanism','STRUCTURAL',(F('same_semantics'),F('neutral'),F('transfers')))
    assert not preoutcome_equivalent(human,alt,P)

    print('controller_v9_equivalence_invariants=PASS')

if __name__=='__main__': main()
