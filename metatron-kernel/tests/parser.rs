use std::fs::File;
use std::io::{BufReader, Cursor};
use std::path::PathBuf;

use metatron_kernel::id::{LevelId, NameId};
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
        [Declaration::Unsupported { tag }] if tag == "inductive"
    ));
    export.resolve().unwrap();
}

#[test]
fn run_separates_malformed_input_from_unimplemented_semantics() {
    let valid = include_bytes!("fixtures/sparse-name-index.ndjson");
    assert_eq!(metatron_kernel::run(Cursor::new(valid)), Verdict::Unknown);
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
