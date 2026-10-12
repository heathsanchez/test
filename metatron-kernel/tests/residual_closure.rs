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
