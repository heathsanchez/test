from controller import ResearchState, controller, local_only

# Retrospective smoke cases. Expected pairs are historical interpretations;
# they are not used by controller.py. V2 exists to test the factorization
# lifecycle x epistemic-mode suggested by V1's two out-of-vocabulary misses.
CASES = [
    # SAIR
    (ResearchState('sair_effect_atlas', residual_sharp=False, repeated_local_failures=3, conditional_regimes=True, competing_explanations=2), ('DISCOVER','MAP')),
    (ResearchState('sair_retro_demod', repeated_local_failures=2, conditional_regimes=True, competing_explanations=2, deciding_test_ready=True), ('VERIFY','DISCRIMINATE')),
    (ResearchState('sair_operator_attribution', residual_sharp=False, repeated_local_failures=3, conditional_regimes=True, competing_explanations=3), ('DISCOVER','MAP')),
    (ResearchState('sair_dependency_failure', apparatus_valid=False, existing_structure_unknown=True), ('REPAIR','INSPECT')),
    (ResearchState('sair_official_800', competing_explanations=2, deciding_test_ready=True), ('VERIFY','DISCRIMINATE')),

    # Triskelion
    (ResearchState('tri_world_map', residual_sharp=False), ('DISCOVER','MAP')),
    (ResearchState('tri_staging_separator', repeated_local_failures=2, competing_explanations=2, deciding_test_ready=True), ('VERIFY','DISCRIMINATE')),
    (ResearchState('tri_carry_repair', repeated_local_failures=2, competing_explanations=2, deciding_test_ready=True), ('VERIFY','DISCRIMINATE')),
    (ResearchState('tri_middle_digit_map', residual_sharp=False, repeated_local_failures=3, conditional_regimes=True, competing_explanations=2), ('DISCOVER','MAP')),
    (ResearchState('tri_internal_state_separator', repeated_local_failures=3, conditional_regimes=True, competing_explanations=3, deciding_test_ready=True), ('VERIFY','DISCRIMINATE')),

    # MathGraph
    (ResearchState('mg_target_independent', repeated_local_failures=2, conditional_regimes=True, competing_explanations=2), ('DISCOVER','REFRAME')),
    (ResearchState('mg_control_repair', competing_explanations=2, deciding_test_ready=True), ('VERIFY','DISCRIMINATE')),
    (ResearchState('mg_coordinate_free', repeated_local_failures=2, conditional_regimes=True, competing_explanations=2), ('DISCOVER','REFRAME')),
    (ResearchState('mg_generic_dsl', repeated_local_failures=2, conditional_regimes=True, competing_explanations=2), ('DISCOVER','REFRAME')),
    (ResearchState('mg_cross_dsl_transfer', competing_explanations=2, deciding_test_ready=True, transfer_candidate_ready=True), ('TRANSFER','DISCRIMINATE')),
    (ResearchState('mg_second_generation', repeated_local_failures=2, conditional_regimes=True, competing_explanations=2), ('DISCOVER','REFRAME')),

    # Additional Triskelion meta-controller episodes not in V1 replay
    (ResearchState('tri_v133_to_v134', repeated_local_failures=2, competing_explanations=2, deciding_test_ready=True), ('VERIFY','DISCRIMINATE')),
    (ResearchState('tri_v149_adapter_repair', apparatus_valid=False, competing_explanations=4, deciding_test_ready=True), ('REPAIR','DISCRIMINATE')),
    (ResearchState('tri_rbs_prospective_self_test', competing_explanations=5, deciding_test_ready=True), ('VERIFY','DISCRIMINATE')),
]

def counterfactual_tests():
    # Tests that lifecycle and epistemic mode are genuinely factorized rather
    # than aliases for one flat label list.
    base = ResearchState('base')
    assert controller(base) == ('DISCOVER','EXPLOIT')
    assert controller(ResearchState('repair', apparatus_valid=False)) == ('REPAIR','EXPLOIT')
    assert controller(ResearchState('repair_map', apparatus_valid=False, residual_sharp=False)) == ('REPAIR','MAP')
    assert controller(ResearchState('transfer_map', transfer_candidate_ready=True, residual_sharp=False)) == ('TRANSFER','MAP')
    assert controller(ResearchState('transfer_test', transfer_candidate_ready=True, competing_explanations=2, deciding_test_ready=True)) == ('TRANSFER','DISCRIMINATE')
    assert controller(ResearchState('retain_attack', retention_candidate_ready=True, competing_explanations=2, deciding_test_ready=True)) == ('RETAIN','DISCRIMINATE')
    assert controller(ResearchState('inspect', existing_structure_unknown=True, deciding_test_ready=True, competing_explanations=3)) == ('VERIFY','INSPECT')
    # External imports do not force a reframe by themselves.
    assert controller(ResearchState('import_only', external_import_active=True)) == ('DISCOVER','EXPLOIT')
    assert controller(ResearchState('import_triggered', external_import_active=True, repeated_local_failures=2)) == ('DISCOVER','REFRAME')


def main():
    rows=[]
    for s, expected in CASES:
        got=controller(s); local=local_only(s)
        rows.append((s.name, expected, got, local, got==expected, local==expected))
    n=len(rows)
    c=sum(r[4] for r in rows)/n
    b=sum(r[5] for r in rows)/n
    print('case,expected,controller,local_only,controller_ok,local_ok')
    for r in rows:
        print(f'{r[0]},{r[1][0]}+{r[1][1]},{r[2][0]}+{r[2][1]},{r[3][0]}+{r[3][1]},{r[4]},{r[5]}')
    print(f'n={n}')
    print(f'controller_pair_accuracy={c:.3f}')
    print(f'local_pair_accuracy={b:.3f}')
    counterfactual_tests()
    print('counterfactual_factorization_tests=PASS')
    assert c > b
    assert c == 1.0

if __name__ == '__main__': main()
