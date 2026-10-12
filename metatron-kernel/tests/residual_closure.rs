use std::fs::File;
use std::io::BufReader;
use std::path::PathBuf;

use metatron_kernel::verdict::Verdict;

#[test]
#[ignore = "requires pinned Arena artifact 11272848230 in NUCLEUS_FROZEN196"]
fn all_seven_complete_positive_exports_accept() {
    let root = PathBuf::from(std::env::var("NUCLEUS_FROZEN196").expect("pinned corpus path"));
    for name in [
        "init-prelude", "perf/grind-ring-5", "perf/magma-list-pair-n7",
        "perf/magma-list-pair-n21", "perf/magma-list-deep-n21",
        "perf/magma-list-deep-n36", "perf/fueled-chain",
    ] {
        let path = root.join("good").join(format!("{name}.ndjson"));
        let actual = std::thread::Builder::new().stack_size(64 * 1024 * 1024)
            .spawn(move || metatron_kernel::run(BufReader::new(File::open(path).unwrap())))
            .unwrap().join().unwrap();
        assert_eq!(actual, Verdict::Accept, "complete export remains unresolved: {name}");
    }
}

#[test]
#[ignore = "requires pinned frozen196 and qualified origin flags"]
fn admitted_nonrecursive_lift_supports_its_source_eta_equation() {
    let root=PathBuf::from(std::env::var("NUCLEUS_FROZEN196").expect("pinned corpus path"));
    let raw=std::fs::read_to_string(root.join("good/init-prelude.ndjson")).unwrap();
    let parsed=metatron_kernel::parser::parse(std::io::Cursor::new(&raw)).unwrap().resolve().unwrap();
    let name=parsed.names.iter_raw().find_map(|(id,n)|matches!(n,metatron_kernel::syntax::Name::Str{prefix,value} if value=="up_down" && matches!(parsed.names.get(*prefix),Some(metatron_kernel::syntax::Name::Str{value,..}) if value=="ULift")).then_some(id)).unwrap();
    let mut prefix=String::new();
    for line in raw.lines() {
        prefix.push_str(line);prefix.push('\n');
        let row:serde_json::Value=serde_json::from_str(line).unwrap();
        if row["thm"]["name"].as_u64()==Some(name) {break;}
    }
    assert_eq!(metatron_kernel::run(std::io::Cursor::new(&prefix)),Verdict::Accept);
    assert_eq!(metatron_kernel::run(std::io::Cursor::new(prefix.replace("\"str\":\"ULift\"","\"str\":\"RenamedLift\""))),Verdict::Accept);
}

#[test]
#[ignore = "requires pinned frozen196 and qualified origin flags"]
fn checked_product_iota_closes_source_no_confusion_prefix() {
    let root=PathBuf::from(std::env::var("NUCLEUS_FROZEN196").expect("pinned corpus path"));
    let raw=std::fs::read_to_string(root.join("good/init-prelude.ndjson")).unwrap();
    let parsed=metatron_kernel::parser::parse(std::io::Cursor::new(&raw)).unwrap().resolve().unwrap();
    let name=parsed.names.iter_raw().find_map(|(id,n)|matches!(n,metatron_kernel::syntax::Name::Str{prefix,value} if value=="noConfusion" && matches!(parsed.names.get(*prefix),Some(metatron_kernel::syntax::Name::Str{value,..}) if value=="PProd")).then_some(id)).unwrap();
    let mut prefix=String::new();
    for line in raw.lines() {
        prefix.push_str(line);prefix.push('\n');
        let row:serde_json::Value=serde_json::from_str(line).unwrap();
        if row["def"]["name"].as_u64()==Some(name) {break;}
    }
    assert_eq!(metatron_kernel::run(std::io::Cursor::new(prefix)),Verdict::Accept);
}

#[test]
#[ignore = "requires pinned frozen196 and qualified origin flags"]
fn checked_nonrecursive_indexed_prop_closes_int_nonneg_prefix() {
    let root=PathBuf::from(std::env::var("NUCLEUS_FROZEN196").expect("pinned corpus path"));
    let raw=std::fs::read_to_string(root.join("good/perf/grind-ring-5.ndjson")).unwrap();
    let parsed=metatron_kernel::parser::parse(std::io::Cursor::new(&raw)).unwrap().resolve().unwrap();
    let name=parsed.names.iter_raw().find_map(|(id,n)|matches!(n,metatron_kernel::syntax::Name::Str{prefix,value} if value=="NonNeg" && matches!(parsed.names.get(*prefix),Some(metatron_kernel::syntax::Name::Str{value,..}) if value=="Int")).then_some(id)).unwrap();
    let mut prefix=String::new();
    for line in raw.lines() {
        prefix.push_str(line);prefix.push('\n');
        let row:serde_json::Value=serde_json::from_str(line).unwrap();
        if row["inductive"]["types"][0]["name"].as_u64()==Some(name) {break;}
    }
    assert_eq!(metatron_kernel::run(std::io::Cursor::new(prefix)),Verdict::Accept);
}

#[test]
#[ignore = "requires pinned frozen196 and qualified origin flags"]
fn checked_transport_projection_closes_syntax_no_confusion_prefix() {
    let root=PathBuf::from(std::env::var("NUCLEUS_FROZEN196").expect("pinned corpus path"));
    let raw=std::fs::read_to_string(root.join("good/init-prelude.ndjson")).unwrap();
    let parsed=metatron_kernel::parser::parse(std::io::Cursor::new(&raw)).unwrap().resolve().unwrap();
    let name=parsed.names.iter_raw().find_map(|(id,n)|matches!(n,metatron_kernel::syntax::Name::Str{prefix,value} if value=="noConfusion" && matches!(parsed.names.get(*prefix),Some(metatron_kernel::syntax::Name::Str{value,..}) if value=="Syntax")).then_some(id)).unwrap();
    let mut prefix=String::new();
    for line in raw.lines() {
        prefix.push_str(line);prefix.push('\n');
        let row:serde_json::Value=serde_json::from_str(line).unwrap();
        if row["def"]["name"].as_u64()==Some(name) {break;}
    }
    assert_eq!(metatron_kernel::run(std::io::Cursor::new(prefix)),Verdict::Accept);
}

#[test]
#[ignore = "requires pinned frozen196 and qualified origin flags"]
fn checked_source_replay_closes_parser_no_confusion_prefix() {
    let root=PathBuf::from(std::env::var("NUCLEUS_FROZEN196").expect("pinned corpus path"));
    let raw=std::fs::read_to_string(root.join("good/init-prelude.ndjson")).unwrap();
    let parsed=metatron_kernel::parser::parse(std::io::Cursor::new(&raw)).unwrap().resolve().unwrap();
    let name=parsed.names.iter_raw().find_map(|(id,n)|matches!(n,metatron_kernel::syntax::Name::Str{prefix,value} if value=="noConfusion" && matches!(parsed.names.get(*prefix),Some(metatron_kernel::syntax::Name::Str{value,..}) if value=="ParserDescr")).then_some(id)).unwrap();
    let mut prefix=String::new();
    for line in raw.lines() {
        prefix.push_str(line);prefix.push('\n');
        let row:serde_json::Value=serde_json::from_str(line).unwrap();
        if row["def"]["name"].as_u64()==Some(name) {break;}
    }
    assert_eq!(metatron_kernel::run(std::io::Cursor::new(prefix)),Verdict::Accept);
}

#[test]
#[ignore = "requires pinned frozen196 and qualified origin flags"]
fn checked_ofnat_iota_closes_no_confusion_prefix() {
    let root=PathBuf::from(std::env::var("NUCLEUS_FROZEN196").expect("pinned corpus path"));
    let raw=std::fs::read_to_string(root.join("good/init-prelude.ndjson")).unwrap();
    let parsed=metatron_kernel::parser::parse(std::io::Cursor::new(&raw)).unwrap().resolve().unwrap();
    let name=parsed.names.iter_raw().find_map(|(id,n)|matches!(n,metatron_kernel::syntax::Name::Str{prefix,value} if value=="noConfusion" && matches!(parsed.names.get(*prefix),Some(metatron_kernel::syntax::Name::Str{value,..}) if value=="OfNat")).then_some(id)).unwrap();
    let mut prefix=String::new();
    for line in raw.lines() {
        prefix.push_str(line);prefix.push('\n');
        let row:serde_json::Value=serde_json::from_str(line).unwrap();
        if row["def"]["name"].as_u64()==Some(name) {break;}
    }
    assert_eq!(metatron_kernel::run(std::io::Cursor::new(prefix)),Verdict::Accept);
}
