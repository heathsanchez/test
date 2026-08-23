from tournament import GeneratorSpec, Proposal, ExecutedResult, provenance_map, first_discovery, generator_metrics, ablation_reach, substitution_matrix

S=(
 GeneratorSpec('LOCAL','local',('nearby','deeper'),4),
 GeneratorSpec('RESIDUAL','residual',('residual_map','separator'),4),
 GeneratorSpec('STRUCTURAL','structural',('analogy','cross_domain'),4),
 GeneratorSpec('IMPORT','import',('paper','comment'),4),
 GeneratorSpec('HUMAN','human',('injection',),4),
)


def main():
    # Equivalent moves from different sources share canonical identity rather than
    # being counted as independent discoveries.
    P=[
      Proposal('HUMAN','injection','tail_splice',1,1,audited_split=.8),
      Proposal('RESIDUAL','separator','tail_splice',3,1,audited_split=.8),
      Proposal('LOCAL','nearby','cache_resize',1,1,audited_split=.2),
      Proposal('IMPORT','paper','new_dag',2,1,audited_split=.5),
    ]
    R=[ExecutedResult('tail_splice',True,True,True,True), ExecutedResult('cache_resize',False,False), ExecutedResult('new_dag',False,False)]
    prov=provenance_map(S,P)
    assert len(prov['tail_splice'])==2
    assert first_discovery(prov,'tail_splice')==('HUMAN',)

    # First arrival and unique necessity are different. Human gets first-discovery
    # credit here but is substitutable because RESIDUAL independently found the same move.
    sub=substitution_matrix(S,P,R)
    assert sub['HUMAN']['own_deciding']==1 and sub['HUMAN']['substitutable']==1 and sub['HUMAN']['unique_deciding']==0
    assert ablation_reach(S,P,R,'HUMAN')

    # If the only deciding move is human-only, human ablation destroys reachability.
    P2=[Proposal('HUMAN','injection','hard_reframe',1,1),Proposal('LOCAL','nearby','patch',1,1)]
    R2=[ExecutedResult('hard_reframe',True,True,True,True),ExecutedResult('patch',True,False)]
    assert not ablation_reach(S,P2,R2,'HUMAN')
    assert substitution_matrix(S,P2,R2)['HUMAN']['unique_deciding']==1

    # Protected leakage cannot earn attribution.
    P3=P2+[Proposal('IMPORT','paper','hard_reframe',0,1,protected_leakage=True)]
    assert substitution_matrix(S,P3,R2)['IMPORT']['own_deciding']==0

    # Undeclared slots and over-budget proposals are excluded.
    P4=[Proposal('LOCAL','bogus','x',1,1), Proposal('LOCAL','nearby','a',1,3), Proposal('LOCAL','deeper','b',2,3)]
    prov4=provenance_map(S,P4)
    assert 'x' not in prov4 and 'a' in prov4 and 'b' not in prov4

    # Metrics preserve causal gates rather than conflating proposal with success.
    m=generator_metrics(S,P,R)
    assert m['HUMAN']['deciding_moves']==1 and m['HUMAN']['attack_survivors']==1 and m['HUMAN']['transfer_survivors']==1
    assert m['IMPORT']['deciding_moves']==0

    # Simultaneous equivalent discovery produces shared first-discovery credit.
    P5=[Proposal('LOCAL','nearby','z',2,1),Proposal('STRUCTURAL','analogy','z',2,1)]
    assert first_discovery(provenance_map(S,P5),'z')==('LOCAL','STRUCTURAL')

    print('controller_v8_tournament_invariants=PASS')

if __name__=='__main__': main()
