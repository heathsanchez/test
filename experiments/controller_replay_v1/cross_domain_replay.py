from run import Snapshot, controller, local_only

# Frozen controller from run.py is NOT modified here.
# These retrospective episodes are selected from three independent recent programmes.
# Labels describe the next research mode evidenced by the subsequent repository sequence.
# Some labels are intentionally outside V1's action vocabulary to test controller completeness.

CASES = [
    # SAIR / equational-theories-lean-stage2
    ('sair_pre_effect_atlas', Snapshot('sair_pre_effect_atlas','five residuals',3,False,False,True,2,False,'MAP'), '25c605b'),
    ('sair_pre_retro_demod', Snapshot('sair_pre_retro_demod','rule handoff',2,True,False,True,2,True,'DISCRIMINATE'), 'c29cdff'),
    ('sair_pre_operator_attribution', Snapshot('sair_pre_operator_attribution','mechanism unclear',3,False,False,True,3,False,'MAP'), 'e0e268e'),
    ('sair_proxy_dependency_failure', Snapshot('sair_proxy_dependency_failure','infrastructure',0,True,False,False,1,False,'REPAIR_INFRA'), 'b80b163'),
    ('sair_pre_official_800', Snapshot('sair_pre_official_800','candidate stable',1,True,False,False,2,True,'DISCRIMINATE'), 'dcf8ead'),

    # Triskelion
    ('tri_pre_world_map', Snapshot('tri_pre_world_map','world structure unclear',1,False,False,False,1,False,'MAP'), '0293907'),
    ('tri_pre_staging_separator', Snapshot('tri_pre_staging_separator','staging hypothesis',2,True,False,False,2,True,'DISCRIMINATE'), 'aa0bc74'),
    ('tri_pre_carry_repair', Snapshot('tri_pre_carry_repair','carry-state hypothesis',2,True,False,False,2,True,'DISCRIMINATE'), 'df482bf'),
    ('tri_pre_middle_digit_map', Snapshot('tri_pre_middle_digit_map','post-carry residual unclear',3,False,False,True,2,False,'MAP'), '386be17'),
    ('tri_pre_internal_state_separator', Snapshot('tri_pre_internal_state_separator','aggregation/internal-state rival',3,True,False,True,3,True,'DISCRIMINATE'), 'd5d664c'),

    # Metalogic Labs MathGraph / Daniel lineage
    ('mg_pre_v2_target_independent', Snapshot('mg_pre_v2_target_independent','target dependence scaffold',2,True,False,True,2,False,'REFRAME'), '5fab0d4'),
    ('mg_pre_v21_control_repair', Snapshot('mg_pre_v21_control_repair','audit defect',1,True,False,False,2,True,'DISCRIMINATE'), 'e6f857b'),
    ('mg_pre_v3_coordinate_free', Snapshot('mg_pre_v3_coordinate_free','coordinate scaffold',2,True,False,True,2,False,'REFRAME'), '10431a7'),
    ('mg_pre_v4_generic_dsl', Snapshot('mg_pre_v4_generic_dsl','representation language scaffold',2,True,False,True,2,False,'REFRAME'), '71b9ba0'),
    ('mg_pre_v5_cross_dsl_transfer', Snapshot('mg_pre_v5_cross_dsl_transfer','law identity across DSL',1,True,False,True,2,True,'TRANSFER'), '9b43530'),
    ('mg_pre_v6_second_generation', Snapshot('mg_pre_v6_second_generation','second-generation constructibility',2,True,False,True,2,False,'REFRAME'), 'c916863'),
]

SUPPORTED = {'EXPLOIT','INSPECT_CLOSURE','MAP','REFRAME','DISCRIMINATE'}

def main():
    rows=[]
    for domain_case, s, anchor in CASES:
        c=controller(s); b=local_only(s)
        rows.append((domain_case, anchor, s.expected, c, b, c==s.expected, b==s.expected, s.expected in SUPPORTED))

    n=len(rows)
    cacc=sum(r[5] for r in rows)/n
    bacc=sum(r[6] for r in rows)/n
    supported=[r for r in rows if r[7]]
    sacc=sum(r[5] for r in supported)/len(supported)
    sbacc=sum(r[6] for r in supported)/len(supported)
    oov=[r for r in rows if not r[7]]

    print('case,anchor,expected,controller,local_only,controller_ok,local_ok,supported_label')
    for r in rows: print(','.join(map(str,r)))
    print(f'n={n}')
    print(f'controller_accuracy_all={cacc:.3f}')
    print(f'local_only_accuracy_all={bacc:.3f}')
    print(f'controller_accuracy_supported={sacc:.3f}')
    print(f'local_only_accuracy_supported={sbacc:.3f}')
    print(f'unsupported_mode_rate={len(oov)/n:.3f}')
    print('unsupported_modes=' + ','.join(sorted({r[2] for r in oov})))

    # This is a completeness test, not a pass-at-all-costs test.
    # Require only that the frozen controller beats local-only on labels it can express.
    assert sacc > sbacc

if __name__ == '__main__': main()
