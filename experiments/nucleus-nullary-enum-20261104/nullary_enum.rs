use std::io::Cursor;
use metatron_kernel::verdict::Verdict;
fn run(s:&str)->Verdict{metatron_kernel::run(Cursor::new(s))}
#[test]fn three_nullary_alternatives_and_typed_numeral_probes(){assert_eq!(run(include_str!("fixtures/nullary-enum/enum3.ndjson")),Verdict::Accept);}
#[test]fn sixteen_alternatives_boundary(){assert_eq!(run(include_str!("fixtures/nullary-enum/enum16.ndjson")),Verdict::Accept);}
#[test]fn seventeenth_alternative_remains_outside_scope(){assert_eq!(run(include_str!("fixtures/nullary-enum/enum17.ndjson")),Verdict::Unknown);}
#[test]fn exact_minor_order_and_annotations_are_mandatory(){for s in [include_str!("fixtures/nullary-enum/wrong-branch.ndjson"),include_str!("fixtures/nullary-enum/wrong-rule-annotation.ndjson")]{assert_ne!(run(s),Verdict::Accept);}}
#[test]fn canonical_motive_universe_is_mandatory(){for s in [include_str!("fixtures/nullary-enum/motive-v.ndjson"),include_str!("fixtures/nullary-enum/motive-hierarchical.ndjson")]{assert_ne!(run(s),Verdict::Accept);}}
#[test]fn constructor_and_rule_metadata_do_not_supply_authority(){for s in [include_str!("fixtures/nullary-enum/wrong-index.ndjson"),include_str!("fixtures/nullary-enum/wrong-constructor-result.ndjson"),include_str!("fixtures/nullary-enum/wrong-field-count.ndjson"),include_str!("fixtures/nullary-enum/wrong-k.ndjson")]{assert_ne!(run(s),Verdict::Accept);}}
#[test]fn all_rule_annotations_receive_the_bounded_preflight(){for s in [include_str!("fixtures/nullary-enum/deep-rule-annotation.ndjson"),include_str!("fixtures/nullary-enum/dag-rule-annotation.ndjson")]{assert_ne!(run(s),Verdict::Accept);}}
