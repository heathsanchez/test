use std::fs::File;
use std::io::{BufReader, Cursor};
use std::path::PathBuf;

use metatron_kernel::id::{ExprId, LevelId, NameId};
use metatron_kernel::parser::{ParseError, parse};
use metatron_kernel::syntax::Declaration;
use metatron_kernel::verdict::Verdict;

fn parse_fixture(name: &str) -> Result<metatron_kernel::parser::ParsedExport, ParseError> {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("fixtures")
        .join(name);
    parse(BufReader::new(File::open(path).unwrap()))
}

#[test]
fn parses_sparse_name_index() {
    let export = parse_fixture("sparse-name-index.ndjson").unwrap();
    assert!(export.names.contains(NameId(2)));
    assert!(!export.names.contains(NameId(1)));
}

#[test]
fn resolves_forward_referenced_levels() {
    let export = parse_fixture("level-index-out-of-order.ndjson")
        .unwrap()
        .resolve()
        .unwrap();
    assert_eq!(export.levels.len(), 3);
}

#[test]
fn missing_reference_is_malformed_not_unknown() {
    const MISSING_LEVEL: &str = concat!(
        "{\"meta\":{\"exporter\":{\"name\":\"handcrafted\",\"version\":\"0.1.0\"},",
        "\"format\":{\"version\":\"3.1.0\"},\"lean\":{\"githash\":\"test\",\"version\":\"4.29.1\"}}}\n",
        "{\"ie\":0,\"sort\":99}\n",
    );

    let error = parse(Cursor::new(MISSING_LEVEL))
        .unwrap()
        .resolve()
        .unwrap_err();
    assert!(matches!(error, ParseError::MissingLevel(LevelId(99))));
}

#[test]
fn preserves_unsupported_declaration_for_semantic_unknown() {
    let export = parse_fixture("unsupported-inductive.ndjson").unwrap();
    assert!(matches!(
        export.declarations.as_slice(),
        [Declaration::Inductive(block)] if block.types.is_empty()
            && block.constructors.is_empty()
            && block.recursors.is_empty()
    ));
    export.resolve().unwrap();
}

#[test]
fn parses_the_complete_empty_inductive_contract() {
    let bytes = include_bytes!("../evidence/residuals/G9-001/fixture.ndjson");
    let export = parse(Cursor::new(bytes)).unwrap().resolve().unwrap();
    let Declaration::Inductive(block) = &export.declarations[0] else {
        panic!("expected explicit inductive block");
    };
    assert_eq!(block.types.len(), 1);
    assert!(block.constructors.is_empty());
    assert_eq!(block.recursors.len(), 1);
    assert_eq!(block.types[0].name, NameId(1));
    assert_eq!(block.recursors[0].name, NameId(2));
    assert_eq!(block.recursors[0].all, vec![NameId(1)]);
    assert_eq!(block.recursors[0].num_motives, 1);
    assert!(!block.recursors[0].k);
}

#[test]
fn missing_nested_inductive_type_reference_is_malformed() {
    const MISSING_TYPE: &str = concat!(
        "{\"meta\":{\"exporter\":{\"name\":\"handcrafted\",\"version\":\"0.1.0\"},",
        "\"format\":{\"version\":\"3.1.0\"},\"lean\":{\"githash\":\"test\",\"version\":\"4.29.1\"}}}\n",
        "{\"in\":1,\"str\":{\"pre\":0,\"str\":\"I\"}}\n",
        "{\"inductive\":{\"types\":[{\"all\":[1],\"ctors\":[],\"isRec\":false,",
        "\"isReflexive\":false,\"isUnsafe\":false,\"levelParams\":[],\"name\":1,",
        "\"numIndices\":0,\"numNested\":0,\"numParams\":0,\"type\":99}],",
        "\"ctors\":[],\"recs\":[]}}\n",
    );
    let error = parse(Cursor::new(MISSING_TYPE))
        .unwrap()
        .resolve()
        .unwrap_err();
    assert!(matches!(error, ParseError::MissingExpr(ExprId(99))));
}

#[test]
fn parses_theorem_as_a_distinct_supported_declaration() {
    let bytes = include_bytes!("../evidence/residuals/G6-001/fixture.ndjson");
    let export = parse(Cursor::new(bytes)).unwrap().resolve().unwrap();
    assert!(matches!(
        export.declarations.as_slice(),
        [Declaration::Theorem {
            all,
            name: NameId(1),
            level_params,
            ty: ExprId(0),
            value: ExprId(2),
        }] if all == &[NameId(1)] && level_params.is_empty()
    ));
}

#[test]
fn missing_theorem_expression_reference_is_malformed() {
    const MISSING_THEOREM_VALUE: &str = concat!(
        "{\"meta\":{\"exporter\":{\"name\":\"handcrafted\",\"version\":\"0.1.0\"},",
        "\"format\":{\"version\":\"3.1.0\"},\"lean\":{\"githash\":\"test\",\"version\":\"4.29.1\"}}}\n",
        "{\"in\":1,\"str\":{\"pre\":0,\"str\":\"missingProof\"}}\n",
        "{\"ie\":0,\"sort\":0}\n",
        "{\"thm\":{\"all\":[1],\"levelParams\":[],\"name\":1,\"type\":0,\"value\":99}}\n",
    );

    let error = parse(Cursor::new(MISSING_THEOREM_VALUE))
        .unwrap()
        .resolve()
        .unwrap_err();
    assert!(matches!(error, ParseError::MissingExpr(ExprId(99))));
}

#[test]
fn missing_theorem_all_name_reference_is_malformed() {
    const MISSING_THEOREM_NAME: &str = concat!(
        "{\"meta\":{\"exporter\":{\"name\":\"handcrafted\",\"version\":\"0.1.0\"},",
        "\"format\":{\"version\":\"3.1.0\"},\"lean\":{\"githash\":\"test\",\"version\":\"4.29.1\"}}}\n",
        "{\"in\":1,\"str\":{\"pre\":0,\"str\":\"theoremName\"}}\n",
        "{\"ie\":0,\"sort\":0}\n",
        "{\"thm\":{\"all\":[99],\"levelParams\":[],\"name\":1,\"type\":0,\"value\":0}}\n",
    );

    let error = parse(Cursor::new(MISSING_THEOREM_NAME))
        .unwrap()
        .resolve()
        .unwrap_err();
    assert!(matches!(error, ParseError::MissingName(NameId(99))));
}

#[test]
fn run_separates_malformed_input_from_supported_and_unimplemented_semantics() {
    let valid = include_bytes!("fixtures/sparse-name-index.ndjson");
    let unsupported = include_bytes!("fixtures/unsupported-inductive.ndjson");
    assert_eq!(metatron_kernel::run(Cursor::new(valid)), Verdict::Accept);
    assert_eq!(
        metatron_kernel::run(Cursor::new(unsupported)),
        Verdict::Unknown
    );
    assert_eq!(
        metatron_kernel::run(Cursor::new(b"{not-json}\n")),
        Verdict::Error
    );
}

#[test]
fn unknown_structural_table_record_is_malformed() {
    const UNKNOWN_EXPR: &str = concat!(
        "{\"meta\":{\"exporter\":{\"name\":\"handcrafted\",\"version\":\"0.1.0\"},",
        "\"format\":{\"version\":\"3.1.0\"},\"lean\":{\"githash\":\"test\",\"version\":\"4.29.1\"}}}\n",
        "{\"ie\":0,\"futureExpr\":{}}\n",
    );
    let error = parse(Cursor::new(UNKNOWN_EXPR)).unwrap_err();
    assert!(matches!(error, ParseError::Malformed { line: 2, .. }));
}
