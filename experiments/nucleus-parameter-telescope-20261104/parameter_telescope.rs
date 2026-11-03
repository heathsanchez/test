use std::io::Cursor;
use metatron_kernel::verdict::Verdict;
fn run(source:&str)->Verdict{metatron_kernel::run(Cursor::new(source))}
#[test]fn two_parameters_three_fields(){assert_eq!(run(include_str!("fixtures/parameter-telescope/two.ndjson")),Verdict::Accept);}
#[test]fn dependent_parameters_and_fields(){assert_eq!(run(include_str!("fixtures/parameter-telescope/dependent.ndjson")),Verdict::Accept);}
#[test]fn sixty_four_parameters_and_fields(){assert_eq!(run(include_str!("fixtures/parameter-telescope/boundary.ndjson")),Verdict::Accept);}
#[test]fn larger_field_universe_declines(){assert_ne!(run(include_str!("fixtures/parameter-telescope/field-too-large.ndjson")),Verdict::Accept);}
#[test]fn altered_parameter_domains_decline(){for s in [include_str!("fixtures/parameter-telescope/ctor-parameter-domain.ndjson"),include_str!("fixtures/parameter-telescope/rhs-parameter-annotation.ndjson")]{assert_ne!(run(s),Verdict::Accept);}}
#[test]fn altered_motive_minor_and_field_annotations_decline(){for s in [include_str!("fixtures/parameter-telescope/rhs-motive-annotation.ndjson"),include_str!("fixtures/parameter-telescope/rhs-minor-annotation.ndjson"),include_str!("fixtures/parameter-telescope/rhs-field-shift.ndjson")]{assert_ne!(run(s),Verdict::Accept);}}
#[test]fn metadata_and_hidden_recursion_decline(){for s in [include_str!("fixtures/parameter-telescope/wrong-parameter-count.ndjson"),include_str!("fixtures/parameter-telescope/colliding-motive-universe.ndjson"),include_str!("fixtures/parameter-telescope/recursive-function-domain.ndjson")]{assert_ne!(run(s),Verdict::Accept);}}
#[test]fn overlapping_four_parameter_depth_and_dag_are_bounded(){for s in [include_str!("fixtures/parameter-telescope/excessive-depth.ndjson"),include_str!("fixtures/parameter-telescope/expanded-dag.ndjson")]{assert_ne!(run(s),Verdict::Accept);}}
