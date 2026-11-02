use std::io::BufReader;
use std::fs::File;
use std::path::PathBuf;
use metatron_kernel::verdict::Verdict;

#[test]
fn original_magma_pair_n7_discharges_its_checked_decide_equality() {
    let root=PathBuf::from(std::env::var("NUCLEUS_FROZEN196").expect("immutable original corpus required"));
    let path=root.join("good/perf/magma-list-pair-n7.ndjson");
    let result=std::thread::Builder::new().stack_size(64*1024*1024)
        .spawn(move || metatron_kernel::run(BufReader::new(File::open(path).unwrap())))
        .unwrap().join().unwrap();
    assert_eq!(result,Verdict::Accept,"source-checked Decidable.rec computation remains unresolved");
}
